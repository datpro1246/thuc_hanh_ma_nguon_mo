# 1. IMPORT
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import sqlite3
import pandas as pd
import time
import random
import os


# 1. FIREFOX + GECKODRIVER 
GECKO = "/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/geckodriver"

opt = webdriver.firefox.options.Options()
opt.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
opt.headless = False

# LONG CHÂU HTTPS FIX
opt.set_preference("security.enterprise_roots.enabled", True)
opt.set_preference("webdriver_accept_untrusted_certs", True)
opt.set_preference("acceptInsecureCerts", True)
opt.set_preference("dom.security.https_only_mode", False)

driver = webdriver.Firefox(service=Service(GECKO), options=opt)
driver.maximize_window()


# 2. VÀO TRANG LONG CHÂU
url = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang"
driver.get(url)
time.sleep(2)

body = driver.find_element(By.TAG_NAME, "body")

# 3. TỰ ĐỘNG TÌM & NHẤN NÚT “Xem thêm sản phẩm”
def click_xem_them():
    try:
        # chờ spinner tắt
        WebDriverWait(driver, 8).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".custom-estore-spinner"))
        )
    except:
        pass

    btns = driver.find_elements(By.CSS_SELECTOR, "button")
    for b in btns:
        txt = b.text.strip().lower()
        if "xem thêm" in txt and "phẩm" in txt:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
            time.sleep(0.4)
            try:
                b.click()
                return True
            except:
                return False
    return False


# Bấm tối đa 20 lần
for _ in range(20):
    ok = click_xem_them()
    time.sleep(1.2)
    if not ok:
        break


# 4. CUỘN TRANG EXTRA LOAD
for _ in range(50):
    body.send_keys(Keys.PAGE_DOWN)
    time.sleep(0.02)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(1)


# 5. CHUẨN BỊ MẢNG LƯU DỮ LIỆU
ids, names, prices, units, originals, links = [], [], [], [], [], []


# 6. TÌM TẤT CẢ BUTTON “Chọn mua” 
buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Chọn mua')]")
print("Số sản phẩm tìm thấy:", len(buttons))


# 7. LẶP QUA TỪNG SẢN PHẨM
for btn in buttons:
    # Lấy block cha 3 tầng
    block = btn.find_element(By.XPATH, "./ancestor::div[3]")

    pid = "SP" + str(random.randint(11111, 99999))

    # Tên sản phẩm
    try:
        name = block.find_element(By.CSS_SELECTOR, "h3").text.strip()
    except:
        name = ""

    # Giá / Đơn vị
    try:
        pbox = block.find_element(By.CSS_SELECTOR, ".text-blue-5")
        price = pbox.find_element(By.CSS_SELECTOR, ".font-semibold").text.strip()
        unit = pbox.find_element(By.CSS_SELECTOR, ".text-label2").text.strip().replace("/", "")
    except:
        price, unit = "", ""

    # Giá gốc
    try:
        original = block.find_element(By.CSS_SELECTOR, ".line-through").text.strip()
    except:
        original = price

    # URL sản phẩm
    try:
        link = block.find_element(By.TAG_NAME, "a").get_attribute("href")
    except:
        link = ""

    if name:
        ids.append(pid)
        names.append(name)
        prices.append(price)
        units.append(unit)
        originals.append(original)
        links.append(link)

driver.quit()


# 8. TẠO DB - XÓA DB CŨ
dbname = "longchau_db.sqlite"

if os.path.exists(dbname):
    os.remove(dbname)

conn = sqlite3.connect(dbname)
cur = conn.cursor()

cur.execute("""
CREATE TABLE products (
    product_url TEXT PRIMARY KEY,
    product_id TEXT,
    product_name TEXT,
    price TEXT,
    unit TEXT,
    original_price TEXT
)
""")
conn.commit()

# Insert dữ liệu
for a,b,c,d,e,f in zip(ids, names, prices, units, originals, links):
    cur.execute("""
        INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?)
    """, (f,a,b,c,d,e))
conn.commit()

print(">>> Đã lưu xong dữ liệu vào longchau_db.sqlite")


