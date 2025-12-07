from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import random

# geckodriver
gecko_path = "/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/geckodriver"
ser = Service(gecko_path)

# Firefox options
options = webdriver.firefox.options.Options()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
options.headless = False

# Khởi tạo driver
driver = webdriver.Firefox(options=options, service=ser)
driver.maximize_window()

url = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang"
driver.get(url)
time.sleep(2)

# Tìm body
body = driver.find_element(By.TAG_NAME, "body")

# CLICK NÚT "Xem thêm sản phẩm"
for k in range(20):
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "custom-estore-spinner"))
        )
    except:
        pass

    time.sleep(1)
    buttons = driver.find_elements(By.TAG_NAME, "button")
    clicked = False

    for btn in buttons:
        text = btn.text.strip().lower()
        if "xem thêm" in text and "sản phẩm" in text:
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            try:
                btn.click()
                clicked = True
                time.sleep(2)
            except:
                pass
            break

    if not clicked:
        break

# CUỘN XUỐNG HẾT TRANG
for _ in range(80):
    body.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.01)

time.sleep(1)

# LIST CHỨA DỮ LIỆU
ma_id = []
ten = []
gia = []
don_vi = []
gia_goc = []
product_url = []

# Tìm các nút "Chọn mua"
buttons = driver.find_elements(By.XPATH, "//button[text()='Chọn mua']")
print("Tổng sản phẩm tìm thấy:", len(buttons))

for i, bt in enumerate(buttons, 1):
    sp = bt
    for _ in range(3):
        sp = sp.find_element(By.XPATH, "./..")

    ma = "000" + str(random.randint(0, 99999)).zfill(5)

    try:
        tsp = sp.find_element(By.TAG_NAME, "h3").text.strip()
    except:
        tsp = ""

    try:
        price_block = sp.find_element(By.CLASS_NAME, "text-blue-5")
        gsp = price_block.find_element(By.CLASS_NAME, "font-semibold").text.strip()
        dv_raw = price_block.find_element(By.CLASS_NAME, "text-label2").text.strip()
        dv = dv_raw.replace("/", "").strip()
    except:
        gsp = ""
        dv = ""

    try:
        ggc = sp.find_element(By.CLASS_NAME, "line-through").text.strip()
    except:
        ggc = gsp

    try:
        link = sp.find_element(By.TAG_NAME, "a").get_attribute("href")
    except:
        link = ""

    if tsp != "":
        ma_id.append(ma)
        ten.append(tsp)
        gia.append(gsp)
        don_vi.append(dv)
        gia_goc.append(ggc)
        product_url.append(link)

# Tạo DataFrame
df = pd.DataFrame({
    "Mã ID": ma_id,
    "Tên sản phẩm": ten,
    "Giá": gia,
    "Đơn vị tính": don_vi,
    "Giá gốc": gia_goc,
    "Link URL": product_url
})

driver.quit()
# ------------------------------
# LƯU VÀO SQLITE
# ------------------------------

import sqlite3

conn = sqlite3.connect("longchau_db.sqlite")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_url TEXT PRIMARY KEY,
    product_id TEXT,
    product_name TEXT,
    price TEXT,
    unit TEXT,
    original_price TEXT
)
""")
conn.commit()

for ma, tsp, gsp, dv, ggc, link in zip(ma_id, ten, gia, don_vi, gia_goc, product_url):
    cursor.execute("""
        INSERT OR IGNORE INTO products(product_url, product_id, product_name, price, unit, original_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (link, ma, tsp, gsp, dv, ggc))
conn.commit()

print("ĐÃ LƯU TOÀN BỘ DỮ LIỆU VÀO SQLite (longchau_db.sqlite)")

# ---------------------------
# HÀM IN BẢNG ĐẸP
# ---------------------------

def print_table(cursor, query):
    cursor.execute(query)
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]

    df = pd.DataFrame(rows, columns=col_names)

    if df.empty:
        print("(Không có dữ liệu)\n")
    else:
        print(df.to_string(index=False), "\n")

# -------------------------------------------
# PHẦN 2: 15 CÂU QUERY PHÂN TÍCH DỮ LIỆU
# -------------------------------------------

print("\n=====================")
print("BẮT ĐẦU CHẠY 15 QUERY")
print("=====================\n")

