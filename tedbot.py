import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from supabase import create_client, Client

# ==========================================
# 🔧 1. 수파베이스 설정
# ==========================================
SUPABASE_URL = "https://xuaoetbkjbuokugprssl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1YW9ldGJramJ1b2t1Z3Byc3NsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExNjY2MTIsImV4cCI6MjA5Njc0MjYxMn0.83uFvaO297axM7zUvvOR8odg7OuQX5m_kB7vcTz3q0M"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

views_selector = "#__next > div.css-8d1p21.ezvkq1v0 > div > div > div > div.css-1oodiyi.e1yglk3s2 > div.css-id9ywc.e87qmeb0 > p > em:nth-child(3)"
likes_selector = "#__next > div.css-8d1p21.ezvkq1v0 > div > div > div > div.css-1oodiyi.e1yglk3s2 > div.css-s03pr7.e176hhnb0 > div:nth-child(1) > button"
comments_selector = "#__next > div.css-8d1p21.ezvkq1v0 > div > div > div > div.css-1oodiyi.e1yglk3s2 > div.css-sc2lyq.e1hgieb00 > div > div.css-1g8xvac.edq92ul1 > div > strong > em"
bookmarks_selector = "#__next > div.css-8d1p21.ezvkq1v0 > div > div > div > div.css-1oodiyi.e1yglk3s2 > div.css-s03pr7.e176hhnb0 > div:nth-child(2) > button"

# ==========================================
# 👻 2. 크롬 브라우저 설정 (시크릿 모드 추가!)
# ==========================================
chrome_options = Options()
# chrome_options.add_argument("--headless") # 유령 모드를 켜려면 앞의 '#'을 지우세요.
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--incognito") # 과거 캐시를 무시하는 시크릿 모드 장착!

def scrape_and_update_all():
    print("\n🚀 [DB 확인] 등록된 작품 목록을 불러옵니다...")
    response = supabase.table("works").select("*").execute()
    works_list = response.data
    
    if not works_list:
        print("⚠️ 창고가 비어있습니다. TED 앱에서 URL을 먼저 등록해주세요.")
        return

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        for work in works_list:
            url = work.get("entry_url")
            work_id = work.get("id")
            work_name = work.get("work_name")
            
            if not url or "playentry.org" not in url:
                continue
                
            print(f"\n🔍 [{work_name}] 데이터 수집 중... ({url})")
            driver.get(url)
            time.sleep(8) 
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            def get_number(selector):
                element = soup.select_one(selector)
                if element:
                    clean_text = element.text.replace(',', '').replace('조회', '').strip()
                    return int(clean_text) if clean_text.isdigit() else 0
                return 0

            views = get_number(views_selector)
            likes = get_number(likes_selector)
            comments = get_number(comments_selector)
            bookmarks = get_number(bookmarks_selector)

            if views == 0 and likes == 0:
                print(f"⚠️ {work_name}의 숫자를 읽지 못했습니다. 주소가 잘못되었거나 로딩이 덜 끝났을 수 있습니다.")
                continue

            try:
                supabase.table("works").update({
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "bookmarks": bookmarks
                }).eq("id", work_id).execute()
                print(f"✅ 업데이트 완료 -> 조회수: {views}, 좋아요: {likes}")
            except Exception as e:
                print(f"❌ DB 업데이트 에러: {e}")

        driver.quit()
        print("\n🏁 모든 작품의 순회가 끝났습니다!")

    except Exception as e:
        print(f"\n❌ 크롬 통신 에러: {e}")
        print("⚠️ 창이 닫혔거나 통신이 끊어졌습니다. 다음 사이클을 기다립니다.")

# ==========================================
# ⏰ 3. 스케줄러 (1분 간격으로 단축!)
# ==========================================
print("==================================")
print("  🤖 TED 1분 전역 순찰 봇 가동 시작")
print("==================================")

while True:
    scrape_and_update_all()
    wait_time = 60 # 60초(1분) 대기!
    print(f"\n💤 대기 중... 다음 순찰은 {wait_time}초 뒤 시작됩니다.")
    time.sleep(wait_time)