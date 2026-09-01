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

    # Localização do Chromium no servidor Linux
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
    print("[Robô] Acessando tela de login...")
    driver.get(BASE_URL)
    time.sleep(3)

    # Preenche e-mail e senha
    email_input = driver.find_element(By.CSS_SELECTOR, 'input[type="email"], input[name="email"], input[placeholder*="email" i]')
    email_input.clear()
    email_input.send_keys(email)

    pass_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"], input[name="password"]')
    pass_input.clear()
    pass_input.send_keys(password)

    # Clica no botão de entrar
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"], button')
    submit_btn.click()

    time.sleep(5)

    # Salva cookies
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    print("[Robô] Login realizado e cookies salvos.")

def scrape(email=None, password=None):
    """Executa a raspagem com Selenium."""
    driver = get_driver()
    results = []
    try:
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
                print(f"[Robô] Erro ao carregar cookies: {e}")

        # Se não estiver no dashboard, faz login com credenciais
        if "dashboard" not in driver.current_url.lower():
            if not email or not password:
                raise ValueError("Preencha seu E-mail e Senha do Viralyze nos campos acima para o primeiro acesso.")
            login_and_save_cookies(driver, email, password)
            driver.get(DASHBOARD_URL)
            time.sleep(3)

        # 2. Extrai os cards de produtos
        cards = driver.find_elements(By.CSS_SELECTOR, '.product-card, .video-card, tr, .card, div[data-product]')
        
        for idx, card in enumerate(cards):
            text_content = card.text
            if not text_content or len(text_content.strip()) < 10:
                continue

            links = card.find_elements(By.TAG_NAME, 'a')
            video_url = ""
            for link in links:
                href = link.get_attribute("href") or ""
                if "tiktok" in href or "video" in href:
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
                "detalhes": text_content.replace("\n", " | ")[:180],
                "video_url": video_url,
                "formato": "POV / Influencer Silenciosa",
                "score_ia": 8.5
            })

    finally:
        driver.quit()

    return results
    
