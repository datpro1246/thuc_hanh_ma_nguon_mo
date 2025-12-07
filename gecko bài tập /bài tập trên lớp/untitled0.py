from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import sqlite3
import random

# ============================
# KHỞI TẠO SELENIUM
# ============================

gecko_path = r"/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/geckodriver"
ser = Service(gecko_path)

options = webdriver.firefox.options.Options()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
options.headless = False

driver = webdriver.Firefox(options=options, service=ser)
driver.maximize_window()

url = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang"
driver.get(url)
time.sleep(2)

body = driver.find_element(By.TAG_NAME, "body")

# ============================
# CLICK "Xem thêm sản phẩm"
# ============================

for k in range(18):
    try:
        WebDriverWait(driver, 8).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "custom-estore-spinner"))
        )
    except:
        pass

    buttons = driver.find_elements(By.TAG_NAME, "button")
    clicked = False

    for btn in buttons:
        tx = btn.text.strip().lower()
        if "xem thêm" in tx and "sản phẩm" in tx:
            driver.execute_script("arguments[0].scrollIntoView();", btn)
            time.sleep(0.3)
            try:
                btn.click()
                clicked = True
                time.sleep(1.5)
            except:
                pass
            break

    if not clicked:
        break

# ============================
# CUỘN XUỐNG CUỐI TRANG
# ============================

for _ in range(60):
    body.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.01)

time.sleep(1)

# ============================
# TẠO BIẾN LƯU DỮ LIỆU
# ============================

ma_id = []
ten_sp = []
gia_sp = []
don_vi = []
gia_goc = []
link_url = []

# ============================
# LẤY DANH SÁCH SẢN PHẨM
# ============================

buttons = driver.find_elements(By.XPATH, "//button[text()='Chọn mua']")
print("Tổng sản phẩm tìm được:", len(buttons))

for i, bt in enumerate(buttons, 1):
    parent = bt
    for _ in range(3):
        parent = parent.find_element(By.XPATH, "./..")

    # Mã id random
    mid = "SP" + str(random.randint(10000, 99999))

    # Tên sản phẩm
    try:
        name = parent.find_element(By.TAG_NAME, "h3").text.strip()
    except:
        name = ""

    # Giá
    try:
        price_block = parent.find_element(By.CLASS_NAME, "text-blue-5")
        price = price_block.find_element(By.CLASS_NAME, "font-semibold").text.strip()
        dv_raw = price_block.find_element(By.CLASS_NAME, "text-label2").text.strip()
        unit = dv_raw.replace("/", "").strip()
    except:
        price = ""
        unit = ""

    # Giá gốc
    try:
        goc = parent.find_element(By.CLASS_NAME, "line-through").text.strip()
    except:
        goc = price

    # Link chi tiết
    try:
        url_sp = parent.find_element(By.TAG_NAME, "a").get_attribute("href")
    except:
        url_sp = ""

    if name != "":
        ma_id.append(mid)
        ten_sp.append(name)
        gia_sp.append(price)
        don_vi.append(unit)
        gia_goc.append(goc)
        link_url.append(url_sp)

driver.quit()

# ===================================================================
# LƯU XUỐNG SQLITE GIỐNG THẦY (nhưng dựa trên code của bạn)
# ===================================================================

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

