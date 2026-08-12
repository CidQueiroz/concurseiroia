import os
import yaml

def parse_edital():
    """
    Lê o arquivo estudos.yaml e retorna um 
    dicionário onde a chave é o nome do Grupo e o valor é uma lista de 
    dicionários contendo 'nome' (o nome do subgrupo) e 'conteudo' (se houver).
    """
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), "estudos.yaml")
    
    if not os.path.exists(caminho):
        return {}
        
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = yaml.safe_load(f)
            
        edital = {}
        for item in dados.get("conteudo", []):
            grupo_nome = item.get("grupo")
            if not grupo_nome:
                continue
                
            subgrupos_lista = []
            for sg in item.get("subgrupos", []):
                sg_nome = sg.get("subgrupo")
                if sg_nome:
                    subgrupos_lista.append({
                        "nome": sg_nome,
                        "conteudo": sg.get("conteudo", None)
                    })
                    
            edital[grupo_nome] = subgrupos_lista
            
        return edital
        
    except yaml.YAMLError as e:
        print(f"Erro ao ler o YAML do edital: {e}")
        return {}
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return {}

if __name__ == "__main__":
    from pprint import pprint
    pprint(parse_edital())
