import time
import os
from auth import get_cookies_dict, COOKIES_FILE
from parser import parse_questions_page
from database import init_db, save_batch, question_exists
from playwright.sync_api import sync_playwright

def run_crawler():
    """
    Crawler usando Playwright para bypassar o Cloudflare do Estude Grátis.
    """
    init_db()
    
    if not os.path.exists(COOKIES_FILE):
        print("Cookies não encontrados. Execute o auth.py primeiro para fazer login.")
        return
        
       # "atualidades-e-conhecimentos-gerais": 1243, 
    materias = {
       "algoritmos-e-estrutura-de-dados": 1284, 
       "arquitetura-de-software": 1257, 
       "banco-de-dados": 1255, 
       "ciencia-da-computacao": 1284, 
       "ciencia-e-tecnologia": 1284, 
       "conhecimentos-gerais": 1243, 
       "direitos-humanos": 1284, 
       "engenharia-de-redes": 1249, 
       "engenharia-de-software": 1257, 
       "estatística": 1242, 
       "informática-básica-microinformática": 1274, 
       "ingles": 1237, 
       "portugues": 1233, 
       "matemática": 1242, 
       "programação": 1275, 
       "raciocínio-lógico": 1239, 
       "redes-de-computadores": 1249, 
       "segurança-da-informação": 1270, 
       "sistemas-de-informação": 1284, 
       "sistemas-operacionais": 1274
    }
    
    import json
    import re
    import unicodedata
    
    def slugify(text):
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')
        
    print("Iniciando Playwright para coleta...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless=False para evitar bloqueios
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        import json
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
            context.add_cookies(cookies)
            
        page = context.new_page()
        
        for materia, subgrupo_id in materias.items():
            print(f"\\nIniciando coleta da matéria: {materia.upper()}")
            materia_slug = slugify(materia)
            base_url = f"https://www.estudegratis.com.br/questoes-de-concurso/materia/{materia_slug}/banca/fgv"
            
            p_num = 1
            while True:
                url = f"{base_url}?pag={p_num}" if p_num > 1 else base_url
                print(f"[Página {p_num}] Acessando {url} ...")
                
                resp = None
                for tentativa in range(3):
                    try:
                        resp = page.goto(url, timeout=60000)
                        break
                    except Exception as e:
                        print(f"  Erro ao acessar {url} (Tentativa {tentativa+1}/3): {e}")
                        time.sleep(2)
                
                if resp is None:
                    print(f"  Falha ao acessar {url} após 3 tentativas. Fim desta matéria.")
                    break
                # Verifica se a página retornou 404 ou o título é de não encontrada
                if resp and resp.status == 404:
                    print(f"  Página {p_num} retornou 404. Fim das páginas para a matéria {materia}.")
                    break
                if "Página não encontrada" in page.title():
                    print(f"  Página {p_num} não encontrada (404 na tela). Fim das páginas para a matéria {materia}.")
                    break
                
                # Espera carregar os blocos de questão
                try:
                    page.wait_for_selector('.questao-card', timeout=8000)
                except Exception:
                    print(f"  Timeout ou sem questões na página {p_num} para a matéria {materia}. Movendo para próxima página ou matéria.")
                    break # Fim das questões ou erro de carregamento
                    
                html = page.content()
                questoes = parse_questions_page(html)
                print(f"  Encontradas {len(questoes)} questões na página.")
                
                if len(questoes) == 0:
                    print(f"  Fim das páginas para a matéria {materia} (0 questões retornadas pelo parser).")
                    break
                
                novas_questoes = []
                for q in questoes:
                    ext_id = q.get('external_id')
                    if ext_id and not question_exists(q.get('questao')):
                        q['subgrupo_id'] = subgrupo_id
                        try:
                            api_resp = context.request.post(
                                "https://www.estudegratis.com.br/api/salvar-resolucao.php",
                                data={"questao_id": ext_id, "resposta": "A"},
                                headers={"X-Requested-With": "XMLHttpRequest"}
                            )
                            if api_resp.ok:
                                data = api_resp.json()
                                gab = data.get("gabarito")
                                if gab:
                                    q['gabarito'] = str(gab).upper()
                        except Exception as e:
                            print(f"  Erro ao buscar gabarito da {ext_id}: {e}")
                            
                        novas_questoes.append(q)
                        time.sleep(0.5)
                    
                if novas_questoes:
                    save_batch(novas_questoes)
                    print(f"  Salvas {len(novas_questoes)} novas questões no banco.")
                else:
                    print("  Todas as questões desta página já existem no banco. Fim desta matéria (site repetindo páginas).")
                    break
                
                if len(questoes) < 10:
                    print(f"  A página retornou menos de 10 questões ({len(questoes)}). Fim desta matéria.")
                    break
                    
                p_num += 1
                    
        browser.close()
        print("Coleta finalizada.")

if __name__ == '__main__':
    run_crawler()
