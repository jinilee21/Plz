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
# 로그인 정보
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
# 13시까지 대기 (필요시 주석 해제)
# ----------------------------
# while datetime.now().hour < 13:
#     print("🕒 대기 중...", datetime.now().strftime("%H:%M:%S"))
#     time.sleep(10)

# ----------------------------
# 게시글 작성 함수
# ----------------------------
def post_to_plato(forum_id, title):
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://plato.pusan.ac.kr/")

        # 로그인 입력 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "input-username"))
        )
        driver.find_element(By.ID, "input-username").send_keys(PLATO_ID)
        driver.find_element(By.ID, "input-password").send_keys(PLATO_PW)

        # 로그인 버튼 클릭 대기 → 클릭
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "loginbutton"))
        ).click()

        time.sleep(3)

        # ✅ 로그인 성공 확인
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "page-footer"))  # 또는 사용자 메뉴의 ID
            )
            print("✅ 로그인 성공")
        except:
            print("❌ 로그인 실패: 아이디 또는 비밀번호가 잘못됐거나, 페이지 로딩 실패")
            driver.save_screenshot("login_failed.png")
            driver.quit()
            return
        # 게시판 진입
        forum_url = f"https://plato.pusan.ac.kr/mod/forum/view.php?id={forum_id}"
        driver.get(forum_url)
        time.sleep(2)

        # "쓰기" 버튼 클릭
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
            ).click()
            print("🟢 '쓰기' 버튼 클릭 성공")
        except Exception as e:
            print("❌ '쓰기' 버튼 클릭 실패:", e)
            driver.save_screenshot("write_button_error.png")
            return
        time.sleep(2)

        # 제목 입력
        try:
            driver.find_element(By.ID, "id_subject").send_keys(title)
            print("🟢 제목 입력 성공")
        except Exception as e:
            print("❌ 제목 입력 실패:", e)
            driver.save_screenshot("subject_error.png")
            return
        # 본문 작성 (간단히 마침표)
        try:
            driver.execute_script("document.getElementById('id_content').value = '.'")
            print("🟢 본문 입력 성공")
        except Exception as e:
            print("❌ 본문 입력 실패 (JS):", e)
            driver.save_screenshot("content_error.png")
            return
        # 게시 클릭
        try:
            driver.find_element(By.ID, "id_submitbutton").click()
            print(f"✅ 게시 완료: {title}")

        except Exception as e:
            print("❌ 제출 버튼 클릭 실패:", e)
            driver.save_screenshot("submit_error.png")
            with open("submit_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        finally:
            if driver:
                driver.quit()

# ----------------------------
# 오늘의 게시글들 반복 업로드
# ----------------------------
for forum_id, title in titles_today:
    post_to_plato(forum_id, title)
