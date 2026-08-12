from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        url = 'https://www.estudegratis.com.br/buscar?q=banca:fgv'
        resp = page.goto(url)
        print(f"URL {url}: {resp.status}")
        
        try:
            page.wait_for_selector('.box-questao, .questao, .resultado', timeout=5000)
            print("Found questions!")
        except Exception as e:
            print("No questions found.", str(e))
        
        browser.close()

if __name__ == "__main__":
    run()
