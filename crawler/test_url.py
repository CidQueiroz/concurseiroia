from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    resp = page.goto('https://www.estudegratis.com.br/banca/fundacao-getulio-vargas-fgv')
    print("banca/:", resp.status)
    resp2 = page.goto('https://www.estudegratis.com.br/questoes-de-concurso/banca/fundacao-getulio-vargas-fgv')
    print("questoes-de-concurso/banca/:", resp2.status)
    browser.close()
