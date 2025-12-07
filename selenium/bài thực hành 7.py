from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import pandas as pd
import re
import time

# ================================
# 1. LINK DANH SÁCH TRƯỜNG
# ================================
MAIN_URL = "https://vi.wikipedia.org/wiki/" + quote(
    "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam", safe=""
)

BAD_KEYWORDS = ["cao đẳng", "học viện", "sĩ quan", "cảnh sát", "quân sự", "nhạc viện"]

FOREIGN_KEYWORDS = [
    "malaysia","singapore","philippines","indonesia","thailand",
    "china","japan","korea","taiwan","australia",
    "putra","universiti","universitas","university of","international"
]

VALID_PREFIXES = ["đại học", "trường đại học"]


# ================================
# 2. HÀM XỬ LÝ TEXT
# ================================
def clean_text(t):
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
    m = re.search(r"\(([^)]+)\)\s*$", name)
    return m.group(1).strip() if m else ""


# ================================
# 3. KHỞI TẠO SELENIUM
# ================================
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

print("Đang tải trang…")
driver.get(MAIN_URL)
time.sleep(2)

# Scroll full trang để load đủ dữ liệu
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)


# ================================
# LƯU DANH SÁCH TRƯỜNG
# ================================
found = {}

def add_record(name, url=""):
    name = clean_text(name)
    if not name: return

    if not starts_valid_prefix(name): return
    if match_bad(name): return
    if match_foreign(name) or match_foreign(url): return

    key = name.lower()

    if key not in found:
        found[key] = {
            "Name": name,
            "ShortName": short_name(name),
            "Rector": "",
            "Website": "",
            "URL": url
        }
    else:
        if url and not found[key]["URL"]:
            found[key]["URL"] = url


# ================================
# 4. QUÉT BẢNG WIKITABLE
# ================================
print("Đang quét bảng…")

tables = driver.find_elements(By.CSS_SELECTOR, "table.wikitable")

for table in tables:
    rows = table.find_elements(By.TAG_NAME, "tr")[1:]
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if not cols:
            continue

        name = clean_text(cols[0].text)
        a = cols[0].find_elements(By.TAG_NAME, "a")
        url = a[0].get_attribute("href") if a else ""

        add_record(name, url)


# ================================
# 5. QUÉT CÁC <ul> GIỐNG 100% BEAUTIFULSOUP
# ================================
print("Đang quét danh sách ul…")

uls = driver.find_elements(By.XPATH, "//ul")

for ul in uls:
    # Selenium tương đương recursive=False của BeautifulSoup
    lis = ul.find_elements(By.XPATH, "./li")

    for li in lis:
        text = clean_text(li.text)
        name = clean_text(text.split("-")[0])

        a = li.find_elements(By.TAG_NAME, "a")
        url = a[0].get_attribute("href") if a else ""

        add_record(name, url)


# ================================
# 6. CRAWL INFOBOX TỪNG TRANG
# ================================
def crawl_infobox(url):
    info = {"Rector": "", "Website": ""}

    try:
        driver.get(url)
        time.sleep(1)

        rows = driver.find_elements(By.CSS_SELECTOR, "table.infobox tr")

        for tr in rows:
            ths = tr.find_elements(By.TAG_NAME, "th")
            tds = tr.find_elements(By.TAG_NAME, "td")

            if not ths or not tds:
                continue

            key = ths[0].text.lower()
            val = clean_text(tds[0].text)

            if "hiệu trưởng" in key or "rector" in key:
                info["Rector"] = val
            elif "website" in key:
                a = tds[0].find_elements(By.TAG_NAME, "a")
                info["Website"] = a[0].get_attribute("href") if a else val

        return info

    except:
        return info


# ================================
# 7. CRAWL TỪNG TRƯỜNG
# ================================
keys = list(found.keys())

for i, key in enumerate(keys, start=1):
    rec = found[key]
    url = rec["URL"]

    if url:
        print(f"({i}/{len(keys)}) Lấy infobox: {url}")
        info = crawl_infobox(url)
        rec["Rector"] = info["Rector"]
        rec["Website"] = info["Website"]
        time.sleep(1)
    else:
        print(f"({i}/{len(keys)}) Không có URL: {rec['Name']}")

driver.quit()


# ================================
# 8. XUẤT EXCEL
# ================================
df = pd.DataFrame(found.values()).drop_duplicates(subset=["Name"])
df = df[["Name", "ShortName", "Rector", "Website"]]
df = df.sort_values("Name").reset_index(drop=True)
df.to_excel("Vietnam_Universities.xlsx", index=False)

print("\nXONG! Tổng số trường:", len(df))
print("Đã lưu file: Vietnam_Universities.xlsx")
