from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re

#######################################################
# I. Tai noi chua links vaf Tao dataframe rong
all_links = []
d = pd.DataFrame({'name' : [], 'birth' : [],'death' : [], 'nationality' : []})

# Đường dẫn chromedriver
service = Service("/Users/binh/Downloads/chromedriver-mac-arm64 bài tập lớp/chromedriver")

#############################################################
# II. Lay ra tat ca duong dan de truy cap den painters
for i in range(70, 71):
    driver = webdriver.Chrome(service=service)
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22"+chr(i)+"%22"
    try:
        driver.get(url)
        time.sleep(3)

        ul_tags = driver.find_elements(By.TAG_NAME, "ul")
        print(len(ul_tags))

        ul_painters = ul_tags[20]
        li_tags = ul_painters.find_elements(By.TAG_NAME, "li")

        links = [tag.find_element(By.TAG_NAME, "a").get_attribute("href") for tag in li_tags]
        for x in links:
            all_links.append(x)

    except:
        print("Error!")

driver.quit()

############################################################
# III. Lay thong tin cua tung hoa si
count = 0
for link in all_links:
    if count > 3:
        break
    count += 1

    print(link)

    try:
        driver = webdriver.Chrome(service=service)
        url = link
        driver.get(url)
        time.sleep(2)

        # Lay ten hoa si
        try:
            name = driver.find_element(By.TAG_NAME, "h1").text
        except:
            name = ""

        # Lay ngay sinh
        try:
            birth_element = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
            birth_raw = birth_element.text
            birth = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', birth_raw)[0]
        except:
            birth = ""

        # Lay ngay mat
        try:
            death_element = driver.find_element(By.XPATH, "//th[text()='Died']/following-sibling::td")
            death_raw = death_element.text
            death = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', death_raw)[0]
        except:
            death = ""

        # Lay quoc tich
        try:
            nationality_element = driver.find_element(By.XPATH, "//th[text()='Nationality']/following-sibling::td")
            nationality = nationality_element.text
        except:
            nationality = ""

        # Tao dictionary thong tin cua hoa si
        painter = {'name': name, 'birth': birth, 'death': death, 'nationality': nationality}

        # CHuyen doi dictionary thanh DataFrame
        painter_df = pd.DataFrame([painter])

        # Them vao DF chinh
        d = pd.concat([d, painter_df], ignore_index=True)

        driver.quit()

    except:
        pass

#################################
# IV. In thong tin
print(d)

file_name = 'Painters.xlsx'
d.to_excel(file_name)
print('Dataframe is written to Excel File successfully.')
