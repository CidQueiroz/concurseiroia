from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://www.estudegratis.com.br/questoes-de-concurso/materia/portugues/banca/fgv?pag=1')
        html = page.content()
        with open('crawler/test_questions.html', 'w') as f:
            f.write(html)
        print("HTML saved to test_questions.html")
        browser.close()

if __name__ == "__main__":
    run()
