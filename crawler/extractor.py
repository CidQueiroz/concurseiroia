import requests

def get_gabarito(session: requests.Session, question_id: int):
    """
    Obtém o gabarito de uma questão específica.
    Como a rota exata do site pode variar (ex: /questoes/responder, /api/gabarito),
    este é um esboço que deve ser adaptado à chamada de rede real do Estude Grátis.
    """
    try:
        # Muitas plataformas retornam o gabarito ao tentar submeter uma resposta
        url = f"https://www.estudegratis.com.br/api/questoes/responder"
        payload = {
            "questao_id": question_id,
            "alternativa": "A" # Chutamos uma alternativa para ver o retorno
        }
        
        # Fazemos a requisição (geralmente exige cookies de login já embutidos na session)
        response = session.post(url, data=payload, headers={"X-Requested-With": "XMLHttpRequest"})
        
        if response.status_code == 200:
            data = response.json()
            # Espera-se que o JSON retorne algo como {"correta": "B", "acertou": false}
            gabarito = data.get("correta") or data.get("gabarito")
            if gabarito:
                return str(gabarito).upper()
                
        # Fallback: tentar obter o HTML da questão isolada e buscar a classe de gabarito
        url_html = f"https://www.estudegratis.com.br/questao/{question_id}"
        resp_html = session.get(url_html)
        if "gabarito-correto" in resp_html.text:
            # Aqui usaria BeautifulSoup para extrair a alternativa que tem a classe certa
            pass
            
    except Exception as e:
        print(f"Erro ao buscar gabarito da questão {question_id}: {e}")
        
    return None
