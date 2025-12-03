from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# 1. Cấu hình ChromeDriver
chrome_path = "/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập về nhà /chromedriver"
service = Service(chrome_path)

# Khởi tạo trình duyệt Chrome với ChromeDriver
driver = webdriver.Chrome(service=service)

# Mở cửa sổ trình duyệt tối đa
driver.maximize_window()

# 2. Mở trang Quora và đăng nhập
driver.get("https://fr.quora.com/login")

# Chờ trường email xuất hiện rồi điền email
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.NAME, "email"))
).send_keys("binhpro1246@gmail.com")

# Chờ trường password xuất hiện rồi điền mật khẩu
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.NAME, "password"))
).send_keys("Thai123@gl")

# Chờ nút "Se connecter" clickable rồi click để đăng nhập
login_btn = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(),'Se connecter')]]"))
)
login_btn.click()

# Chờ trang load
time.sleep(10)

# 3. Scroll để load bài viết
SCROLL_PAUSE = 3     # thời gian tạm dừng sau mỗi lần scroll
MAX_SCROLL = 50     # số lần scroll tối đa
last_height = driver.execute_script("return document.body.scrollHeight")
scroll_count = 0

# Scroll xuống cuối trang nhiều lần để load nhiều bài viết
while scroll_count < MAX_SCROLL:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")        # scroll tới cuối trang
    time.sleep(SCROLL_PAUSE)                                                        # đợi trang load
    new_height = driver.execute_script("return document.body.scrollHeight")         # lấy chiều cao trang mới
    if new_height == last_height:                                                   # nếu không còn bài mới load nữa, dừng
        break
    last_height = new_height
    scroll_count += 1

# 4. Lấy dữ liệu bài viết
# Tìm tất cả bài viết trên trang sau khi scroll xong
posts = driver.find_elements(By.XPATH, "//div[contains(@class,'puppeteer_test_tribe_post_item_feed_story')]")
data = []            # danh sách lưu dữ liệu bài viết
authors_set = set()  # để tránh tác giả trùng

# danh sách lưu dữ liệu bài viết
for post in posts:  
    # Lấy tên tác giả
    try:
        author_elem = post.find_element(By.XPATH, ".//a[contains(@class,'puppeteer_test_link') and contains(@href,'profile')]")
        author = author_elem.text.strip()
    except:
        author = ""
        
    # Bỏ qua nếu tác giả trùng hoặc không có tên
    if author in authors_set or author == "":
        continue  # bỏ trùng tác giả hoặc tác giả trống
        
    # Lấy ngày đăng và link bài viết
    try:
        date_elem = post.find_element(By.XPATH, ".//a[contains(@class,'post_timestamp')]")
        posting_date = date_elem.text.strip()
        post_link = date_elem.get_attribute("href")
    except:
        posting_date = post_link = ""
        
    # Lấy link hình ảnh trong bài (nếu có)
    try:
        img_elem = post.find_element(By.XPATH, ".//img")
        img_link = img_elem.get_attribute("src")
    except:
        img_link = ""

    # Chờ 5 giây cho bài viết này load thêm nội dung (nếu có)
    time.sleep(5)
    
    # Lưu dữ liệu vào danh sách
    data.append({
        "Author": author,
        "Posting Date": posting_date,
        "Post Link": post_link,
        "Image Link": img_link
    })
    
    # Đánh dấu tác giả đã lấy để tránh lặp
    authors_set.add(author)

    # dừng khi đủ 10 bài viết
    if len(data) >= 10:  
        break

# 5. Xuất ra Excel
df = pd.DataFrame(data)
df.to_excel("quora_10_posts.xlsx", index=False)
print(f"Đã lưu {len(data)} bài viết ra quora_10_posts.xlsx")

# 6. Đóng trình duyệt
driver.quit()
