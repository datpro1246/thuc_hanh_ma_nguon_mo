from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

# Đường dẫn geckodriver
gecko_path = r"/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập về nhà /geckodriver"

# Khởi tạo service
ser = Service(gecko_path)

# Tùy chọn Firefox
options = webdriver.firefox.options.Options()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
options.headless = False

# Khởi tạo driver
driver = webdriver.Firefox(options=options, service=ser)

# Link danh sách tất cả sản phẩm
url = "https://gochek.vn/collections/all"

driver.get(url)
time.sleep(2)

# Cuộn trang thật sâu để load toàn bộ sản phẩm
body = driver.find_element(By.TAG_NAME, "body")
for _ in range(300):
    body.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.02)

time.sleep(2)

# ------ TRÍCH XUẤT SẢN PHẨM ------
stt, ten, gia, giam, hinhanh, linksp = [], [], [], [], [], []

# Tất cả sản phẩm theo đúng HTML
products = driver.find_elements(By.CSS_SELECTOR, ".content-product-list .pro-loop")

print("Tổng số sản phẩm tìm được:", len(products))

for i, sp in enumerate(products, 1):

    # Tên sản phẩm
    try:
        tsp = sp.find_element(By.CSS_SELECTOR, "h3.pro-name a").text
    except:
        tsp = ""

    # Link
    try:
        lsp = sp.find_element(By.CSS_SELECTOR, "h3.pro-name a").get_attribute("href")
    except:
        lsp = ""

    # Giá hiện tại
    try:
        gsp = sp.find_element(By.CSS_SELECTOR, "p.pro-price span:not(.pro-price-del)").text
    except:
        gsp = ""
        
    # % giảm giá
    try:
        sale = sp.find_element(By.CSS_SELECTOR, ".product-sale span").text
    except:
        sale = ""

    # Ảnh sản phẩm
    try:
        ha = sp.find_element(By.CSS_SELECTOR, ".product-img picture source").get_attribute("srcset")
    except:
        ha = ""

    # Chỉ thêm nếu có tên
    if tsp.strip():
        stt.append(len(stt) + 1)
        ten.append(tsp)
        gia.append(gsp)
        giam.append(sale)
        hinhanh.append(ha)
        linksp.append(lsp)

# Lưu kết quả
df = pd.DataFrame({
    "STT": stt,
    "Tên sản phẩm": ten,
    "Giá bán": gia,
    "Giảm giá": giam,
    "Ảnh sản phẩm": hinhanh,
    "Link SP": linksp
})

df.to_excel("danh_sach_gochek.xlsx", index=False)

driver.quit()

print("Xong!")
