import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from urllib.parse import quote

# 1. Link Wikipedia chứa danh sách trường
MAIN_URL = "https://vi.wikipedia.org/wiki/" + quote(
    "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam", safe=""
)

# Giả làm trình duyệt để tránh bị chặn
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Những từ khóa để loại bỏ vì không phải đại học
BAD_KEYWORDS = ["cao đẳng", "học viện", "sĩ quan", "cảnh sát", "quân sự", "nhạc viện"]

# Từ khóa để loại bỏ trường nước ngoài
FOREIGN_KEYWORDS = [
    "malaysia","singapore","philippines","indonesia","thailand",
    "china","japan","korea","taiwan","australia",
    "putra","universiti","universitas","university of","international"
]

# Chỉ lấy các tên đúng chuẩn đại học
VALID_PREFIXES = ["đại học", "trường đại học"]


# 2. Các hàm xử lý dữ liệu
def clean_text(t):
    """ Làm sạch text cho nó gọn gàng, bỏ ký tự lạ """
    if not t: return ""
    t = re.sub(r"\[\d+\]", "", t)
    t = t.replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()

def starts_valid_prefix(name):
    """ Kiểm tra tên trường có bắt đầu bằng 'Đại học...' không """
    t = name.lower().strip()
    return any(t.startswith(p) for p in VALID_PREFIXES)

def match_bad(text):
    """ Kiểm tra xem có phải Cao đẳng / Học viện... """
    t = text.lower()
    return any(k in t for k in BAD_KEYWORDS)

def match_foreign(text):
    """ Kiểm tra có phải trường nước ngoài """
    t = text.lower()
    return any(k in t for k in FOREIGN_KEYWORDS)

def short_name(name):
    """ Lấy phần viết tắt trong ngoặc (nếu có) """
    m = re.search(r"\(([^)]+)\)\s*$", name)
    return m.group(1).strip() if m else ""

# 3. Tải trang chính
print("Đang tải danh sách trường đại học…")
resp = requests.get(MAIN_URL, headers=HEADERS)
soup = BeautifulSoup(resp.text, "html.parser")

# Lưu danh sách trường (dạng dictionary để tránh trùng)
found = {}

def add_record(name, url=""):
    """ 
    Hàm kiểm tra tên trường và quyết định có thêm vào danh sách hay không
    """
    name = clean_text(name)
    if not name:
        return

    if not starts_valid_prefix(name):
        return

    if match_bad(name):
        return

    if match_foreign(name) or match_foreign(url):
        return

    key = name.lower()

    # Nếu trường chưa có thì thêm
    if key not in found:
        found[key] = {
            "Name": name,
            "ShortName": short_name(name),
            "Rector": "",
            "Website": "",
            "URL": url  # để vào từng trang lấy info
        }
    else:
        # Nếu có URL mới tốt hơn
        if url and not found[key]["URL"]:
            found[key]["URL"] = url


# 4. Lấy trường trong bảng
print("Đang quét bảng trong Wikipedia…")

for table in soup.find_all("table", class_="wikitable"):
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if not cols:
            continue

        name = clean_text(cols[0].get_text())
        a = cols[0].find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_record(name, url)


# 5. Lấy trường trong danh sách <ul>
print("Đang quét danh sách gạch đầu dòng…")

for ul in soup.find_all("ul"):
    for li in ul.find_all("li", recursive=False):
        text = clean_text(li.get_text())
        name = clean_text(text.split("-")[0])
        a = li.find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_record(name, url)


# 6. Cào INFOBOX từng trường
def crawl_infobox(url):
    """ 
    Chỉ lấy Rector (hiệu trưởng) và Website 
    """
    info = {"Rector": "", "Website": ""}

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        sp = BeautifulSoup(r.text, "html.parser")

        box = sp.find("table", class_="infobox")
        if not box:
            return info

        for tr in box.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if not th or not td:
                continue

            key = th.text.lower()
            val = clean_text(td.get_text(" "))

            # Lấy hiệu trưởng
            if "hiệu trưởng" in key or "rector" in key:
                info["Rector"] = val

            # Lấy website
            elif "website" in key:
                a = td.find("a", href=True)
                info["Website"] = a["href"] if a else val

        return info

    except:
        return info


# BẮT ĐẦU CRAWL TỪNG TRANG
keys = list(found.keys())

for i, key in enumerate(keys, start=1):
    rec = found[key]
    url = rec["URL"]

    if url:
        print(f"({i}/{len(keys)}) Đang lấy thông tin từ {url}")
        info = crawl_infobox(url)

        rec["Rector"] = info["Rector"]
        rec["Website"] = info["Website"]

        time.sleep(1)   # nghỉ 1 giây để không bị chặn (theo yêu cầu của bạn)

    else:
        print(f"({i}/{len(keys)}) Không có URL: {rec['Name']}")


# 7. Xuất Excel (CHỈ 4 CỘT)
df = pd.DataFrame(found.values()).drop_duplicates(subset=["Name"])
df = df[["Name", "ShortName", "Rector", "Website"]]
df = df.sort_values("Name").reset_index(drop=True)

df.to_excel("Vietnam_Universities.xlsx", index=False)

print("\nXONG! Tổng số trường đại học thu được:", len(df))
print("Đã lưu file: Vietnam_Universities.xlsx")
