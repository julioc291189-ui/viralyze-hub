import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

COOKIES_FILE = "cookies.json"
BASE_URL = "https://viralyze.site"
DASHBOARD_URL = "https://viralyze.site/dashboard.html"

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    if os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/chromium-browser"):
        options.binary_location = "/usr/bin/chromium-browser"

    if os.path.exists("/usr/bin/chromedriver"):
        service = Service("/usr/bin/chromedriver")
        return webdriver.Chrome(service=service, options=options)
    
    return webdriver.Chrome(options=options)

def scrape(email=None, password=None):
    driver = get_driver()
    results = []
    debug_info = {}
    try:
        print(f"[Robô] Acessando {DASHBOARD_URL}...")
        driver.get(DASHBOARD_URL)
        time.sleep(3)

        # 1. Injeta cookies se existirem
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for c in cookies:
                        driver.add_cookie(c)
                driver.get(DASHBOARD_URL)
                time.sleep(3)
            except Exception as e:
                print(f"[Robô] Erro cookies: {e}")

        # 2. Se não estiver no dashboard, tenta fazer o login
        if "dashboard" not in driver.current_url.lower():
            driver.get(BASE_URL)
            time.sleep(3)
            
            if email and password:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    t = (inp.get_attribute("type") or "").lower()
                    n = (inp.get_attribute("name") or "").lower()
                    if t == "email" or "email" in n or t == "text":
                        inp.clear()
                        inp.send_keys(email)
                    elif t == "password" or "pass" in n or "senha" in n:
                        inp.clear()
                        inp.send_keys(password)
                
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    txt = btn.text.lower()
                    if any(w in txt for w in ["entrar", "login", "acessar", "submit"]):
                        btn.click()
                        break
                time.sleep(5)
                
                cookies = driver.get_cookies()
                with open(COOKIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(cookies, f)
                
                driver.get(DASHBOARD_URL)
                time.sleep(5)

        # Tira print de diagnóstico da tela
        driver.save_screenshot("debug_screen.png")
        debug_info["url"] = driver.current_url
        debug_info["title"] = driver.title
        try:
            debug_info["body"] = driver.find_element(By.TAG_NAME, "body").text[:800]
        except:
            debug_info["body"] = "Sem texto capturado."

        # Extrai os cards / tabelas
        selectors = [
            'tbody tr',
            '.product-card',
            '.video-card',
            'div.grid > div',
            'div[class*="product"]',
            'div[class*="item"]',
            'div[class*="card"]',
            'table tr'
        ]
        
        cards = []
        for sel in selectors:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            if len(found) > 1:
                cards = found
                break

        for idx, card in enumerate(cards):
            text_content = card.text.strip()
            if not text_content or len(text_content) < 8:
                continue

            links = card.find_elements(By.TAG_NAME, 'a')
            video_url = ""
            for link in links:
                href = link.get_attribute("href") or ""
                if any(domain in href for domain in ["tiktok", "video", "http"]):
                    video_url = href
                    break

            categoria = "Outros"
            text_lower = text_content.lower()
            if any(w in text_lower for w in ["vestido", "calça", "conjunto", "moda", "feminina", "look", "cropped"]):
                categoria = "Moda Feminina"
            elif any(w in text_lower for w in ["casa", "cozinha", "limpeza", "organizador", "achadinho", "luminária"]):
                categoria = "Achadinhos para Casa"

            results.append({
                "id": f"PROD_{idx+1:03d}",
                "titulo_bruto": text_content.split("\n")[0][:60],
                "categoria": categoria,
                "detalhes": text_content.replace("\n", " | ")[:200],
                "video_url": video_url,
                "formato": "POV / Influencer Silenciosa",
                "score_ia": 8.5
            })

    finally:
        driver.quit()

    return results, debug_info
    
