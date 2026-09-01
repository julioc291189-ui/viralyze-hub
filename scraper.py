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
    """Inicializa o Chromium nativo do servidor Streamlit."""
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

def login_and_save_cookies(driver, email, password):
    """Realiza login no Viralyze e salva os cookies."""
    print(f"[Robô] Acessando {BASE_URL} para login...")
    driver.get(BASE_URL)
    time.sleep(4)

    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
        email_field = None
        pass_field = None
        
        for inp in inputs:
            inp_type = (inp.get_attribute("type") or "").lower()
            inp_name = (inp.get_attribute("name") or "").lower()
            inp_placeholder = (inp.get_attribute("placeholder") or "").lower()
            
            if not email_field and (inp_type == "email" or "email" in inp_name or "email" in inp_placeholder or inp_type == "text"):
                email_field = inp
            elif not pass_field and (inp_type == "password" or "pass" in inp_name or "senha" in inp_placeholder):
                pass_field = inp

        if email_field and pass_field:
            email_field.clear()
            email_field.send_keys(email)
            pass_field.clear()
            pass_field.send_keys(password)
            
            buttons = driver.find_elements(By.TAG_NAME, "button")
            clicked = False
            for btn in buttons:
                txt = btn.text.lower()
                if any(w in txt for w in ["entrar", "login", "acessar", "submit"]):
                    btn.click()
                    clicked = True
                    break
            if not clicked and buttons:
                buttons[0].click()
            elif not clicked:
                pass_field.submit()
            
            time.sleep(6)
            
            cookies = driver.get_cookies()
            with open(COOKIES_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f)
            print("[Robô] Login executado e cookies salvos.")
    except Exception as e:
        print(f"[Robô] Erro durante o login: {e}")

def scrape(email=None, password=None):
    """Executa a raspagem com Selenium e seletores abrangentes."""
    driver = get_driver()
    results = []
    try:
        print(f"[Robô] Acessando {DASHBOARD_URL}...")
        driver.get(DASHBOARD_URL)
        time.sleep(4)

        # 1. Injeta cookies salvos
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for c in cookies:
                        driver.add_cookie(c)
                driver.get(DASHBOARD_URL)
                time.sleep(4)
            except Exception as e:
                print(f"[Robô] Erro ao carregar cookies: {e}")

        # Se for redirecionado para a tela de login
        current_url = driver.current_url.lower()
        if "dashboard" not in current_url:
            if not email or not password:
                raise ValueError("Preencha seu E-mail e Senha no painel para realizar o login.")
            login_and_save_cookies(driver, email, password)
            driver.get(DASHBOARD_URL)
            time.sleep(6)

        # Aguarda renderização completa do JavaScript
        time.sleep(6)
        
        # 2. Busca por diferentes estruturas possíveis (tabelas, cards, grids)
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
            if any(w in text_lower for w in ["vestido", "calça", "conjunto", "moda", "feminina", "look", "cropped", "saia", "blusa"]):
                categoria = "Moda Feminina"
            elif any(w in text_lower for w in ["casa", "cozinha", "limpeza", "organizador", "achadinho", "luminária", "quarto", "banheiro"]):
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

    return results
