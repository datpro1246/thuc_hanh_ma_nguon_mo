import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from urllib.parse import quote

# 1) CẤU HÌNH
MAIN_URL = "https://vi.wikipedia.org/wiki/" + quote(
    "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam", safe=""
)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Từ khóa để bỏ (không phải Đại học)
BAD_KEYWORDS = [
    "cao đẳng", "học viện", "sĩ quan",
    "cảnh sát", "quân sự", "nhạc viện"
]

# Từ khóa trường nước ngoài
FOREIGN_KEYWORDS = [
    "malaysia","singapore","philippines","indonesia","thailand",
    "china","japan","korea","taiwan","australia",
    "putra","universiti","universitas","university of","international"
]

# Chỉ nhận các tên bắt đầu bằng 2 tiền tố này
VALID_PREFIXES = ["đại học", "trường đại học"]


# 2) HÀM TIỆN ÍCH
def clean_text(t):
    """Xóa [1], [2], xuống dòng, khoảng trắng thừa…"""
    if not t: return ""
    t = re.sub(r"\[\d+\]", "", t)
    t = t.replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()

def starts_valid_prefix(name):
    t = name.lower().strip()
    return any(t.startswith(p) for p in VALID_PREFIXES)

def match_bad(text):
    t = text.lower()
    return any(k in t for k in BAD_KEYWORDS)

def match_foreign(text):
    t = text.lower()
    return any(k in t for k in FOREIGN_KEYWORDS)

def short_name(name):
    """Lấy tên viết tắt trong ngoặc cuối"""
    m = re.search(r"\(([^)]+)\)\s*$", name)
    return m.group(1).strip() if m else ""


# 3) TẢI TRANG CHÍNH
print("Tải trang:", MAIN_URL)
resp = requests.get(MAIN_URL, headers=HEADERS)
soup = BeautifulSoup(resp.text, "html.parser")

found = {}  # key = name.lower(), value = record dict


def add_record(name, url="", source="page"):
    """Thêm trường vào danh sách sau khi lọc"""
    name = clean_text(name)
    if not name:
        return

    # lọc theo prefix
    if not starts_valid_prefix(name):
        return

    # bỏ cao đẳng, học viện, sĩ quan
    if match_bad(name):
        return

    # bỏ từ khóa nước ngoài
    if match_foreign(name) or match_foreign(url):
        return

    key = name.lower()

    if key not in found:
        found[key] = {
            "Name": name,
            "ShortName": short_name(name),
            "URL": url,
            "Type": "",
            "Established": "",
            "Rector": "",
            "Website": "",
            "Location": "",
            "Source": source
        }
    else:
        # nếu đã có nhưng chưa có URL -> cập nhật
        if url and not found[key]["URL"]:
            found[key]["URL"] = url


# 4) LẤY TÊN TỪ BẢNG WIKITABLE
print("Đang quét bảng...")
for table in soup.find_all("table", class_="wikitable"):
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if not cols:
            continue

        name = clean_text(cols[0].get_text())
        a = cols[0].find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_record(name, url, "table")


# 5) LẤY TÊN TỪ DANH SÁCH <ul>
print("Đang quét danh sách...")
for ul in soup.find_all("ul"):
    for li in ul.find_all("li", recursive=False):
        text = clean_text(li.get_text())
        name = clean_text(text.split("-")[0])  # lấy phần trước dấu '-'

        a = li.find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_record(name, url, "ul")


# 6) CÀO INFOBOX TỪ URL TỪNG TRANG
def crawl_infobox(url):
    """Trả về thông tin từ infobox"""
    info = {"Type": "", "Established": "", "Rector": "", "Website": "", "Location": ""}
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        sp = BeautifulSoup(r.text, "html.parser")
        box = sp.find("table", class_="infobox")
        if not box:
            return info

        for tr in box.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if not th or not td: continue
            key = th.text.lower()
            val = clean_text(td.get_text(" "))

            if "loại" in key or "type" in key:
                info["Type"] = val
            elif "lập" in key or "established" in key:
                info["Established"] = val
            elif "hiệu trưởng" in key or "rector" in key:
                info["Rector"] = val
            elif "website" in key:
                a = td.find("a", href=True)
                info["Website"] = a["href"] if a else val
            elif "địa" in key or "location" in key:
                info["Location"] = val

        return info
    except:
        return info


# Bắt đầu cào từng trường
keys = list(found.keys())

for i, key in enumerate(keys, start=1):
    rec = found[key]
    url = rec["URL"]

    if url:
        print(f"Cào {i}/{len(keys)}: {url}")
        info = crawl_infobox(url)

        # loại trường nước ngoài sau khi đọc location
        mix = (rec["Name"] + " " + info["Location"]).lower()
        if match_foreign(mix):
            print(" -> Bỏ (nước ngoài):", rec["Name"])
            del found[key]
            continue

        for k in info:
            if info[k]:
                rec[k] = info[k]

        time.sleep(0.1)

    else:
        print(f"Cào (no-url) {i}/{len(keys)}: {rec['Name']}")


# 7) XUẤT EXCEL (bỏ Source)
df = pd.DataFrame(found.values()).drop_duplicates(subset=["Name"])

# loại bỏ cột Source nếu có
if "Source" in df.columns:
    df = df.drop(columns=["Source"])

df = df.sort_values("Name").reset_index(drop=True)
df.to_excel("Vietnam_Universities.xlsx", index=False)

print("\nHoàn thành! Tổng số trường đại học Việt Nam thu được:", len(df))
print("Đã lưu file: Vietnam_Universities.xlsx")

