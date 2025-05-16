import os
import time
import requests
import email.utils
from datetime import datetime, timedelta, timezone
import pytz
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

# ✅ 오늘 요일을 한국 시간 기준으로 반환
def get_korea_weekday():
    korea_tz = pytz.timezone("Asia/Seoul")
    return datetime.now(korea_tz).strftime("%A")

# ✅ PLATO 서버 시간 받아오기 (Date 헤더 기반)
def get_plato_server_time():
    response = requests.get("https://plato.pusan.ac.kr", timeout=5)
    server_date = response.headers['Date']
    return email.utils.parsedate_to_datetime(server_date)

# ✅ 서버 시간과 로컬 시간의 오차 계산
def get_time_offset():
    server_time = get_plato_server_time()
    local_time = datetime.now(timezone.utc)
    delta = server_time - local_time
    print(f"🧭 서버 시간 (UTC): {server_time.strftime('%H:%M:%S')} | 🕓 로컬 시간 (UTC): {local_time.strftime('%H:%M:%S')} | 📏 오차: {delta.total_seconds():.3f}초")
    return delta

# ✅ 목표 서버 시간까지 대기 (보정 포함)
def wait_until_server_target_time(target_server_time_utc: datetime):
    delta = get_time_offset()
    adjusted_target_time = target_server_time_utc - delta
    print(f"⏰ 조정된 로컬 대기 목표: {adjusted_target_time.strftime('%H:%M:%S')} (서버 목표: {target_server_time_utc.strftime('%H:%M:%S')})")
    while datetime.now(timezone.utc) < adjusted_target_time:
        time.sleep(0.2)
    print("✅ 보정된 서버 시간에 도달함")

# ✅ 크롬 드라이버 생성
def get_driver():
    print("🚗 크롬 드라이버 실행 중...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver_path = ChromeDriverManager().install()
    return webdriver.Chrome(service=Service(driver_path), options=chrome_options)

# ✅ PLATO 로그인
def login_to_plato(driver, user_id, user_pw):
    print("🔐 로그인 시도 중...")
    driver.get("https://plato.pusan.ac.kr/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "input-username")))
    driver.find_element(By.ID, "input-username").send_keys(user_id)
    driver.find_element(By.ID, "input-password").send_keys(user_pw)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "loginbutton"))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page-footer")))
    print("✅ 로그인 성공")

# ✅ 게시판 진입
def navigate_to_board(driver, board_name):
    print(f"📁 게시판 이동 시도 - {board_name}")
    link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "연습실 예약")))
    driver.execute_script("arguments[0].click();", link)
    xpath = f"//span[@class='instancename' and normalize-space(.)='{board_name} 게시판']"
    board_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    a_tag = board_elem.find_element(By.XPATH, "./ancestor::a")
    driver.execute_script("arguments[0].click();", a_tag)
    print(f"🟢 게시판 진입 성공 - {board_name}")

# ✅ 글쓰기 화면 진입 + 제목 + 본문 작성
def write_post(driver, board_name, title):
    print("📝 글쓰기 버튼 클릭")
    write_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn.btn-primary")))
    driver.execute_script("arguments[0].click();", write_btn)

    print(f"📝 제목 입력: {title}")
    driver.execute_script(f"""
        const subjectInput = document.getElementById('id_subject');
        subjectInput.value = `{title}`;
        subjectInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        subjectInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
    """)

    print("📝 본문 입력 (Atto 에디터)")
    driver.execute_script("""
        const attoDiv = document.querySelector('div.editor_atto_content[contenteditable="true"]');
        if (attoDiv) {
            attoDiv.focus();
            attoDiv.innerHTML = '<p>자동화 테스트 게시글입니다.</p>';
            attoDiv.dispatchEvent(new Event('input', { bubbles: true }));
            attoDiv.dispatchEvent(new Event('change', { bubbles: true }));
            const hiddenTextarea = document.getElementById('id_content');
            if (hiddenTextarea) {
                hiddenTextarea.value = '자동화 테스트 게시글입니다.';
                hiddenTextarea.dispatchEvent(new Event('input', { bubbles: true }));
                hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    """)
    print("✅ 제목/본문 입력 완료")

# ✅ 글 제출
def submit_post(driver, board_name, title):
    print("📤 제출 버튼 클릭")
    submit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "id_submitbutton")))
    driver.execute_script("arguments[0].click();", submit_btn)
    time.sleep(2)
    current_url = driver.current_url
    print("📄 현재 URL:", current_url)
    if "article.php?id=" in current_url or "글이 등록되었습니다" in driver.page_source:
        print(f"✅ 실제 등록 성공 - {board_name} / {title}")
    else:
        print(f"⚠️ 등록 실패 가능성 있음 - {board_name} / {title}")

# ✅ 전체 실행 절차 (드라이버 실행 ~ 제출)
def prepare_and_post(board_name, title):
    driver = get_driver()
    try:
        print(f"\n=== 🚀 게시 시작: {board_name} / {title} ===")
        login_to_plato(driver, os.getenv("PLATO_ID"), os.getenv("PLATO_PW"))
        navigate_to_board(driver, board_name)
        write_post(driver, board_name, title)
        target_utc_time = get_plato_server_time() + timedelta(minutes=1)
        wait_until_server_target_time(target_utc_time)
        submit_post(driver, board_name, title)
        print(f"=== ✅ 완료: {board_name} / {title} ===\n")
    except Exception as e:
        print(f"❌ 오류 발생 - {board_name}: {e}")
        driver.save_screenshot(f"error_{board_name}.png")
        with open(f"page_source_{board_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()

# ✅ 메인 실행부
def main():
    title_map = {
        "Monday": [("216호 연습실 예약", "202465133 피아노 최윤정 16-20"), ("208호 연습실 예약", "202465133 피아노 최윤정 12-15")],
        "Tuesday": [("216호 연습실 예약", "202465133 피아노 최윤정 15-19"), ("208호 연습실 예약", "202465133 피아노 최윤정 19-22")],
        "Wednesday": [("216호 연습실 예약", "202465133 피아노 최윤정 11:20-15"), ("208호 연습실 예약", "202465133 피아노 최윤정 16-20")],
        "Thursday": [("216호 연습실 예약", "202465133 피아노 최윤정 12-16"), ("208호 연습실 예약", "202465133 피아노 최윤정 16-20")],
        "Friday": [("216호", "202465133 피아노 최윤정 토 14-18"), ("208호", "토 202465133 피아노 최윤정 18-22"),
                   ("216호", "202465133 피아노 최윤정 일 14-18"), ("208호", "일 202465133 피아노 최윤정 18-22")],
        "Saturday": [],
        "Sunday": [("216호 연습실 예약", "202465133 피아노 최윤정 16:40-20:40"), ("208호 연습실 예약", "202465133 피아노 최윤정 20:40-22:40")]
    }
    weekday = get_korea_weekday()
    titles_today = list(dict.fromkeys(title_map.get(weekday, [])))
    print(f"\n📅 오늘 요일 (한국 기준): {weekday}")
    print(f"✍️ 오늘 예약할 게시글 수: {len(titles_today)}")

    threads = [threading.Thread(target=prepare_and_post, args=(board_name, title)) for board_name, title in titles_today]
    for t in threads: t.start()
    for t in threads: t.join()

# ✅ 실행
if __name__ == "__main__":
    main()
