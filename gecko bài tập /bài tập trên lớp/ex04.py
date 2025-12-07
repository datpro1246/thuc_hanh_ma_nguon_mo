from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
import time
import pandas as pd
import getpass

# Đường dẫn ChromeDriver của bạn
service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/chromedriver")

driver = webdriver.Chrome(service=service)

# Truy cập link login của bạn
url = 'https://www.reddit.com/login/?dest=https%3A%2F%2Fwww.reddit.com%2Fsettings%2F'
driver.get(url)
time.sleep(3)

# Nhap thong tin nguoi dung
my_email = input('Please provide your email: ')
my_password = getpass.getpass('Please provide your password: ')

actionChains = ActionChains(driver)
time.sleep(1)

# TAB qua đến ô username
for i in range(5):
    actionChains.key_down(Keys.TAB).perform()

actionChains.send_keys(my_email).perform()
actionChains.key_down(Keys.TAB).perform()

actionChains.send_keys(my_password + Keys.ENTER).perform()

time.sleep(5)

# Truy cap trang post bai (đổi thành user của bạn nếu bạn muốn)
url2 = 'https://www.reddit.com/user/binhpro1246/submit/?type=TEXT'
driver.get(url2)
time.sleep(2)

for i in range(17):
    actionChains.key_down(Keys.TAB).perform()

actionChains.send_keys('Vi du post').perform()

actionChains.key_down(Keys.TAB)
actionChains.key_down(Keys.TAB).perform()

actionChains.send_keys('Le Nhat Tung').perform()

for i in range(2):
    actionChains.key_down(Keys.TAB).perform()
    time.sleep(3)

actionChains.send_keys(Keys.ENTER).perform()

time.sleep(120)
driver.quit()
