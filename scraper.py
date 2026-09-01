import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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

def execute_login(driver, email, password):
    """Preenche os campos exatos do Viralyze e clica no botão Entrar."""
    print(f"[Robô] Executando login com e-mail: {email}...")
    
    # 1. Localiza campo de e-mail
    email_input = None
    for sel in ['input[type="email"]', 'input[placeholder*="email" i]', 'input[placeholder*="Digite seu email" i]']:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        if elems and elems[0].is_displayed():
            email_input = elems[0]
            break
            
    # 2. Localiza campo de senha
    pass_input = None
    for sel in ['input[type="password"]', 'input[placeholder*="senha" i]', 'input[placeholder*="Digite a senha" i]']:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        if elems and elems[0].is_displayed():
            pass_input = elems[0]
            break

    if email_input and pass_input:
        email_input.click()
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.5)

        pass_input.click()
        pass_input.clear()
        pass_input.send_keys(password)
        time.sleep(0.5)

        # 3. Clica no botão verde 'Entrar'
        clicked = False
        buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Entrar') or contains(text(), 'entrar')]")
        for btn in buttons:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                break
        
        if not clicked:
            pass_input.send_keys(Keys.RETURN)

        # Aguarda a transição para o Dashboard
        time.sleep(6)

        # Salva cookies da sessão logada
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        print("[Robô] Sessão autenticada e cookies salvos.")

def scrape(email=None, password=None):
    driver = get_driver()
    results = []
    debug_info = {"url": "", "title": "", "body": "", "error": ""}
    
    try:
        print(f"[Robô] Acessando {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(3)

        # Injeta cookies salvos se existirem
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for c in cookies:
                        driver.add_cookie(c)
                driver.get(DASHBOARD_URL)
                time.sleep(4)
            except Exception as e:
                print(f"[Robô] Erro cookies: {e}")

        # Se a tela atual for a de login ("Entrar na sua conta"), executa o login
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "entrar na sua conta" in page_text or "dashboard" not in driver.current_url.lower():
            if not email or not password:
                raise ValueError("Preencha seu e-mail e senha do Viralyze nos campos acima.")
            execute_login(driver, email, password)

        # Tira print do que o robô vê após o login (para vermos o Dashboard)
        time.sleep(4)
        driver.save_screenshot("debug_screen.png")
        debug_info["url"] = driver.current_url
        debug_info["title"] = driver.title
        try:
            debug_info["body"] = driver.find_element(By.TAG_NAME, "body").text[:800]
        except:
            debug_info["body"] = "Sem texto capturado."

        # Extrai os cards / tabelas de produtos do Dashboard
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
    
