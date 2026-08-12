from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://www.estudegratis.com.br/login')
        page.wait_for_timeout(2000)
        
        # Save HTML
        with open('test_html.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
            
        print("HTML saved.")
        browser.close()

if __name__ == "__main__":
    run()
