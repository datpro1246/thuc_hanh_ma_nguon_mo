from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import getpass

# Đường dẫn đến file thực thi geckodriver
gecko_path = r"/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập về nhà /geckodriver"
ser = Service(gecko_path)

# Tạo tùy chọn Firefox
options = webdriver.firefox.options.Options()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
options.headless = False  # True nếu muốn chạy ngầm

# Lấy username + password từ người dùng
username_input = input("Nhập tài khoản: ")
password_input = getpass.getpass("Nhập mật khẩu (sẽ được ẩn): ")

# Khởi tạo driver
driver = webdriver.Firefox(options=options, service=ser)

# Truy cập trang đăng nhập
url = 'https://daotao.hutech.edu.vn/default.aspx?page=dangnhap'
driver.get(url)

try:
    # Chờ tối đa 20 giây để username hiện ra
    username = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ctl00_txtTaiKhoa"))
    )
    username.send_keys(username_input)

    # Chờ password hiện ra
    password = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ctl00_txtMatKhau"))
    )
    password.send_keys(password_input)

    # Chờ nút đăng nhập
    login_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_ctl00_btnDangNhap"))
    )
    login_btn.click()

    # Chờ vài giây để đăng nhập xong
    time.sleep(10)

finally:
    driver.quit()
