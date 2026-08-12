from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        resp = page.goto('https://www.estudegratis.com.br/questoes-de-concurso/materia/atualidades-e-conhecimentos-gerais/banca/fgv')
        print(f"Status: {resp.status}")
        print("Title:", page.title())
        browser.close()

if __name__ == "__main__":
    test()
