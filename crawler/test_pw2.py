from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://www.estudegratis.com.br/')
        page.wait_for_timeout(2000)
        
        with open('test_html2.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        browser.close()

if __name__ == "__main__":
    run()
