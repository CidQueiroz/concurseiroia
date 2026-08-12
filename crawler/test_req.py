import requests

url = "https://www.estudegratis.com.br/questoes-de-concurso/banca/fgv"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
with open('test_html3.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
