from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import time

# Đường dẫn đến file thực thi geckodriver
gecko_path = r"/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/geckodriver"


# Khởi tạođối tượng dịch vụ với đường geckodriver
ser = Service(gecko_path)

# Tạo tuỳ chọn
options = webdriver.firefox.options.Options()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"

# Thiết lập firefox chỉ hiện thị giao giện
options.headless = False

# Khoi tao driver
driver = webdriver.Firefox(options = options, service=ser)

# Tao url
url = 'http://pythonscraping.com/pages/javascript/ajaxDemo.html'

# truy cap
driver.get(url)

# in ra noi dung cua trang web
print("Before: ===========================\n")
print(driver.page_source)

# tam dung khoang 3 giay
time.sleep(3)

# in lai
print("\n\n\n\nAfter: ======================\n")
print(driver.page_source)

# dong browser
driver.quit()
