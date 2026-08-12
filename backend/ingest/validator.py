from models import Questao


def validar(lista):
    questoes = []
    
    if not lista:
        return questoes

    # Se o LLM retornou um único objeto JSON em vez de um array
    if isinstance(lista, dict):
        if "enunciado" in lista:
            # É uma única questão
            lista = [lista]
        else:
            # Pode ter retornado algo como {"questoes": [...]}
            for key, value in lista.items():
                if isinstance(value, list):
                    lista = value
                    break
            else:
                lista = []

    for q in lista:
        try:
            if isinstance(q, dict):
                questoes.append(Questao(**q))
        except Exception as e:
            print(f"Erro ao validar questão: {e}")

    return questoes