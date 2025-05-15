import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------
# 요일별 게시판 ID + 제목 리스트
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
# Chrome 옵션 설정
# ----------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# ----------------------------
# 로그인 정보 (GitHub Secrets)
# ----------------------------
PLATO_ID = os.getenv("PLATO_ID")
PLATO_PW = os.getenv("PLATO_PW")

# ----------------------------
# 오늘의 요일에 해당하는 제목 리스트
# ----------------------------
now = datetime.now()
weekday = now.strftime("%A")
titles_today = title_map.get(weekday, [])

# ----------------------------
# 13시까지 대기
# ----------------------------
#while datetime.now().hour < 13:
 #   print("🕒 대기 중...", datetime.now().strftime("%H:%M:%S"))
 #   time.sleep(10)

# ----------------------------
# 게시글 작성 함수
# ----------------------------
def post_to_plato(forum_id, title):
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://plato.pusan.ac.kr/")

        # 로그인 입력칸 로딩 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "input-username"))
        )

        try:
            driver.find_element(By.ID, "input-username").send_keys(PLATO_ID)
            driver.find_element(By.ID, "input-password").send_keys(PLATO_PW)
            driver.find_element(By.ID, "loginbutton").click()
        except Exception as e:
            print("❌ 로그인 입력칸 찾기 실패:", e)
            driver.save_screenshot("login_error.png")
            return
        time.sleep(3)

        forum_url = f"https://plato.pusan.ac.kr/mod/forum/view.php?id={str(forum_id)}"
        driver.get(forum_url)
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "쓰기").click()
        time.sleep(2)

        driver.find_element(By.ID, "id_subject").send_keys(title)
        driver.execute_script("document.getElementById('id_content').value = '.'")
        driver.find_element(By.ID, "id_submitbutton").click()

        print(f"✅ 게시 완료: {title}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    finally:
        if driver:
            driver.quit()

# ----------------------------
# 오늘의 게시글들 업로드
# ----------------------------
for forum_id, title in titles_today:
    post_to_plato(forum_id, title)
