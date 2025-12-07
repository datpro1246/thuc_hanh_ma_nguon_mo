from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re

# I. KHỞI TẠO CẤU TRÚC DỮ LIỆU & HÀM XỬ LÝ
# DataFrame rỗng – nơi chứa kết quả cuối cùng
d = pd.DataFrame({'name': [], 'birth': [], 'death': [], 'nationality': []})

# Danh sách link đến từng họa sĩ
all_links = []

# Danh sách từ cần bỏ khi suy luận quốc tịch từ mô tả
descriptors = [
    'portrait', 'landscape', 'historical', 'miniaturist',
    'sculptor', 'painter', 'artist', 'multi-media'
]

# Đường dẫn ChromeDriver
service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver")


# Hàm lọc và chuẩn hóa ngày tháng
def extract_date(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.strip()

    match1 = re.search(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b', text)
    match2 = re.search(r'\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b', text)
    match3 = re.search(r'\b\d{4}\b', text)

    if match1: return match1.group(0)
    if match2: return match2.group(0)
    if match3: return match3.group(0)
    return ""


# Lưu backup sau mỗi họa sĩ
def save_backup():
    d.to_excel("Painters_backup.xlsx", index=False)
    print("Đã lưu tạm → Painters_backup.xlsx")


# II. CÀO LINK THEO CHỮ CÁI A → Z (mỗi chữ 15 người)
for i in range(65, 91):   # ASCII 65–90 → A–Z

    driver = webdriver.Chrome(service=service)

    url = (
        "https://en.wikipedia.org/wiki/"
        "List_of_painters_by_name_beginning_with_%22" + chr(i) + "%22"
    )

    collected = 0  # đếm số họa sĩ của từng chữ cái

    try:
        driver.get(url)
        time.sleep(3)

        divs = driver.find_elements(By.CLASS_NAME, "div-col")

        for div in divs:
            li_tags = div.find_elements(By.TAG_NAME, "li")

            for li in li_tags:

                if collected >= 15:
                    break

                try:
                    a_tag = li.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")

                    if href and "/wiki/" in href:
                        all_links.append(href)
                        collected += 1

                except:
                    continue

            if collected >= 15:
                break

        print(f"Chữ cái {chr(i)} → đã lấy {collected} link")

    except Exception as e:
        print("Lỗi khi lấy danh sách:", e)

    driver.quit()


# III. LẶP QUA TỪNG LINK – CÀO THÔNG TIN HỌA SĨ
driver = webdriver.Chrome(service=service)
count = 0

try:
    for link in all_links:
        count += 1
        print(f"\n===== {count}. Đang xử lý: {link} =====")

        try:
            driver.get(link)
            time.sleep(2)

            name = birth = death = nationality = ""

            # 1. Tên
            try:
                name = driver.find_element(By.TAG_NAME, "h1").text
            except:
                pass

            # 2. Ưu tiên Infobox
            try:
                # Born
                birth_element = driver.find_element(
                    By.XPATH, "//th[text()='Born' or text()='Birth Date']/following-sibling::td"
                )
                birth_text = birth_element.text.strip()
                birth_lines = birth_text.split("\n")
                birth = extract_date("\n".join(birth_lines))

                # Died
                try:
                    death_element = driver.find_element(
                        By.XPATH, "//th[text()='Died' or text()='Death Date']/following-sibling::td"
                    )
                    death_text = death_element.text.strip()
                    death_lines = death_text.split("\n")
                    death = extract_date("\n".join(death_lines))
                except:
                    pass

                # Nationality
                try:
                    nat_element = driver.find_element(
                        By.XPATH, "//th[text()='Nationality']/following-sibling::td"
                    )
                    nationality = nat_element.text.strip()
                except:
                    if birth_lines:
                        last_line = re.sub(r'\d', '', birth_lines[-1]).strip()
                        nationality = last_line.split(",")[-1].strip()

            # 3. Nếu không có infobox → fallback paragraphs
            except:
                try:
                    paragraphs = driver.find_elements(
                        By.XPATH, "//div[@id='mw-content-text']//p"
                    )
                    text = " ".join([p.text for p in paragraphs[:5]])
                    text = re.sub(r'\[.*?\]', '', text)

                    # born ... – died ...
                    born_died = re.search(
                        r'born\s+([^-\n,]+).*?-\s*died\s+([^,)\n]+.*?)',
                        text, flags=re.IGNORECASE
                    )
                    if born_died:
                        birth = born_died.group(1).strip()
                        death_full = born_died.group(2).strip()
                        if "," in death_full:
                            death = death_full.split(",")[0].strip()
                            nationality = death_full.split(",")[-1].strip()
                        else:
                            death = death_full

                    # (1820–1900)
                    if not birth or not death:
                        matches = re.findall(r'\(([^)]*?\d{3,4}[^)]*?)\)', text)
                        if matches:
                            range_text = matches[0]
                            parts = range_text.split("–")
                            birth = extract_date(parts[0])
                            if len(parts) > 1:
                                death = extract_date(parts[1])

                    # was a French painter
                    nat_match = re.search(
                        r'(?:was|is) an? (.*?) (?:painter|artist)',
                        text, flags=re.IGNORECASE
                    )
                    if nat_match:
                        words = [
                            w for w in nat_match.group(1).split()
                            if w.lower() not in descriptors
                        ]
                        if words:
                            nationality = words[-1]

                    # born in France
                    if not nationality:
                        born_match = re.search(
                            r'[Bb]orn\s.*?in\s([A-Za-z\s]+)',
                            text
                        )
                        if born_match:
                            nationality = born_match.group(1).strip()

                except:
                    birth = death = nationality = ""

            # 4. Lưu vào DataFrame
            painter = {
                'name': name,
                'birth': birth,
                'death': death,
                'nationality': nationality
            }

            d = pd.concat([d, pd.DataFrame([painter])], ignore_index=True)

            save_backup()

        except Exception as e:
            print("Lỗi khi xử lý họa sĩ:", e)
            continue

finally:
    driver.quit()
    d.to_excel("Painters.xlsx", index=False)
    print("\n====> ĐÃ LƯU FILE CUỐI: Painters.xlsx")
