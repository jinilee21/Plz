import os
import time
from datetime import datetime
import pytz
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------
# 요일별 게시판명 + 제목 리스트 (한국 시간 기준으로 판별)
# ----------------------------
title_map = {
    "Monday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 16-20"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 12-15"),
    ],
    "Tuesday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 15-19"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 19-22"),
    ],
    "Wednesday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 11:20-15"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 16-20"),
    ],
    "Thursday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 12-16"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 16-20"),
    ],
    "Friday": [
        ("216호", "토 202465133 피아노 최윤정 14-18"),
        ("208호", "토 202465133 피아노 최윤정 18-22"),
        ("216호", "일 202465133 피아노 최윤정 14-18"),
        ("208호", "일 202465133 피아노 최윤정 18-22"),
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
# 환경 변수에서 로그인 정보 가져오기
# ----------------------------
PLATO_ID = os.getenv("PLATO_ID")
PLATO_PW = os.getenv("PLATO_PW")

# ----------------------------
# 한국 시간으로 오늘 요일 확인
# ----------------------------
korea_tz = pytz.timezone("Asia/Seoul")
today_korea = datetime.now(korea_tz).strftime("%A")
titles_today = title_map.get(today_korea, [])

# ----------------------------
# 병렬 제출용 스레드 함수
# ----------------------------
def prepare_and_wait_post(board_name, title):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        print(f"\n🌐 로그인 및 준비 시작 - {board_name}")
        driver.get("https://plato.pusan.ac.kr/")

        # 로그인
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "input-username")))
        driver.find_element(By.ID, "input-username").send_keys(PLATO_ID)
        driver.find_element(By.ID, "input-password").send_keys(PLATO_PW)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "loginbutton"))).click()

        # 로그인 확인
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page-footer")))
        print(f"✅ 로그인 성공 - {board_name}")

        # 게시판 접근
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "연습실 예약"))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, board_name))).click()
        print(f"🟢 게시판 진입 성공 - {board_name}")

        # 글쓰기 버튼 클릭
        write_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn.btn-primary")))
        driver.execute_script("arguments[0].scrollIntoView(true);", write_btn)
        driver.execute_script("arguments[0].click();", write_btn)
        print("📝 글쓰기 준비 완료")

        # 제목/내용 작성 (제출은 나중에)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_subject"))).send_keys(title)
        driver.execute_script("document.getElementById('id_content').value = '.'")

        # 🕒 서버 시간 13시까지 대기 (UTC 기준)
        #print("⏳ 제출 대기 중 (서버 시간 기준 13시)...")
        #while datetime.utcnow().hour != 13:
        #    time.sleep(0.5)

        # 제출
        driver.find_element(By.ID, "id_submitbutton").click()
        print(f"✅ 게시 완료: {board_name} / {title}")

    except Exception as e:
        print(f"❌ 오류 발생 - {board_name}: {e}")
        driver.save_screenshot(f"error_{board_name}.png")
        with open(f"page_source_{board_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    finally:
        driver.quit()

# ----------------------------
# 게시글 병렬 준비 + 동시 제출
# ----------------------------
threads = []
for board_name, title in titles_today:
    t = threading.Thread(target=prepare_and_wait_post, args=(board_name, title))
    t.start()
    threads.append(t)

# 모든 스레드 종료까지 대기
for t in threads:
    t.join()
