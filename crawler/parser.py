from bs4 import BeautifulSoup

def parse_questions_page(html):
    """
    Analisa uma página HTML de listagem de questões e extrai os dados.
    """
    soup = BeautifulSoup(html, 'html.parser')
    questoes = []
    
    # Encontra os blocos de questão
    blocks = soup.find_all('article', class_=lambda c: c and 'questao-card' in c)
    if not blocks:
        blocks = soup.find_all('div', class_=lambda c: c and ('box-questao' in c or 'questao' in c))
        
    for block in blocks:
        try:
            # External ID
            q_id = block.get('id', '').replace('questao-', '')
            if not q_id:
                q_id = block.get('data-id', '')
            if not q_id:
                continue
                
            enunciado_elem = block.find('div', class_='questao-enunciado') or block.find('div', class_='enunciado') or block.find('div', class_='texto-questao')
            enunciado = enunciado_elem.get_text(separator='\\n', strip=True) if enunciado_elem else "Enunciado não encontrado"
            
            # Alternativas
            alts_elems = block.find_all('label', class_=lambda c: c and 'alternativa' in c)
            if not alts_elems:
                alts_elems = block.find_all('div', class_='alternativa') or block.find_all('li', class_='alternativa')
                
            alternativas = {}
            for i, alt in enumerate(alts_elems):
                if i > 4: # No máximo 5 alternativas (a, b, c, d, e)
                    break
                letra = chr(97 + i)
                texto_elem = alt.find('span', class_='alternativa-texto')
                if texto_elem:
                    texto_alt = texto_elem.get_text(strip=True)
                else:
                    texto_alt = alt.get_text(strip=True)
                alternativas[f'alternativa_{letra}'] = texto_alt

            # Metadados (Ano)
            ano = 2024
            meta_items = block.find_all('div', class_='questao-meta-item')
            for item in meta_items:
                label = item.find('span', class_='questao-meta-label')
                val = item.find('span', class_='questao-meta-value')
                if label and val and 'Ano' in label.get_text():
                    try:
                        ano = int(val.get_text(strip=True))
                    except:
                        pass
            
            questao = {
                'external_id': int(q_id) if q_id.isdigit() else 0,
                'questao': enunciado,
                'alternativa_a': alternativas.get('alternativa_a'),
                'alternativa_b': alternativas.get('alternativa_b'),
                'alternativa_c': alternativas.get('alternativa_c'),
                'alternativa_d': alternativas.get('alternativa_d'),
                'alternativa_e': alternativas.get('alternativa_e'),
                'banca': 'FGV',
                'ano': ano,
                'grupo': 'Não Classificado',
                'subgrupo': 'Não Classificado',
                'assunto': 'Extraído',
                'gabarito': None
            }
            questoes.append(questao)
        except Exception as e:
            print(f"Erro ao parsear uma questão: {e}")
            
    return questoes
