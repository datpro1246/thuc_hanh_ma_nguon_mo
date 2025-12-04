from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# Đường dẫn ChromeDriver
driver_path = "/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver"
service = Service(driver_path)

# Khởi tạo Webdriver
driver = webdriver.Chrome(service=service)

# Mở Trang
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)
time.sleep(2)

# Lấy tất cả thẻ <a> với title chứa "List of painters"
tags = driver.find_elements(By.XPATH, "//a[contains(@title, 'List of painters')]")

# tạo danh sách các liên kết
links = [tag.get_attribute("href") for tag in tags]

# xuất thông tin
for link in links:
    print(link)

# Đóng webdriver
driver.quit()
