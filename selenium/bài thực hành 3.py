from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

# ĐƯỜNG DẪN CHO CHROMEDRIVER 
chrome_driver_path = "/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver"
service = Service(chrome_driver_path)

# Khởi tạo WebDriver Chrome
driver = webdriver.Chrome(service=service)

# Mở trang Wikipedia
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22X%22"
driver.get(url)

# Đợi 2 giây để trang tải xong
time.sleep(2)

# Lấy tất cả thẻ <ul>
ul_tags = driver.find_elements(By.TAG_NAME, "ul")
print("Số lượng <ul> trên trang:", len(ul_tags))

# Chọn thẻ <ul> thứ 21 (index = 20)
ul_painters = ul_tags[20]

# Lấy tất cả thẻ <li> bên trong <ul> này
li_tags = ul_painters.find_elements(By.TAG_NAME, "li")  # dùng find_elements để lấy tất cả

# Tạo danh sách các URL và tiêu đề
links = [tag.find_element(By.TAG_NAME, "a").get_attribute("href") for tag in li_tags]
titles = [tag.find_element(By.TAG_NAME, "a").get_attribute("title") for tag in li_tags]

# In ra URL
for link in links:
    print(link)

# Đóng WebDriver
driver.quit()
