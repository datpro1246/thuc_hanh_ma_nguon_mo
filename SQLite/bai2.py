import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re
import os

###############################################################
# I. CÀI ĐẶT & CHUẨN BỊ
###############################################################

DB_FILE = 'Painters_Data.db'
TABLE_NAME = 'painters_info'
all_links = []

# Xóa DB cũ cho sạch (tùy chọn)
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Đã xóa DB cũ: {DB_FILE}")

# Tạo kết nối SQLite
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    name TEXT PRIMARY KEY,
    birth TEXT,
    death TEXT,
    nationality TEXT
);
""")
conn.commit()

print(f"Đã tạo database '{DB_FILE}' và bảng '{TABLE_NAME}' sẵn sàng.\n")

# Chromedriver
service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver")

###############################################################
# II. EXTRACTION UTILS
###############################################################

def extract_date(text):
    """Trích xuất ngày từ text Wikipedia (rất nhiều dạng)."""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.strip()

    m1 = re.search(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b', text)
    m2 = re.search(r'\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b', text)
    m3 = re.search(r'\b\d{4}\b', text)

    if m1: return m1.group(0)
    if m2: return m2.group(0)
    if m3: return m3.group(0)
    return ""

descriptors = ['portrait', 'landscape', 'historical', 'miniaturist', 'sculptor', 'painter', 'artist', 'multi-media']

def safe_quit(driver):
    try:
        if driver:
            driver.quit()
    except:
        pass

###############################################################
# III. LẤY TẤT CẢ LINK HỌA SĨ CHỮ 'F'
###############################################################

print("=== BẮT ĐẦU LẤY DANH SÁCH LINK ===")
driver = webdriver.Chrome(service=service)
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22F%22"
driver.get(url)
time.sleep(3)

divs = driver.find_elements(By.CLASS_NAME, "div-col")

for div in divs:
    li_tags = div.find_elements(By.TAG_NAME, "li")
    for li in li_tags:
        try:
            a = li.find_element(By.TAG_NAME, "a")
            href = a.get_attribute("href")
            if "/wiki/" in href:
                all_links.append(href)
        except:
            pass

safe_quit(driver)
print(f"→ Tìm được {len(all_links)} links họa sĩ.\n")

###############################################################
# IV. CÀO TỪNG HỌA SĨ + LƯU SQLITE
###############################################################

print("=== BẮT ĐẦU CÀO DỮ LIỆU ===")
count = 0

for link in all_links:
    if count >= 5:    # Giới hạn test – muốn full thì xóa dòng này
        break
    count += 1

    print(f"\n[{count}] Đang xử lý: {link}")
    driver = webdriver.Chrome(service=service)
    driver.get(link)
    time.sleep(2)

    name = ""
    birth = ""
    death = ""
    nationality = ""

    # Lấy tên
    try:
        name = driver.find_element(By.TAG_NAME, "h1").text
    except:
        name = ""

    # Ưu tiên từ Infobox
    try:
        # Born
        birth_el = driver.find_element(By.XPATH, "//th[text()='Born' or text()='Birth Date']/following-sibling::td")
        birth_lines = birth_el.text.split("\n")
        birth = extract_date("\n".join(birth_lines))

        # Died
        try:
            death_el = driver.find_element(By.XPATH, "//th[text()='Died' or text()='Death Date']/following-sibling::td")
            death_lines = death_el.text.split("\n")
            death = extract_date("\n".join(death_lines))
        except:
            death = ""

        # Nationality
        try:
            nat_el = driver.find_element(By.XPATH, "//th[text()='Nationality']/following-sibling::td")
            nationality = nat_el.text.strip()
        except:
            nationality = ""

    except:
        # Fallback mô tả bài
        try:
            text = ""
            ps = driver.find_elements(By.XPATH, "//div[@id='mw-content-text']//p")
            for p in ps[:5]:
                text += p.text + " "

            text = re.sub(r'\[.*?\]', '', text)

            bd = re.search(r'born\s+([^-\n,]+).*?-\s*died\s+([^,)\n]+)', text, re.I)
            if bd:
                birth = extract_date(bd.group(1))
                death = extract_date(bd.group(2))

            nat = re.search(r'(?:was|is) an? (.*?) (?:painter|artist)', text)
            if nat:
                words = nat.group(1).split()
                words = [w for w in words if w.lower() not in descriptors]
                if words:
                    nationality = words[-1]

        except:
            pass

    safe_quit(driver)

    # Lưu SQLite (OR IGNORE để tránh trùng)
    cursor.execute(f"""
        INSERT OR IGNORE INTO {TABLE_NAME} (name, birth, death, nationality)
        VALUES (?, ?, ?, ?)
    """, (name, birth, death, nationality))
    conn.commit()

    print(f"→ Đã lưu: {name}")

print("\n=== CÀO DỮ LIỆU XONG ===\n")

###############################################################
# V. CHẠY 10 TRUY VẤN SQL THEO YÊU CẦU
###############################################################

print("\n==============================")
print("KẾT QUẢ TRUY VẤN SQL")
print("==============================\n")

# 1. Tổng số họa sĩ
print("1. Tổng số họa sĩ:")
print(cursor.execute("SELECT COUNT(*) FROM painters_info").fetchone()[0], "\n")

# 2. 5 dòng đầu tiên
print("2. 5 dòng đầu tiên:")
print(pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} LIMIT 5", conn), "\n")

# 3. Quốc tịch duy nhất
print("3. Danh sách quốc tịch:")
rows = cursor.execute(f"""
SELECT DISTINCT nationality 
FROM {TABLE_NAME}
WHERE nationality IS NOT NULL AND nationality <> ''
""").fetchall()
print(rows, "\n")

# 4. Tên bắt đầu bằng 'F'
print("4. Họa sĩ tên bắt đầu bằng F:")
print(cursor.execute(f"SELECT name FROM {TABLE_NAME} WHERE name LIKE 'F%'").fetchall(), "\n")

# 5. Nationality chứa French
print("5. Nationality chứa 'French':")
print(cursor.execute(f"""
SELECT name, nationality 
FROM {TABLE_NAME}
WHERE nationality LIKE '%French%'
""").fetchall(), "\n")

# 6. Không có nationality
print("6. Không có nationality:")
print(cursor.execute(f"""
SELECT name FROM {TABLE_NAME} 
WHERE nationality IS NULL OR nationality = ''
""").fetchall(), "\n")

# 7. Có cả birth và death
print("7. Có birth & death:")
print(cursor.execute(f"""
SELECT name FROM {TABLE_NAME}
WHERE birth <> '' AND death <> ''
""").fetchall(), "\n")

# 8. Tên chứa 'Fales'
print("8. Tên chứa 'Fales':")
print(cursor.execute(f"""
SELECT * FROM {TABLE_NAME}
WHERE name LIKE '%Fales%'
""").fetchall(), "\n")

# 9. Sắp xếp A-Z
print("9. Sắp xếp A-Z:")
print(cursor.execute(f"""
SELECT name FROM {TABLE_NAME}
ORDER BY name ASC
""").fetchall(), "\n")

# 10. Group theo nationality
print("10. Đếm theo nationality:")
print(cursor.execute(f"""
SELECT nationality, COUNT(*) 
FROM {TABLE_NAME}
WHERE nationality <> ''
GROUP BY nationality
ORDER BY COUNT(*) DESC
""").fetchall(), "\n")

###############################################################

conn.close()
print("\nĐã đóng kết nối SQLite.")
