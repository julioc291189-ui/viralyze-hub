import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_FILE = "cookies.json"
LOGIN_URL = "https://viralyze.site/login.html?reason=login&next=%2Fdashboard.html"
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

def execute_login(driver, email, password):
    """Acessa a URL direta de login, aguarda os campos e clica no botão Entrar."""
    print(f"[Robô] Acessando {LOGIN_URL}...")
    driver.get(LOGIN_URL)
    
    # Aguarda os campos de input estarem visíveis na tela
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
    time.sleep(2)

    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    visible_inputs = [inp for inp in all_inputs if inp.is_displayed()]
    
    email_elem = None
    pass_elem = None
    
    for inp in visible_inputs:
        t = (inp.get_attribute("type") or "").lower()
        p = (inp.get_attribute("placeholder") or "").lower()
        n = (inp.get_attribute("name") or "").lower()
        
        if not email_elem and (t in ["email", "text"] or "email" in p or "email" in n):
            email_elem = inp
        elif not pass_elem and (t == "password" or "senha" in p or "pass" in n):
            pass_elem = inp
            
    if not email_elem and len(visible_inputs) >= 1:
        email_elem = visible_inputs[0]
    if not pass_elem and len(visible_inputs) >= 2:
        pass_elem = visible_inputs

    if email_elem and pass_elem:
        print("[Robô] Digitando credenciais...")
        email_elem.click()
        email_elem.clear()
        email_elem.send_keys(email)
        time.sleep(0.5)

        pass_elem.click()
        pass_elem.clear()
        pass_elem.send_keys(password)
        time.sleep(0.5)

        # Clica no botão verde 'Entrar'
        clicked = False
        buttons = driver.find_elements(By.XPATH, "//*[translate(normalize-space(text()), 'ENTRAR', 'entrar') = 'entrar']")
        for btn in buttons:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                break
        
        if not clicked:
            pass_elem.send_keys(Keys.RETURN)

        print("[Robô] Login submetido. Aguardando carregamento do Dashboard...")
        time.sleep(7)

        # Salva cookies da sessão autenticada
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        print("[Robô] Cookies de sessão salvos com sucesso.")

def scrape(email=None, password=None):
    driver = get_driver()
    results = []
    debug_info = {"url": "", "title": "", "body": "", "error": ""}
    
    try:
        # 1. Injeta cookies salvos se existirem
        if os.path.exists(COOKIES_FILE):
            try:
                driver.get("https://viralyze.site")
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for c in cookies:
                        driver.add_cookie(c)
                driver.get(DASHBOARD_URL)
                time.sleep(4)
            except Exception as e:
                print(f"[Robô] Erro cookies: {e}")
        else:
            driver.get(LOGIN_URL)
            time.sleep(3)

        # Se não estiver no dashboard, executa o login
        if "dashboard" not in driver.current_url.lower():
            if not email or not password:
                raise ValueError("Preencha seu e-mail e senha do Viralyze nos campos acima.")
            execute_login(driver, email, password)
            driver.get(DASHBOARD_URL)
            time.sleep(6)

        # Salva captura da tela pós-login
        driver.save_screenshot("debug_screen.png")
        debug_info["url"] = driver.current_url
        debug_info["title"] = driver.title
        try:
            debug_info["body"] = driver.find_element(By.TAG_NAME, "body").text[:800]
        except:
            debug_info["body"] = "Sem texto capturado."

        # Extrai os produtos/vídeos do Dashboard
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
            if not text_content or len(text_content) < 8 or "entrar na sua conta" in text_content.lower():
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

    except Exception as e:
        debug_info["error"] = str(e)
        print(f"[Erro no Scraper] {e}")
    finally:
        if driver:
            driver.quit()

    return results, debug_info
    
