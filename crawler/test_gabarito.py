from playwright.sync_api import sync_playwright
import json

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        with open('data/bancos/cookies.json', 'r') as f:
            context.add_cookies(json.load(f))
            
        ext_id = 1132867 # Exemplo do log
        resp = context.request.post(
            "https://www.estudegratis.com.br/api/salvar-resolucao.php",
            data={"questao_id": ext_id, "resposta": "A"},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        print("Status:", resp.status)
        try:
            print("JSON:", resp.json())
        except:
            print("Text:", resp.text())
            
        browser.close()

if __name__ == "__main__":
    test()
