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
service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver")

#######################################################
# Hàm helper trích ngày từ text
def extract_date(text):
    text = re.sub(r'\[.*?\]', '', text)  # loại bỏ [1], [a]
    text = re.sub(r'\(.*?\)', '', text)  # loại bỏ (aged …)
    text = text.strip()
    match1 = re.search(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b', text)
    match2 = re.search(r'\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b', text)
    match3 = re.search(r'\b\d{4}\b', text)
    if match1:
        return match1.group(0)
    elif match2:
        return match2.group(0)
    elif match3:
        return match3.group(0)
    return ""

#######################################################
# Từ mô tả bỏ khi lấy nationality
descriptors = ['portrait', 'landscape', 'historical', 'miniaturist', 'sculptor', 'painter', 'artist', 'multi-media']

#############################################################
# II. Lấy tất cả đường dẫn họa sĩ chữ A
all_links = []
for i in range(65, 66):  # chỉ chữ A
    driver = webdriver.Chrome(service=service)
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22" + chr(i) + "%22"
    try:
        driver.get(url)
        time.sleep(3)

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

        birth = ""
        death = ""
        nationality = ""

        # ================================
        # I. Lấy từ INFOBOX nếu có
        # ================================
        try:
            birth_element = driver.find_element(By.XPATH,
                "//th[text()='Born' or text()='Birth Date']/following-sibling::td")
            birth_text = birth_element.text.strip()
            birth_lines = birth_text.split("\n")
            birth = extract_date("\n".join(birth_lines))

            try:
                death_element = driver.find_element(By.XPATH,
                    "//th[text()='Died' or text()='Death Date']/following-sibling::td")
                death_text = death_element.text.strip()
                death_lines = death_text.split("\n")
                death = extract_date("\n".join(death_lines))
            except:
                death = ""

            # nationality từ Infobox
            try:
                nat_element = driver.find_element(By.XPATH,
                    "//th[text()='Nationality']/following-sibling::td")
                nationality = nat_element.text.strip()
            except:
                # Nếu không có → thử lấy từ dòng cuối Born
                if birth_lines:
                    last_line = birth_lines[-1].strip()
                    last_line = re.sub(r'\d', '', last_line)
                    if "," in last_line:
                        nationality = last_line.split(",")[-1].strip()
                    else:
                        nationality = last_line

        # ================================
        # II. Không có INFOBOX → Lấy từ paragraph đầu
        # ================================
        except:
            try:
                paragraphs = driver.find_elements(By.XPATH, "//div[@id='mw-content-text']//p")
                text = ""
                for p in paragraphs[:5]:
                    text += p.text + " "
                text = re.sub(r'\[.*?\]', '', text)

                # Trường hợp: born … - died …
                born_died_match = re.search(
                    r'born\s+([^-\n,]+).*?-\s*died\s+([^,)\n]+.*?)(?:,|\))', 
                    text, flags=re.IGNORECASE)
                if born_died_match:
                    birth = born_died_match.group(1).strip()
                    death_full = born_died_match.group(2).strip()
                    if ',' in death_full:
                        parts = death_full.split(',')
                        death = parts[0].strip()
                        nationality = parts[-1].strip()
                    else:
                        death = death_full

                # Trường hợp: (YYYY – YYYY)
                if not birth or not death:
                    matches = re.findall(r'\(([^)]*?\d{3,4}[^)]*?)\)', text)
                    if matches:
                        date_text = matches[0]
                        parts = date_text.split("–")
                        birth = extract_date(parts[0])
                        death = extract_date(parts[1]) if len(parts) > 1 else ""

                # Lấy nationality từ câu was/is a/an … painter/artist
                nat_match = re.search(r'(?:was|is) an? (.*?) (?:painter|artist)', text)
                if nat_match:
                    words = nat_match.group(1).split()
                    # loại bỏ các từ mô tả
                    words = [w for w in words if w.lower() not in descriptors]
                    if words:
                        nationality = words[-1]
                # Nếu vẫn không có → lấy từ nơi sinh
                if not nationality:
                    born_match = re.search(r'[Bb]orn\s.*?in\s([A-Za-z\s]+)', text)
                    if born_match:
                        nationality = born_match.group(1).strip()

            except:
                birth = ""
                death = ""
                nationality = ""

        # Thêm vào DataFrame
        painter = {'name': name, 'birth': birth, 'death': death, 'nationality': nationality}
        d = pd.concat([d, pd.DataFrame([painter])], ignore_index=True)

    except Exception as e:
        print("Error getting info:", e)
        continue

driver.quit()

#################################
# IV. Xuất Excel
print(d)
file_name = 'Painters.xlsx'
d.to_excel(file_name, index=False)
print('Dataframe is written to Excel File successfully.')
