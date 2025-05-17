import os
import time
import requests
import email.utils
from datetime import datetime, time as dtime, timedelta, timezone
import pytz
import json
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------
# 요일별 게시판명 + 제목 리스트 (한국 시간 기준으로 판별)
# ----------------------------
title_map = {
    "Monday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 16-20"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 12-15")
    ],
    "Tuesday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 15-19"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 19-22")
    ],
    "Wednesday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 11:20-15"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 16-20")
    ],
    "Thursday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 12-16"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 16-20")
    ],
    "Friday": [
        ("216호", "202465133 피아노 최윤정 토 14-18"),
        ("208호", "토 202465133 피아노 최윤정 18-22"),
        ("216호", "202465133 피아노 최윤정 일 14-18"),
        ("208호", "일 202465133 피아노 최윤정 18-22")
    ],
    "Saturday": [],
    "Sunday": [
        ("216호 연습실 예약", "202465133 피아노 최윤정 16:40-20:40"),
        ("208호 연습실 예약", "202465133 피아노 최윤정 20:40-22:40")
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
# 오늘 요일 (한국 기준)
# ----------------------------
korea_tz = pytz.timezone("Asia/Seoul")
today_korea = datetime.now(korea_tz).strftime("%A")
titles_today = title_map.get(today_korea, [])
print(f"📅 오늘 요일 (한국 기준): {today_korea}")
print(f"✍️ 오늘 올라갈 게시글 수: {len(titles_today)}")

# ----------------------------
# 서버 시간 요청 함수 (PLATO 서버 기준)
# ----------------------------
def get_plato_server_time():
    response = requests.get("https://plato.pusan.ac.kr", timeout=5)
    server_date = response.headers['Date']
    server_time = email.utils.parsedate_to_datetime(server_date)
    return server_time

# ----------------------------
# 서버-로컬 시간 오차 계산
# ----------------------------
def get_time_offset():
    server_time = get_plato_server_time()
    local_time = datetime.now(timezone.utc)
    delta = server_time - local_time
    print(f"🧭 서버 시간 (UTC): {server_time.strftime('%H:%M:%S')} | 🕓 로컬 시간 (UTC): {local_time.strftime('%H:%M:%S')} | 📏 오차: {delta.total_seconds():.3f}초")
    return delta

# ----------------------------
# 목표 서버 시간에 맞춰 보정 대기
# ----------------------------
def wait_until_server_target_time(target_server_time_utc: datetime):
    delta = get_time_offset()
    adjusted_target_time = target_server_time_utc - delta
    print(f"⏰ 조정된 로컬 대기 목표: {adjusted_target_time.strftime('%H:%M:%S')} (서버 목표: {target_server_time_utc.strftime('%H:%M:%S')})")
    while datetime.now(timezone.utc) < adjusted_target_time:
        time.sleep(0.2)
    print("✅ 보정된 서버 시간에 도달함")

# ----------------------------
# 드라이버 경로 설정
# ----------------------------
driver_path = ChromeDriverManager().install()

# ----------------------------
# 게시글 작성 및 제출 함수
# ----------------------------
def prepare_and_post(board_name, title):
    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    try:
        print(f"🌐 로그인 및 준비 시작 - {board_name}")
        driver.get("https://plato.pusan.ac.kr/")

        # 로그인 단계
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "input-username")))
        driver.find_element(By.ID, "input-username").send_keys(PLATO_ID)
        driver.find_element(By.ID, "input-password").send_keys(PLATO_PW)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "loginbutton"))).click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page-footer")))
        print(f"✅ 로그인 성공 - {board_name}")

        # 게시판으로 이동
        link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "연습실 예약")))
        driver.execute_script("arguments[0].scrollIntoView(true);", link)
        driver.execute_script("arguments[0].click();", link)

        #게시판 클릭
        board_xpath = f"//span[@class='instancename' and normalize-space(.)='{board_name} 게시판']"
        board_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, board_xpath)))

        a_tag = board_elem.find_element(By.XPATH, "./ancestor::a")
        driver.execute_script("arguments[0].scrollIntoView(true);", a_tag)
        driver.execute_script("arguments[0].click();", a_tag)
        print(f"🟢 게시판 진입 성공 - {board_name}")

        # 글쓰기 화면으로 이동
        write_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn.btn-primary")))
        driver.execute_script("arguments[0].scrollIntoView(true);", write_btn)
        driver.execute_script("arguments[0].click();", write_btn)

        # 제목 입력
        safe_title = json.dumps(title)
        driver.execute_script(f"""
            const subjectInput = document.getElementById('id_subject');
            subjectInput.value = {safe_title};
            subjectInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            subjectInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """)

        # 디버깅용 확인
        subject_value = driver.execute_script("return document.getElementById('id_subject').value;")
        print(f"📝 제목 확인: {subject_value}")


        # 본문 입력 처리 - Atto 에디터용
        try:
            print("📝 Atto 에디터에 본문 입력 시도 중...")
            driver.execute_script("""
                const attoDiv = document.querySelector('div.editor_atto_content[contenteditable="true"]');
                if (attoDiv) {
                    attoDiv.focus();
                    attoDiv.innerHTML = '<p>.</p>';
                    attoDiv.dispatchEvent(new Event('input', { bubbles: true }));
                    attoDiv.dispatchEvent(new Event('change', { bubbles: true }));
        
                    const hiddenTextarea = document.getElementById('id_content');
                    if (hiddenTextarea) {
                        hiddenTextarea.value = '.';
                        hiddenTextarea.dispatchEvent(new Event('input', { bubbles: true }));
                        hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                } else {
                    throw new Error('Atto 에디터 div를 찾지 못했습니다.');
                }
            """)
            time.sleep(1)
            print("✅ Atto 에디터 본문 입력 성공")
        except Exception as e:
            print(f"❌ Atto 에디터 본문 입력 실패: {e}")

        
        # 서버 기준 목표 제출 시간 (예: 한국 시간 13:00 == UTC 04:00)
        target_utc_time = datetime.combine(
            datetime.utcnow().date(),
            dtime(4, 0, 0),  # 13시 KST = 04시 UTC
            tzinfo=timezone.utc
        )

        # 서버 시간 기준 목표 시각까지 보정 대기
        wait_until_server_target_time(target_utc_time)

        #글 등록 직전 상태 확인하기
        driver.save_screenshot(f"final_debug_{board_name}.png")
        with open(f"final_source_{board_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        # 제출 직전 textarea에 값이 제대로 들어갔는지 확인
        content_value = driver.execute_script("return document.getElementById('id_content').value;")
        print(f"🧾 제출 직전 textarea 값 확인: {content_value}")

        # 제출 버튼 클릭
        try:
            submit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "id_submitbutton")))
            if submit_btn.is_displayed():
                driver.execute_script("arguments[0].click();", submit_btn)
            else:
                raise Exception("❌ 제출 버튼이 표시되지 않음")
        except UnexpectedAlertPresentException:
            alert = Alert(driver)
            print(f"⚠️ 제출 중 경고창 발생: {alert.text}")
            alert.accept()
        except Exception as e:
            print(f"⚠️ 제출 버튼 예외: {e}")
            with open(f"submit_fail_page_source_{board_name}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

        # ✅ 여기에 5번 코드 넣기!
        time.sleep(2)
        current_url = driver.current_url
        print("📄 현재 URL:", current_url)
        if "article.php?id=" in current_url or "글이 등록되었습니다" in driver.page_source:
            print(f"✅ 실제 등록 성공 - {board_name} / {title}")
        else:
            print(f"⚠️ 등록 실패 가능성 있음 - {board_name} / {title}")

        
        # 제출 후 URL 및 결과 페이지 저장
        time.sleep(2)
        print("📄 현재 URL:", driver.current_url)
        with open(f"post_result_{board_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    except Exception as e:
        print(f"❌ 오류 발생 - {board_name}: {e}")
        driver.save_screenshot(f"error_{board_name}.png")
        with open(f"page_source_{board_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()
# ----------------------------
# 중복 제거된 제목 리스트 만들기
# ----------------------------
seen = set()
unique_titles_today = []
for board_name, title in titles_today:
    key = (board_name, title)
    if key not in seen:
        seen.add(key)
        unique_titles_today.append((board_name, title))


def daily_once():
    # 한국 시간 기준 오늘 13시
    korea_now = datetime.now(pytz.timezone("Asia/Seoul"))
    target_korea_time = korea_now.replace(hour=13, minute=0, second=0, microsecond=0)

    # 이미 13시가 지난 경우 스킵
    if korea_now > target_korea_time:
        print("🕐 이미 13시가 지나 실행하지 않음")
        return

    # UTC로 변환 후 대기
    target_utc_time = target_korea_time.astimezone(pytz.utc)
    wait_until_server_target_time(target_utc_time)

    # 오늘 요일에 해당하는 게시글 처리
    today_weekday = target_korea_time.strftime("%A")
    posts = title_map.get(today_weekday, [])

    seen = set()
    unique_posts = []
    for board, title in posts:
        if (board, title) not in seen:
            seen.add((board, title))
            unique_posts.append((board, title))

    threads = []
    for board, title in unique_posts:
        t = threading.Thread(target=prepare_and_post, args=(board, title))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

# 실행 엔트리포인트
if __name__ == "__main__":
    daily_once()


