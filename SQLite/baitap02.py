import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re
import os

###########################################################
# I. KHỞI TẠO DB + CẤU HÌNH
###########################################################

DB_FILE = "Painters_Data.db"
TABLE_NAME = "painters_info"

# Xoá DB cũ nếu tồn tại
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Đã xoá DB cũ: {DB_FILE}")

# Tạo DB + bảng
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
    name TEXT PRIMARY KEY,
    birth TEXT,
    death TEXT,
    nationality TEXT
);
""")
conn.commit()

# Từ khóa lọc khi suy luận nationality
descriptors = [
    'portrait', 'landscape', 'historical', 'miniaturist',
    'sculptor', 'painter', 'artist', 'multi-media'
]

# Chrome Options
CHROME_DRIVER_PATH = "/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver"
service = Service(CHROME_DRIVER_PATH)

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")


###########################################################
# II. Hàm xử lý ngày tháng
###########################################################

def extract_date(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.strip()

    match1 = re.search(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b', text)
    match2 = re.search(r'\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b', text)
    match3 = re.search(r'\b\d{4}\b', text)

    if match1: return match1.group(0)
    if match2: return match2.group(0)
    if match3: return match3.group(0)
    return ""

def safe_quit(driver):
    try:
        if driver:
            driver.quit()
    except:
        pass


###########################################################
# III. LẤY TẤT CẢ LINK A → Z (15 link mỗi chữ cái)
###########################################################

all_links = []

print("\n--- Lấy link A→Z ---")
for i in range(65, 90):  # A–Z
    driver = None
    collected = 0
    try:
        driver = webdriver.Chrome(service=service, options=options)
        url = f"https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22{chr(i)}%22"
        driver.get(url)
        time.sleep(2)

        divs = driver.find_elements(By.CLASS_NAME, "div-col")

        for div in divs:
            li_tags = div.find_elements(By.TAG_NAME, "li")

            for li in li_tags:
                if collected >= 15:
                    break

                try:
                    a = li.find_element(By.TAG_NAME, "a")
                    href = a.get_attribute("href")
                    if href and "/wiki/" in href:
                        all_links.append(href)
                        collected += 1
                except:
                    pass

            if collected >= 15:
                break

        print(f"{chr(i)} → Lấy {collected} link")

    except Exception as e:
        print(f"Lỗi chữ {chr(i)}:", e)
    finally:
        safe_quit(driver)

print(f"Tổng link: {len(all_links)}")


###########################################################
# IV. CRAWL DỮ LIỆU TỪNG HỌA SĨ → LƯU SQLITE
###########################################################

print("\n--- Crawl dữ liệu ---")
count = 0

for link in all_links:
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(link)
        time.sleep(2)

        name = birth = death = nationality = ""

        # ===== 1. Lấy tên =====
        try:
            name = driver.find_element(By.TAG_NAME, "h1").text
        except:
            name = ""

        # ===== 2. Ưu tiên Infobox =====
        try:
            # Born
            birth_element = driver.find_element(
                By.XPATH, "//th[text()='Born' or text()='Birth Date']/following-sibling::td"
            )
            birth_text = birth_element.text.strip().split("\n")
            birth = extract_date("\n".join(birth_text))

            # Died
            try:
                death_element = driver.find_element(
                    By.XPATH, "//th[text()='Died' or text()='Death Date']/following-sibling::td"
                )
                death_text = death_element.text.strip().split("\n")
                death = extract_date("\n".join(death_text))
            except:
                pass

            # Nationality
            try:
                nat = driver.find_element(
                    By.XPATH, "//th[text()='Nationality']/following-sibling::td"
                ).text.strip()
                nationality = nat
            except:
                if birth_text:
                    tmp = re.sub(r'\d', '', birth_text[-1]).strip()
                    nationality = tmp.split(",")[-1].strip()

        # ===== 3. Fallback paragraphs =====
        except:
            try:
                paragraphs = driver.find_elements(By.XPATH, "//div[@id='mw-content-text']//p")
                text = " ".join([p.text for p in paragraphs[:5]])
                text = re.sub(r'\[.*?\]', '', text)

                # born … – died …
                born_died = re.search(r'born\s+([^-\n,]+).*?-\s*died\s+([^,)\n]+.*?)',
                                      text, flags=re.IGNORECASE)
                if born_died:
                    birth = extract_date(born_died.group(1).strip())
                    death = extract_date(born_died.group(2).strip())

                # (1820–1900)
                matches = re.findall(r'\(([^)]*?\d{3,4}[^)]*?)\)', text)
                if matches:
                    rng = matches[0].split("–")
                    birth = extract_date(rng[0])
                    if len(rng) > 1:
                        death = extract_date(rng[1])

                # nationality bằng pattern “was a French painter”
                nat_match = re.search(
                    r'(?:was|is) an? (.*?) (?:painter|artist)',
                    text, flags=re.IGNORECASE
                )
                if nat_match:
                    words = [
                        w for w in nat_match.group(1).split()
                        if w.lower() not in descriptors
                    ]
                    if words:
                        nationality = words[-1]

                # born in France
                if not nationality:
                    born_match = re.search(r'[Bb]orn\s.*?in\s([A-Za-z\s]+)', text)
                    if born_match:
                        nationality = born_match.group(1).strip()

            except:
                pass

        safe_quit(driver)

        # ===== LƯU VÀO DATABASE =====
        cursor.execute(f"""
            INSERT OR IGNORE INTO {TABLE_NAME} (name, birth, death, nationality)
            VALUES (?, ?, ?, ?)
        """, (name, birth, death, nationality))
        conn.commit()

        count += 1
        print(f"{count}. {name} | {birth} | {death} | {nationality}")

    except Exception as e:
        print("Lỗi:", e)
        safe_quit(driver)


# V. TRUY VẤN KIỂM TRA
###########################################################

def run_sql(query, desc=None):
    if desc:
        print(f"\n{desc}")
    print(query)
    cursor.execute(query)
    rows = cursor.fetchall()
    for r in rows:
        print(" →", r)

# 1. Tổng số họa sĩ
run_sql(
    f"SELECT COUNT(*)\n"
    f"FROM {TABLE_NAME};",
    "1️⃣ Tổng số họa sĩ"
)


# 2. 5 dòng đầu tiên
run_sql(
    f"SELECT *\n"
    f"FROM {TABLE_NAME}\n"
    f"LIMIT 5;",
    "2️⃣ 5 dòng đầu tiên"
)

# 3. Các quốc tịch duy nhất
run_sql(
    f"SELECT DISTINCT nationality\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE nationality <> '';",
    "3️⃣ Quốc tịch duy nhất"
)

# 4. Họa sĩ có tên bắt đầu bằng F
run_sql(
    f"SELECT name\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE name LIKE 'F%';",
    "4️⃣ Họa sĩ tên bắt đầu F"
)

# 5. Nationality có chứa chữ “French”
run_sql(
    f"SELECT name, nationality\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE nationality LIKE '%French%';",
    "5️⃣ Nationality chứa French"
)

# 6. Họa sĩ không có nationality
run_sql(
    f"SELECT name\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE nationality = '' OR nationality IS NULL;",
    "6️⃣ Không có nationality"
)

# 7. Có đầy đủ birth và death
run_sql(
    f"SELECT name\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE birth <> '' AND death <> '';",
    "7️⃣ Đầy đủ birth + death"
)

# 8. Tên chứa “Fales”
run_sql(
    f"SELECT *\n"
    f"FROM {TABLE_NAME}\n"
    f"WHERE name LIKE '%Fales%';",
    "8️⃣ Tên chứa Fales"
)

# 9. Sắp xếp theo alphabet
run_sql(
    f"SELECT name\n"
    f"FROM {TABLE_NAME}\n"
    f"ORDER BY name ASC;",
    "9️⃣ Sort A→Z"
)

# 10. Group theo nationality + đếm số lượng
run_sql(
    f"SELECT nationality, COUNT(*)\n"
    f"FROM {TABLE_NAME}\n"
    f"GROUP BY nationality\n"
    f"ORDER BY COUNT(*) DESC;",
    "🔟 Đếm theo nationality"
)

conn.close()
print("\n====> ĐÃ HOÀN THÀNH & ĐÓNG DATABASE")