# 1
print("1. Trùng lặp product_url:")
print_table(cursor, """
SELECT product_url, COUNT(*) AS so_lan
FROM products
GROUP BY product_url
HAVING COUNT(*) > 1
""")

# 2
print("2. Sản phẩm không có giá:")
print_table(cursor, """
SELECT COUNT(*) AS so_sp_khong_gia
FROM products
WHERE price IS NULL OR price='' OR price='0'
""")

# 3
print("3. Giá bán cao hơn giá gốc:")
print_table(cursor, """
SELECT product_name, price, original_price
FROM products
WHERE CAST(REPLACE(REPLACE(price,'.',''),'₫','') AS INTEGER)
    > CAST(REPLACE(REPLACE(original_price,'.',''),'₫','') AS INTEGER)
""")

# 4
print("4. Các đơn vị tính duy nhất:")
print_table(cursor, "SELECT DISTINCT unit FROM products")

# 5
print("5. Tổng số bản ghi:")
print_table(cursor, "SELECT COUNT(*) AS tong_so_san_pham FROM products")

# 6
print("6. Top 10 sản phẩm giảm giá nhiều nhất:")
print_table(cursor, """
SELECT product_name, price, original_price,
CAST(REPLACE(original_price,'.','') AS INTEGER) -
CAST(REPLACE(price,'.','') AS INTEGER) AS discount
FROM products
ORDER BY discount DESC
LIMIT 10
""")

# 7
print("7. Sản phẩm đắt nhất:")
print_table(cursor, """
SELECT product_name, price
FROM products
ORDER BY CAST(REPLACE(price,'.','') AS INTEGER) DESC
LIMIT 1
""")

# 8
print("8. Đếm sản phẩm theo đơn vị tính:")
print_table(cursor, """
SELECT unit, COUNT(*) AS so_luong
FROM products
GROUP BY unit
""")

# 9
print("9. Sản phẩm chứa từ khóa 'Vitamin C':")
print_table(cursor, """
SELECT *
FROM products
WHERE product_name LIKE '%Vitamin C%'
""")

# 10
print("10. Sản phẩm giá từ 100k đến 200k:")
print_table(cursor, """
SELECT product_name, price
FROM products
WHERE CAST(REPLACE(price,'.','') AS INTEGER)
BETWEEN 100000 AND 200000
""")

# 11
print("11. Sắp xếp theo giá tăng dần (hiển thị 15 dòng đầu):")
cursor.execute("""
SELECT product_name, price
FROM products
ORDER BY CAST(REPLACE(price,'.','') AS INTEGER) ASC
""")
rows = cursor.fetchall()
df = pd.DataFrame(rows, columns=["product_name", "price"])
print(df.head(15).to_string(index=False), "\n")

# 12
print("12. Top 5 phần trăm giảm giá:")
print_table(cursor, """
SELECT product_name, price, original_price,
    (CAST(REPLACE(original_price,'.','') AS FLOAT)
    - CAST(REPLACE(price,'.','') AS FLOAT))
    / CAST(REPLACE(original_price,'.','') AS FLOAT) * 100 AS discount_percent
FROM products
WHERE original_price!='' AND original_price!='0'
ORDER BY discount_percent DESC
LIMIT 5
""")

# 13
print("13. Xóa trùng lặp (giữ bản ghi đầu tiên):")
cursor.execute("""
DELETE FROM products
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM products
    GROUP BY product_url
)
""")
conn.commit()
print("→ Đã xóa xong.\n")

# 14
print("14. Đếm sản phẩm theo nhóm giá:")
print_table(cursor, """
SELECT 
    CASE 
        WHEN CAST(REPLACE(price,'.','') AS INTEGER) < 50000 THEN 'Dưới 50k'
        WHEN CAST(REPLACE(price,'.','') AS INTEGER) BETWEEN 50000 AND 100000 THEN '50k - 100k'
        ELSE 'Trên 100k'
    END AS price_group,
COUNT(*) AS so_sp
FROM products
GROUP BY price_group
""")

# 15
print("15. URL NULL hoặc rỗng:")
print_table(cursor, """
SELECT product_name
FROM products
WHERE product_url IS NULL OR product_url=''
""")

# KÊT THÚC
conn.close()
print("HOÀN THÀNH! ĐÃ CHẠY TOÀN BỘ QUERY.")
