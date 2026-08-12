import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
resp = requests.get('https://www.estudegratis.com.br/bancas-de-concursos', headers=headers)
print("Bancas status:", resp.status_code)
soup = BeautifulSoup(resp.text, 'html.parser')
for a in soup.find_all('a'):
    if a.get('href') and 'getulio-vargas' in a.get('href').lower() or 'fgv' in a.get('href').lower():
        print(a.get('href'))
