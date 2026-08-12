import os
import json
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

COOKIES_FILE = 'data/bancos/cookies.json'

def login():
    """Realiza o login no Estude Grátis usando Playwright de forma interativa e salva os cookies."""
    print("Iniciando navegador para login no Estude Grátis...")
    print("ATENÇÃO: Uma janela do navegador será aberta.")
    print("Por favor, resolva o Captcha (se houver) e faça o login manualmente.")
    
    with sync_playwright() as p:
        # headless=False para permitir que o usuário interaja e passe pelo Cloudflare
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        page.goto('https://www.estudegratis.com.br/login')
        
        print("\n" + "="*50)
        print("Faça o login no navegador que acabou de abrir.")
        print("Quando você terminar e estiver logado no site, volte aqui!")
        print("="*50 + "\n")
        
        input("Pressione ENTER aqui neste terminal APÓS concluir o login no navegador...")
        
        # Exporta cookies
        cookies = context.cookies()
        os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)
            
        print("Login realizado e cookies salvos com sucesso em data/bancos/cookies.json!")
        browser.close()

def get_cookies_dict():
    """Retorna os cookies no formato dict para usar no requests.Session()."""
    if not os.path.exists(COOKIES_FILE):
        return None
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    return {cookie['name']: cookie['value'] for cookie in cookies}

if __name__ == '__main__':
    login()
