import os
import json
import asyncio
from playwright.async_api import async_playwright

COOKIES_FILE = "cookies.json"
BASE_URL = "https://viralyze.site"
DASHBOARD_URL = "https://viralyze.site/dashboard.html"

async def login_and_save_cookies(page, email, password):
    """Realiza login no site e salva os cookies localmente."""
    print("[Robô] Acessando página de login...")
    await page.goto(BASE_URL, wait_until="networkidle")
    
    await page.fill('input[type="email"], input[name="email"]', email)
    await page.fill('input[type="password"], input[name="password"]', password)
    
    await page.click('button[type="submit"], input[type="submit"], button:has-text("Entrar"), button:has-text("Login")')
    await page.wait_for_url("**/dashboard.html*", timeout=15000)
    
    cookies = await page.context.cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    print("[Robô] Login realizado com sucesso! Cookies salvos.")

async def run_viralyze_scraper(email: str = None, password: str = None, headless: bool = True):
    """Executa a raspagem dos produtos em alta no Viralyze."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()

        # 1. Tenta carregar cookies salvos
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                print("[Robô] Cookies carregados com sucesso.")
            except Exception as e:
                print(f"[Robô] Erro ao carregar cookies: {e}")

        page = await context.new_page()

        # 2. Navega até o dashboard
        print(f"[Robô] Acessando {DASHBOARD_URL}...")
        await page.goto(DASHBOARD_URL, wait_until="networkidle")

        # Se foi redirecionado para a tela de login, refaz o login
        if "dashboard" not in page.url:
            if not email or not password:
                await browser.close()
                raise ValueError("Sessão expirada. Informe e-mail e senha para renovar o acesso.")
            await login_and_save_cookies(page, email, password)
            await page.goto(DASHBOARD_URL, wait_until="networkidle")

        # 3. Extração dos cards de produtos
        await page.wait_for_timeout(3000)
        cards = await page.query_selector_all('.product-card, .video-card, tr, .card, div[data-product]')
        
        for idx, card in enumerate(cards):
            text_content = await card.inner_text()
            if not text_content or len(text_content.strip()) < 10:
                continue

            video_link_elem = await card.query_selector('a[href*="tiktok"], a[href*="video"]')
            video_url = await video_link_elem.get_attribute("href") if video_link_elem else ""

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

        await browser.close()
        
    return results

def scrape(email=None, password=None):
    return asyncio.run(run_viralyze_scraper(email, password))
  
