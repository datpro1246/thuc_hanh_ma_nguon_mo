from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re

#######################################################
# I. Tạo DataFrame rỗng
d = pd.DataFrame({'name': [], 'birth': [], 'death': [], 'nationality': []})

# Đường dẫn chromedriver
service = Service("/Users/binh/Downloads/chromedriver-mac-arm64 bài tập lớp/chromedriver")

#############################################################
# II. Lấy tất cả đường dẫn của họa sĩ
all_links = []

# Chọn chữ cái (ví dụ 'A')
for i in range(65, 66):  # 65 là 'A' theo ASCII
    driver = webdriver.Chrome(service=service)
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22" + chr(i) + "%22"
    try:
        driver.get(url)
        time.sleep(3)

        # Lấy các div chứa danh sách họa sĩ
        divs = driver.find_elements(By.CLASS_NAME, "div-col")
        for div in divs:
            li_tags = div.find_elements(By.TAG_NAME, "li")
            for li in li_tags:
                try:
                    a_tag = li.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")
                    if href and "/wiki/" in href:
                        all_links.append(href)
                except:
                    continue

        print(f"Số link thu thập được: {len(all_links)}")

    except Exception as e:
        print("Error!", e)

    driver.quit()

############################################################
# III. Lấy thông tin từng họa sĩ
driver = webdriver.Chrome(service=service)
count = 0

for link in all_links:
    count += 1
    print(f"{count}: {link}")

    try:
        driver.get(link)
        time.sleep(2)

        # Tên họa sĩ
        try:
            name = driver.find_element(By.TAG_NAME, "h1").text
        except:
            name = ""

        # Ngày sinh
        try:
            birth_element = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
            birth_raw = birth_element.text
            birth_match = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', birth_raw)
            birth = birth_match[0] if birth_match else ""
        except:
            birth = ""

        # Ngày mất
        try:
            death_element = driver.find_element(By.XPATH, "//th[text()='Died']/following-sibling::td")
            death_raw = death_element.text
            death_match = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', death_raw)
            death = death_match[0] if death_match else ""
        except:
            death = ""

        # Quốc tịch
        try:
            nationality_element = driver.find_element(By.XPATH, "//th[text()='Nationality']/following-sibling::td")
            nationality = nationality_element.text
        except:
            nationality = ""

        # Thêm vào DataFrame
        painter = {'name': name, 'birth': birth, 'death': death, 'nationality': nationality}
        d = pd.concat([d, pd.DataFrame([painter])], ignore_index=True)

    except Exception as e:
        print("Error getting info:", e)
        continue

driver.quit()

#################################
# IV. In thông tin và xuất Excel
print(d)
file_name = 'Painters.xlsx'
d.to_excel(file_name, index=False)
print('Dataframe is written to Excel File successfully.')
