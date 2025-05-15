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
        ("216", "202465133 피아노 최윤정 16-20"),
        ("208", "202465133 피아노 최윤정 12-15"),
    ],
    "Tuesday": [
        ("216", "202465133 피아노 최윤정 15-19"),
        ("208", "202465133 피아노 최윤정 19-22"),
    ],
    "Wednesday": [
        ("216", "202465133 피아노 최윤정 11:20-15"),
        ("208", "202465133 피아노 최윤정 16-20"),
    ],
    "Thursday": [
        ("216", "202465133 피아노 최윤정 12-16"),
        ("208", "202465133 피아노 최윤정 16-20"),
    ],
    "Friday": [
        ("2층 주말 및 공휴일 연습실 예약 216", "토 202465133 피아노 최윤정 14-18"),
        ("2층 주말 및 공휴일 연습실 예약 208", "토 202465133 피아노 최윤정 18-22"),
        ("2층 주말 및 공휴일 연습실 예약 216", "일 202465133 피아노 최윤정 14-18"),
        ("2층 주말 및 공휴일 연습실 예약 208", "일 202465133 피아노 최윤정 18-22"),
    ],
    "Saturday": [],
    "Sunday": [
        ("216", "202465133 피아노 최윤정 16:40-20:40"),
        ("208", "202465133 피아노 최윤정 20:40-22:40"),
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
def post_to_plato(board_name, title):
    driver = None
    try:
        print("🌐 로그인 시도 중...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://plato.pusan.ac.kr/")

        # 로그인 입력 대기 및 입력
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "input-username")))
        driver.find_element(By.ID, "input-username").send_keys(PLATO_ID)
        driver.find_element(By.ID, "input-password").send_keys(PLATO_PW)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "loginbutton"))).click()

        # 로그인 성공 여부 확인
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page-footer")))
        print("✅ 로그인 성공")

        # 메인 페이지에서 게시판 이동
        print("🎯 '음악학과 연습실예약' 클릭 시도 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "음악학과 연습실예약"))).click()
        print("🟢 '음악학과 연습실예약' 클릭 성공")

        print(f"🎯 게시판 '{board_name}' 클릭 시도 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, board_name))).click()
        print(f"🟢 게시판 '{board_name}' 클릭 성공")

        print("📝 '쓰기' 버튼 클릭 시도 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn.btn-primary"))).click()
        print("🟢 '쓰기' 버튼 클릭 성공")

        print("📝 제목 입력 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_subject"))).send_keys(title)
        print("🟢 제목 입력 성공")

        print("📝 본문 입력 중...")
        driver.execute_script("document.getElementById('id_content').value = '.'")
        print("🟢 본문 입력 성공")

        print("📤 제출 클릭 중...")
        driver.find_element(By.ID, "id_submitbutton").click()
        print(f"✅ 게시 완료: {board_name} / {title}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if driver:
            driver.save_screenshot("error.png")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    finally:
        if driver:
            driver.quit()

# ----------------------------
# 오늘 게시글 반복 업로드
# ----------------------------
for board_name, title in titles_today:
    post_to_plato(board_name, title)
