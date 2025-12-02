# full_robust_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from urllib.parse import quote

# -----------------------------
# Cấu hình
# -----------------------------
# dùng URL đã percent-encode để tránh lỗi requests với ký tự Unicode
MAIN_URL = "https://vi.wikipedia.org/wiki/" + quote(
    "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam", safe=""
)

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0"}

# từ khóa loại trừ
BAD_KEYWORDS = [
    "cao đẳng", "cao_đẳng", "học viện", "học_viện",
    "sĩ quan", "sĩ_quan", "cảnh sát", "nhạc viện", "quân sự"
]

# từ khóa nước ngoài (kiểm tra cả tên + href)
FOREIGN_KEYWORDS = [
    "malaysia", "singapore", "indonesia", "philippines", "thailand",
    "china", "japan", "korea", "taiwan", "australia", "putra",
    "universiti", "university of", "universitas", "international", "campus"
]

# tiền tố hợp lệ cho tên trường VN (không phân biệt hoa thường)
VALID_PREFIXES = ["đại học", "trường đại học"]

# -----------------------------
# Hàm tiện ích
# -----------------------------
def normalize_text(s):
    if not s:
        return ""
    s = re.sub(r'\[\d+\]', '', s)  # bỏ chỉ số [1], [2]
    s = s.replace('\xa0', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def looks_foreign(text):
    t = (text or "").lower()
    return any(k in t for k in FOREIGN_KEYWORDS)

def has_bad_keyword(text):
    t = (text or "").lower()
    return any(k in t for k in BAD_KEYWORDS)

def starts_valid_prefix(text):
    t = (text or "").lower().strip()
    return any(t.startswith(p) for p in VALID_PREFIXES)

def extract_short_name(name):
    # tìm tên viết tắt trong ngoặc đơn cuối
    m = re.search(r'\(([^)]+)\)\s*$', name)
    if m:
        return m.group(1).strip()
    return ""

# -----------------------------
# 1) Tải trang chính
# -----------------------------
print("Tải trang chính:", MAIN_URL)
resp = requests.get(MAIN_URL, headers=HEADERS, timeout=20)
print("HTTP status:", resp.status_code, "URL resolved:", resp.url)

if resp.status_code != 200:
    print("Lỗi khi tải trang chính. In 500 ký tự đầu để debug:")
    print(repr(resp.text[:500]))
    raise SystemExit("Không tải được trang chính. Kiểm tra URL hoặc kết nối.")

html = resp.text
# Debug: kiểm tra kiểu và vài ký tự đầu (giúp tránh MarkupResemblesLocatorWarning)
print("type(html):", type(html), "len:", len(html))
print("Preview:", repr(html[:200]))

soup = BeautifulSoup(html, "html.parser")

# -----------------------------
# 2) Quét tất cả bảng wikitable và các <ul>
# -----------------------------
found = {}  # key = normalized name, value = dict record

def add_record(name, url="", source="table"):
    name = normalize_text(name)
    if not name:
        return
    # filter by prefix
    if not starts_valid_prefix(name):
        return
    # exclude bad keywords
    if has_bad_keyword(name):
        return
    # exclude obvious foreign by name
    if looks_foreign(name):
        return
    key = name.lower()
    rec = found.get(key, {
        "Name": name,
        "ShortName": extract_short_name(name),
        "URL": "",
        "Type": "",
        "Established": "",
        "Rector": "",
        "Website": "",
        "Source": source
    })
    # prefer URL if provided
    if url and not rec["URL"]:
        rec["URL"] = url
    # update source to show where came from (table preferred)
    if rec["Source"] != "table" and source == "table":
        rec["Source"] = "table"
    found[key] = rec

# a) từ các bảng wikitable (dòng theo dòng)
tables = soup.find_all("table", class_=re.compile(r"wikitable"))
print("Số bảng wikitable tìm được:", len(tables))
for table in tables:
    rows = table.find_all("tr")
    for r in rows[1:]:
        cols = r.find_all(["td","th"])
        if not cols:
            continue
        # thường cột 0 chứa tên
        raw = cols[0].get_text(separator=" ").strip()
        raw = normalize_text(raw)
        # nếu có link trong cột 0 thì lấy URL
        a = cols[0].find("a", href=True)
        url = ""
        if a and a.get("href", "").startswith("/wiki/"):
            href = a.get("href")
            url = "https://vi.wikipedia.org" + href
            # filter foreign by href as well
            if looks_foreign(href):
                # nếu href chỉ ra nước ngoài -> skip
                continue
        add_record(raw, url=url, source="table")

# b) từ các danh sách <ul> ngoài bảng (bao gồm các li không có link)
uls = soup.find_all("ul")
print("Số ul tìm được:", len(uls))
for ul in uls:
    # chỉ lấy những li trực tiếp (không đệ quy sâu): tránh list trong list
    for li in ul.find_all("li", recursive=False):
        text = li.get_text(separator=" ").strip()
        text = normalize_text(text)
        # ignore very long noisy lines
        if len(text) > 300:
            continue
        # candidate là phần trước dấu '-' hoặc ',' (thường là tên)
        candidate = re.split(r'[-,–—]', text)[0].strip()
        if not candidate:
            continue
        a = li.find("a", href=True)
        url = ""
        if a and a.get("href", "").startswith("/wiki/"):
            href = a.get("href")
            url = "https://vi.wikipedia.org" + href
            if looks_foreign(href):
                continue
        add_record(candidate, url=url, source="ul")

# c) fallback: scan all <a> anchors on page and add any that look like university names
anchors = soup.find_all("a", href=True)
for a in anchors:
    text = a.get_text().strip()
    href = a.get("href")
    if not href.startswith("/wiki/"):
        continue
    if not text:
        continue
    if not ("đại học" in text.lower() or "trường đại học" in text.lower()):
        continue
    if has_bad_keyword(text):
        continue
    if looks_foreign(text) or looks_foreign(href):
        continue
    add_record(text, url="https://vi.wikipedia.org"+href, source="link")

# -----------------------------
# Sau khi thu thập tên - in số lượng
# -----------------------------
print("Số bản ghi (chưa kiểm tra url/infobox):", len(found))

# nếu 0 thì in debug và exit
if len(found) == 0:
    print("ERROR: Không tìm được bản ghi. In một vài thẻ <a> để debug:")
    for i, a in enumerate(soup.find_all("a")[:50], start=1):
        print(i, repr(a.get_text()[:80]), a.get("href"))
    raise SystemExit("Không tìm được bản ghi nào. Kiểm tra HTML nguồn.")

# -----------------------------
# 3) Với những record có URL -> cào infobox để xác định foreign/ bổ sung info
# Không bắt buộc; nếu không có infobox vẫn giữ record
# -----------------------------
def scrape_infobox(url):
    """Trả về dict chứa Type, Established, Rector, Website, Location (chuỗi)"""
    out = {"Type": "", "Established": "", "Rector": "", "Website": "", "Location": ""}
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.encoding = 'utf-8'
        sp = BeautifulSoup(r.text, "html.parser")
        infobox = sp.find("table", class_=re.compile(r"infobox"))
        if not infobox:
            return out
        for row in infobox.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            key = th.get_text().strip().lower()
            val = td.get_text(separator=" ").strip()
            if "loại" in key or "type" in key:
                out["Type"] = val
            elif any(k in key for k in ["thành lập", "established", "founded"]):
                out["Established"] = val
            elif any(k in key for k in ["hiệu trưởng", "rector", "president"]):
                out["Rector"] = val
            elif any(k in key for k in ["website", "trang web", "trang chủ"]):
                # ưu tiên href
                link = td.find("a", href=True)
                out["Website"] = link.get("href") if link and link.get("href") else val
            elif any(k in key for k in ["địa", "location", "thành phố", "tỉnh", "address"]):
                out["Location"] = val
        return out
    except Exception as e:
        # in debug ngắn nếu cần
        # print("Infobox error for", url, e)
        return out

# duyệt records có URL
keys = list(found.keys())
for idx, key in enumerate(keys, start=1):
    rec = found[key]
    url = rec.get("URL")
    # in trạng thái giống yêu cầu
    if url:
        print(f"Cào {idx}/{len(keys)}: {url}")
        info = scrape_infobox(url)
        # nếu infobox cho thấy location rõ ràng nước ngoài -> loại bỏ
        # (kiểm tra presence of foreign keywords in location or website)
        combined_check = (rec["Name"] + " " + info.get("Location","") + " " + info.get("Website","")).lower()
        if looks_foreign(combined_check):
            # xóa record
            print(" -> Bỏ (khả năng nước ngoài):", rec["Name"])
            del found[key]
            continue
        # gán các trường nếu có
        for k in ["Type","Established","Rector","Website","Location"]:
            if info.get(k):
                found[key][k] = info[k]
        # small delay
        time.sleep(0.15)
    else:
        # không có url — vẫn in tên (cào dạng tên)
        print(f"Cào (no-url) {idx}/{len(keys)}: {rec['Name']}")

# -----------------------------
# 4) Loại bỏ các record còn chứa từ khoá nước ngoài trong Name
# -----------------------------
to_remove = []
for k, rec in found.items():
    if looks_foreign(rec["Name"]):
        to_remove.append(k)
    if has_bad_keyword(rec["Name"]):
        to_remove.append(k)
for k in set(to_remove):
    print("Xóa do từ khóa không hợp lệ:", found[k]["Name"])
    found.pop(k, None)

# -----------------------------
# 5) Chuẩn hóa kết quả và xuất Excel
# -----------------------------
rows = []
for rec in found.values():
    rows.append({
        "Name": rec.get("Name",""),
        "ShortName": rec.get("ShortName",""),
        "URL": rec.get("URL",""),
        "Type": rec.get("Type",""),
        "Established": rec.get("Established",""),
        "Rector": rec.get("Rector",""),
        "Website": rec.get("Website",""),
        "Source": rec.get("Source","")
    })

df = pd.DataFrame(rows)
df = df.drop_duplicates(subset=["Name"])
df = df.sort_values("Name").reset_index(drop=True)

out_file = "Vietnam_Universities_robust.xlsx"
df.to_excel(out_file, index=False)
print(f"\nHoàn thành — ghi {len(df)} trường vào: {out_file}")
