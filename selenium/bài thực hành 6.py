from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re

# I. Tạo DataFrame rỗng để chứa dữ liệu cuối cùng
#    (mỗi hàng sẽ là 1 họa sĩ)
d = pd.DataFrame({'name': [], 'birth': [], 'death': [], 'nationality': []})

# Đường dẫn chromedriver trên máy bạn
service = Service("/Users/binh/thuc_hanh_ma_nguon_mo/selenium/chromedriver")

# Hàm helper: lấy ngày tháng từ text Wikipedia (vì có nhiều dạng lộn xộn)
def extract_date(text):
    # Xóa mấy thứ trong ngoặc vuông và ngoặc tròn để text sạch
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.strip()

    # Ba loại regex để bắt ngày tháng theo các kiểu cơ bản
    match1 = re.search(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b', text)   # 10 March 1800
    match2 = re.search(r'\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b', text)   # March 10 1800
    match3 = re.search(r'\b\d{4}\b', text)                        # chỉ có năm

    # Trả về loại match đầu tiên tìm thấy
    if match1:
        return match1.group(0)
    elif match2:
        return match2.group(0)
    elif match3:
        return match3.group(0)
    return ""

# Một số từ mô tả nghề nghiệp cần bỏ ra khi suy luận nationality
descriptors = ['portrait', 'landscape', 'historical', 'miniaturist', 'sculptor', 'painter', 'artist', 'multi-media']

# II. Lấy tất cả đường dẫn họa sĩ bắt đầu bằng chữ A
all_links = []
for i in range(65, 66):  # 65 = 'A', nhưng bạn chỉ lấy 1 ký tự
    driver = webdriver.Chrome(service=service)
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22" + chr(i) + "%22"
    try:
        driver.get(url)
        time.sleep(3)  # chờ trang load

        # Các danh sách painter nằm trong div-col
        divs = driver.find_elements(By.CLASS_NAME, "div-col")
        for div in divs:
            li_tags = div.find_elements(By.TAG_NAME, "li")
            for li in li_tags:
                try:
                    # lấy thẻ <a> trong từng <li>
                    a_tag = li.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")

                    # chỉ lấy link dạng /wiki/
                    if href and "/wiki/" in href:
                        all_links.append(href)
                except:
                    continue

        print(f"Số link thu thập được: {len(all_links)}")
    except Exception as e:
        print("Error!", e)
    driver.quit()

# Hàm lưu tạm sau mỗi họa sĩ – phòng khi crash vẫn có dữ liệu
def save_backup():
    d.to_excel("Painters_backup.xlsx", index=False)
    print("Đã lưu tạm thời → Painters_backup.xlsx")

# III. Bắt đầu cào từng họa sĩ
driver = webdriver.Chrome(service=service)
count = 0

try:
    for link in all_links:
        count += 1
        print(f"{count}: {link}")

        try:
            driver.get(link)
            time.sleep(2)  # chờ trang load

            # chuẩn bị biến rỗng để lát điền giá trị vào
            name = ""
            birth = ""
            death = ""
            nationality = ""

            # Lấy tên họa sĩ từ thẻ <h1> (thường chuẩn)
            try:
                name = driver.find_element(By.TAG_NAME, "h1").text
            except:
                name = ""

            # I. Ưu tiên lấy từ INFOBOX (bảng bên phải)
            try:
                # Lấy mục Born
                birth_element = driver.find_element(By.XPATH,
                    "//th[text()='Born' or text()='Birth Date']/following-sibling::td")
                birth_text = birth_element.text.strip()
                birth_lines = birth_text.split("\n")
                birth = extract_date("\n".join(birth_lines))

                # Lấy mục Died
                try:
                    death_element = driver.find_element(By.XPATH,
                        "//th[text()='Died' or text()='Death Date']/following-sibling::td")
                    death_text = death_element.text.strip()
                    death_lines = death_text.split("\n")
                    death = extract_date("\n".join(death_lines))
                except:
                    death = ""

                # Lấy mục Nationality (nếu có)
                try:
                    nat_element = driver.find_element(By.XPATH,
                        "//th[text()='Nationality']/following-sibling::td")
                    nationality = nat_element.text.strip()

                # Không có nationality → thử đoán từ dòng cuối của Born
                except:
                    if birth_lines:
                        last_line = birth_lines[-1].strip()
                        last_line = re.sub(r'\d', '', last_line)
                        if "," in last_line:
                            nationality = last_line.split(",")[-1].strip()
                        else:
                            nationality = last_line

            # II. Nếu không có INFOBOX → fallback sang đoạn mô tả
            except:
                try:
                    # gom vài đoạn đầu tiên của bài viết
                    paragraphs = driver.find_elements(By.XPATH, "//div[@id='mw-content-text']//p")
                    text = ""
                    for p in paragraphs[:5]:
                        text += p.text + " "

                    text = re.sub(r'\[.*?\]', '', text)  # bỏ dấu [1], [2], ...

                    # dạng "born ... – died ..."
                    born_died_match = re.search(
                        r'born\s+([^-\n,]+).*?-\s*died\s+([^,)\n]+.*?)(?:,|\))',
                        text, flags=re.IGNORECASE)
                    if born_died_match:
                        birth = born_died_match.group(1).strip()
                        death_full = born_died_match.group(2).strip()

                        # nếu sau death có ", France" thì tách ra luôn nationality
                        if ',' in death_full:
                            parts = death_full.split(',')
                            death = parts[0].strip()
                            nationality = parts[-1].strip()
                        else:
                            death = death_full

                    # dạng "(1820–1900)"
                    if not birth or not death:
                        matches = re.findall(r'\(([^)]*?\d{3,4}[^)]*?)\)', text)
                        if matches:
                            date_text = matches[0]
                            parts = date_text.split("–")
                            birth = extract_date(parts[0])
                            if len(parts) > 1:
                                death = extract_date(parts[1])

                    # dạng "was a French painter"
                    nat_match = re.search(r'(?:was|is) an? (.*?) (?:painter|artist)', text)
                    if nat_match:
                        words = nat_match.group(1).split()
                        words = [w for w in words if w.lower() not in descriptors]
                        if words:
                            nationality = words[-1]

                    # dạng "born in France"
                    if not nationality:
                        born_match = re.search(r'[Bb]orn\s.*?in\s([A-Za-z\s]+)', text)
                        if born_match:
                            nationality = born_match.group(1).strip()

                except:
                    # nếu có lỗi gì thì để trống
                    birth = ""
                    death = ""
                    nationality = ""

            # đưa vào DataFrame
            painter = {'name': name, 'birth': birth, 'death': death, 'nationality': nationality}
            d = pd.concat([d, pd.DataFrame([painter])], ignore_index=True)

            # lưu backup mỗi họa sĩ
            save_backup()

        except Exception as e:
            print("Error getting info:", e)
            continue

finally:
    # đóng chrome
    driver.quit()

    # xuất file Excel cuối cùng
    d.to_excel("Painters.xlsx", index=False)
    print(" ĐÃ LƯU VÀO: Painters.xlsx")