for a, b, c, d, e, f in zip(ma_id, ten_sp, gia_sp, don_vi, gia_goc, link_url):
    cursor.execute("""
        INSERT OR IGNORE INTO products(product_url, product_id, product_name, price, unit, original_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (f, a, b, c, d, e))

conn.commit()
print("\n✔ Đã lưu hết dữ liệu vào SQLite (longchau_db.sqlite)\n")

# ===================================================================
# HÀM IN BẢNG
# ===================================================================

def print_table(cursor, query):
    cursor.execute(query)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    df = pd.DataFrame(rows, columns=cols)
    if df.empty:
        print("(Không có dữ liệu)\n")
    else:
        print(df.to_string(index=False), "\n")

# ===================================================================
# 15 QUERY GIỐNG THẦY
# ===================================================================

print("\n======================")
print(" CHẠY 15 QUERY PHÂN TÍCH ")
print("======================\n")

# 1
print("1. Trùng lặp URL:")
print_table(cursor, """
SELECT product_url, COUNT(*)
FROM products
GROUP BY product_url
HAVING COUNT(*)>1
""")

# 2
print("2. SP không có giá:")
print_table(cursor, """
SELECT COUNT(*) FROM products
WHERE price IS NULL OR price='' OR price='0'
""")

# 3
print("3. Giá > giá gốc:")
print_table(cursor, """
SELECT product_name, price, original_price
FROM products
WHERE CAST(REPLACE(REPLACE(price,'.',''),'₫','') AS INT)
> CAST(REPLACE(REPLACE(original_price,'.',''),'₫','') AS INT)
""")

# 4
print("4. Đơn vị tính unique:")
print_table(cursor, """SELECT DISTINCT unit FROM products""")

# 5
print("5. Tổng số SP:")
print_table(cursor, """SELECT COUNT(*) AS tong FROM products""")

# 6
print("6. Top 10 giảm giá nhiều nhất:")
print_table(cursor, """
SELECT product_name, price, original_price,
CAST(REPLACE(original_price,'.','') AS INT) -
CAST(REPLACE(price,'.','') AS INT) AS giam
FROM products
ORDER BY giam DESC
LIMIT 10
""")

# 7
print("7. SP đắt nhất:")
print_table(cursor, """
SELECT product_name, price
FROM products
ORDER BY CAST(REPLACE(price,'.','') AS INT) DESC
LIMIT 1
""")

# 8
print("8. Đếm theo đơn vị:")
print_table(cursor, """
SELECT unit, COUNT(*) FROM products GROUP BY unit
""")

# 9
print("9. Sản phẩm chứa 'Vitamin C':")
print_table(cursor, """SELECT * FROM products WHERE product_name LIKE '%Vitamin C%'""")

# 10
print("10. SP giá 100k - 200k:")
print_table(cursor, """
SELECT product_name, price
FROM products
WHERE CAST(REPLACE(price,'.','') AS INT)
BETWEEN 100000 AND 200000
""")

# 11
print("11. Sắp giá tăng dần:")
cursor.execute("""
SELECT product_name, price
FROM products
ORDER BY CAST(REPLACE(price,'.','') AS INT)
""")
print(pd.DataFrame(cursor.fetchall(), columns=["product_name", "price"]).head(15))

# 12
print("\n12. Top % giảm giá:")
print_table(cursor, """
SELECT product_name, price, original_price,
(CAST(REPLACE(original_price,'.','') AS FLOAT)
 - CAST(REPLACE(price,'.','') AS FLOAT))
 / CAST(REPLACE(original_price,'.','') AS FLOAT) * 100 AS percent_off
FROM products
WHERE original_price!=''
ORDER BY percent_off DESC
LIMIT 5
""")

# 13
print("\n13. Xóa trùng lặp:")
cursor.execute("""
DELETE FROM products
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM products
    GROUP BY product_url
)
""")
conn.commit()
print("→ Đã xóa.\n")

# 14
print("14. Nhóm giá:")
print_table(cursor, """
SELECT 
CASE 
    WHEN CAST(REPLACE(price,'.','') AS INT) < 50000 THEN 'Dưới 50k'
    WHEN CAST(REPLACE(price,'.','') AS INT) BETWEEN 50000 AND 100000 THEN '50k - 100k'
    ELSE 'Trên 100k'
END AS price_group,
COUNT(*) 
FROM products
GROUP BY price_group
""")

# 15
print("15. URL rỗng:")
print_table(cursor, """SELECT product_name FROM products WHERE product_url IS NULL OR product_url=''""")

conn.close()
print("\n🎉 HOÀN THÀNH TẤT CẢ !")
