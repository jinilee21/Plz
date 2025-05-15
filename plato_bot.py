import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ----------------------------
# 게시글 제목 목록 (요일별)
# ----------------------------
title_map = {
    "Monday": [
        (553004, "202465133 피아노 최윤정 16-20"),
        (552991, "202465133 피아노 최윤정 12-15"),
    ],
    "Tuesday": [
        (553004, "202465133 피아노 최윤정 15-19"),
        (552991, "202465133 피아노 최윤정 19-22"),
    ],
    "Wednesday": [
        (553004, "202465133 피아노 최윤정 11:20-15"),
        (552991, "202465133 피아노 최윤정 16-20"),
    ],
    "Thursday": [
        (553004, "202465133 피아노 최윤정 12-16"),
        (552991, "202465133 피아노 최윤정 16-20"),
    ],
    "Friday": [
        (1306558, "토 202465133 피아노 최윤정 14-18"),
        (1642697, "토 202465133 피아노 최윤정 18-22"),
        (1306558, "일 202465133 피아노 최윤정 14-18"),
        (1642697, "일 202465133 피아노 최윤정 18-22"),
    ],
    "Saturday": [],
    "Sunday": [
        (553004, "202465133 피아노 최윤정 16:40-20:40"),
        (552991, "202465133 피아노 최윤정 20:40-22:40"),
    ],
}

# ----------------------------
# 크롬 헤드리스 브라우저 설정
# ----------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# ----------------------------
# 로그인 정보 (환경변수에서 불러옴)
# ----------------------------
PLATO_ID = os.getenv("PLATO_ID")
PLATO_PW = os.getenv("PLATO_PW")

# ----------------------------
# 오늘의 게시글 제목 추출
# ----------------------------
now = datetime.now()
weekday = now.strftime("%A")
titles_today = title_map.get(weekday, [])

# ----------------------------
# 13시까지 대기
# ----------------------------
while datetime.now().hour < 13:
    print("🕒 대기 중...", datetime.now().strftime("%H:%M:%S"))
    time.sleep(10)

# ----------------------------
# 게시글 업로드 함수 (재시도 + 로그 저장)
# ----------------------------
def post_to_plato(title):
    for attempt in range(3):
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://plato.pusan.ac.kr/")

            driver.find_element(By.ID, "userid").send_keys(PLATO_ID)
            driver.find_element(By.ID, "passwd").send_keys(PLATO_PW)
            driver.find_element(By.ID, "loginbtn").click()
            time.sleep(3)

            forum_url = f"https://plato.pusan.ac.kr/mod/forum/view.php?id=123456"  # 수정 필요
            driver.get(forum_url)
            time.sleep(2)

            driver.find_element(By.LINK_TEXT, "새 토론 주제 추가").click()
            time.sleep(2)

            driver.find_element(By.ID, "id_subject").send_keys(title)
            driver.find_element(By.ID, "id_messageeditable").send_keys(".")
            driver.find_element(By.ID, "id_submitbutton").click()

            print(f"✅ 게시 완료: {title}")
            with open(f'logs/{weekday}_{now.date()}.log', 'a') as log_file:
                log_file.write(f'{datetime.now()} - 게시 성공: {title}\n')
            driver.quit()
            break
        except Exception as e:
            print(f"❌ 오류 발생: {title}, 시도 {attempt + 1}, 오류: {e}")
            time.sleep(5)
            driver.quit()
            if attempt == 2:
                with open(f'logs/{weekday}_{now.date()}.log', 'a') as log_file:
                    log_file.write(f'{datetime.now()} - 게시 실패: {title} - 오류: {e}\n')

# ----------------------------
# 오늘 제목 리스트 반복 처리
# ----------------------------
for _, title in titles_today:
    post_to_plato(title)