# 9. PRINT TABLE HỖ TRỢ
def show(sql):
    cur.execute(sql)
    data = cur.fetchall()
    cols = [x[0] for x in cur.description]
    print(pd.DataFrame(data, columns=cols).to_string(index=False), "\n")


# 10. 15 CÂU SQL - truy vấn
queries = [

    ("1. Các URL trùng nhau:",
     """SELECT COUNT(*) AS so_url_trung
        FROM (
            SELECT product_url
            FROM products
            GROUP BY product_url
            HAVING COUNT(*) > 1
) AS tmp;
"""),

    ("2. Sản phẩm không có giá :",
     """SELECT COUNT(*) AS missing_price
        FROM products
        WHERE IFNULL(price,'') = '';"""),

    ("3. Giá bán > giá gốc:",
     """SELECT product_name, price, original_price
        FROM products
        WHERE CAST(REPLACE(price,'.','') AS INTEGER)
            > CAST(REPLACE(original_price,'.','') AS INTEGER);"""),

    ("4. Các đơn vị tính:",
     "SELECT DISTINCT unit FROM products;"),

    ("5. Tổng số mặt hàng:",
     "SELECT COUNT(product_id) AS tong FROM products;"),

    ("6. Top 10 giảm giá mạnh:",
     """
     SELECT product_name, price, original_price,
     CAST(REPLACE(original_price,'.','') AS INT)
     - CAST(REPLACE(price,'.','') AS INT) AS giam_tien
     FROM products
     ORDER BY giam_tien DESC
     LIMIT 10;
     """),

    ("7. Món đắt nhất:",
     """
     SELECT product_name, price
     FROM products
     ORDER BY CAST(REPLACE(price,'.','') AS INT) DESC
     LIMIT 1;
     """),

    ("8. Thống kê theo đơn vị tính:",
     """SELECT unit, COUNT(*) AS sl FROM products GROUP BY unit;"""),

    ("9. Sản phẩm chứa chữ Vitamin C:",
     """SELECT * FROM products
        WHERE product_name LIKE '%Vitamin C%';"""),

    ("10. Giá từ 100k–200k:",
     """
     SELECT product_name, price
     FROM products
     WHERE CAST(REPLACE(price,'.','') AS INT)
           BETWEEN 100000 AND 200000;
     """),

    ("11. 15 sản phẩm giá thấp nhất:",
     """
     SELECT product_name, price
     FROM products
     ORDER BY CAST(REPLACE(price,'.','') AS INT) ASC
     LIMIT 15;
     """),

    ("12. Top % giảm giá:",
     """
     SELECT product_name, price, original_price,
       ROUND(
         (CAST(REPLACE(original_price,'.','') AS FLOAT) -
          CAST(REPLACE(price,'.','') AS FLOAT))
          / CAST(REPLACE(original_price,'.','') AS FLOAT) * 100, 2
       ) AS percent
     FROM products
     WHERE original_price <> ''
     ORDER BY percent DESC
     LIMIT 5;
     """),

    ("13. Xóa URL trùng (chỉ giữ 1 cái):",
     """
     DELETE FROM products
     WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM products
        GROUP BY product_url
     );
     """),

    ("14. Phân nhóm giá sản phẩm:",
     """
     SELECT 
       CASE
         WHEN CAST(REPLACE(price,'.','') AS INT) < 50000 THEN 'Dưới 50k'
         WHEN CAST(REPLACE(price,'.','') AS INT) <= 100000 THEN '50k - 100k'
         ELSE 'Trên 100k'
       END AS nhom,
       COUNT(*) AS sl
     FROM products
     GROUP BY nhom;
     """),

    ("15. Sản phẩm thiếu URL:",
     """SELECT COUNT(*) AS so_san_pham_thieu_url
        FROM products
        WHERE product_url IS NULL OR product_url = '';
""")

]


print("\n==================== SQL RESULT ====================\n")
for desc, sql in queries:
    print(desc)
    if sql.strip().upper().startswith("DELETE"):
        cur.execute(sql)
        conn.commit()
        print("Đã chạy DELETE.\n")
    else:
        show(sql)

conn.close()
print("\n>>> HOÀN TẤT TOÀN BỘ SCRIPT <<<")
