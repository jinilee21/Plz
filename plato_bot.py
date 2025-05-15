import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

title_map = {
    "Monday": [("216", "202465133 피아노 최윤정 16-20"), ("208", "202465133 피아노 최윤정 12-15")],
    "Tuesday": [("216", "202465133 피아노 최윤정 15-19"), ("208", "202465133 피아노 최윤정 19-22")],
    "Wednesday": [("216", "202465133 피아노 최윤정 11:20-15"), ("208", "202465133 피아노 최윤정 16-20")],
    "Thursday": [("216", "202465133 피아노 최윤정 12-16"), ("208", "202465133 피아노 최윤정 16-20")],
    "Friday": [
        ("2층 주말 및 공휴일 연습실 예약 216", "토 202465133 피아노 최윤정 14-18"),
        ("2층 주말 및 공휴일 연습실 예약 208", "토 202465133 피아노 최윤정 18-22"),
        ("2층 주말 및 공휴일 연습실 예약 216", "일 202465133 피아노 최윤정 14-18"),
        ("2층 주말 및 공휴일 연습실 예약 208", "일 202465133 피아노 최윤정 18-22"),
    ],
    "Saturday": [],
    "Sunday": [("216", "202465133 피아노 최윤정 16:40-20:40"), ("208", "202465133 피아노 최윤정 20:40-22:40")],
}

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

PLATO_ID = os.getenv("PLATO_ID")
PLATO_PW = os.getenv("PLATO_PW")

now = datetime.now()
weekday = now.strftime("%A")
titles_today = title_map.get(weekday, [])

while datetime.now().hour < 13:
    print("🕒 대기 중...", datetime.now().strftime("%H:%M:%S"))
    time.sleep(10)

def post_to_plato(title):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://plato.pusan.ac.kr/")

    driver.find_element(By.ID, "userid").send_keys(PLATO_ID)
    driver.find_element(By.ID, "passwd").send_keys(PLATO_PW)
    driver.find_element(By.ID, "loginbtn").click()
    time.sleep(3)

    driver.get("https://plato.pusan.ac.kr/mod/forum/view.php?id=123456")  # 게시판 URL 수정 필요
    time.sleep(2)

    driver.find_element(By.LINK_TEXT, "새 토론 주제 추가").click()
    time.sleep(2)

    driver.find_element(By.ID, "id_subject").send_keys(title)
    driver.find_element(By.ID, "id_messageeditable").send_keys(".")
    driver.find_element(By.ID, "id_submitbutton").click()

    print(f"✅ 게시 완료: {title}")
    driver.quit()

for _, title in titles_today:
    post_to_plato(title)
