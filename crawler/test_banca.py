from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url1 = 'https://www.estudegratis.com.br/banca/fundacao-getulio-vargas-fgv'
        resp1 = page.goto(url1)
        print(f"URL 1 {url1}: {resp1.status}")
        
        url2 = 'https://www.estudegratis.com.br/questoes-de-concurso/banca/fundacao-getulio-vargas-fgv'
        resp2 = page.goto(url2)
        print(f"URL 2 {url2}: {resp2.status}")
        
        url3 = 'https://www.estudegratis.com.br/questoes-de-concurso/banca/fgv'
        resp3 = page.goto(url3)
        print(f"URL 3 {url3}: {resp3.status}")
        
        browser.close()

if __name__ == "__main__":
    run()
