import sqlite3
import os

DB_PATH = "data/bancos/db_novo.sqlite"
CARGA_PATH = "data/questoes/carga.txt"

def obter_id_assunto(cursor, nome_assunto):
    """Busca o ID do assunto. Se não existir, cria um genérico para não travar a importação."""
    cursor.execute("SELECT id FROM assuntos WHERE nome = ?", (nome_assunto.strip(),))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute("INSERT INTO assuntos (nome, peso) VALUES (?, 1)", (nome_assunto.strip(),))
        return cursor.lastrowid

def processar_carga():
    if not os.path.exists(CARGA_PATH):
        print(f"Arquivo não encontrado: {CARGA_PATH}")
        return

    with open(CARGA_PATH, 'r', encoding='utf-8') as file:
        conteudo = file.read()

    # Divide o arquivo em blocos de questões usando o separador
    blocos = conteudo.split('---')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    questoes_inseridas = 0

    for bloco in blocos:
        if not bloco.strip():
            continue
            
        linhas = bloco.strip().split('\n')
        dados = {}
        
        # Faz o parse de cada linha baseada na tag [CHAVE]
        for linha in linhas:
            if linha.startswith('['):
                fim_tag = linha.find(']')
                chave = linha[1:fim_tag]
                valor = linha[fim_tag+1:].strip()
                dados[chave] = valor

        try:
            assunto_id = obter_id_assunto(cursor, dados.get('ASSUNTO', 'Geral'))
            
            cursor.execute('''
                INSERT INTO questoes (assunto_id, banca, ano, dificuldade, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assunto_id,
                dados.get('BANCA', 'N/A'),
                dados.get('ANO', 0),
                dados.get('DIFICULDADE', 'N/A'),
                dados.get('ENUNCIADO', ''),
                dados.get('A', ''),
                dados.get('B', ''),
                dados.get('C', ''),
                dados.get('D', ''),
                dados.get('E', ''),
                dados.get('GABARITO', '')
            ))
            questoes_inseridas += 1
        except Exception as e:
            print(f"Erro ao inserir questão: {e}. Bloco: {dados.get('ENUNCIADO')[:30]}...")

    conn.commit()
    conn.close()
    print(f"Operação Nominal: {questoes_inseridas} questões injetadas com sucesso no banco de dados.")

if __name__ == "__main__":
    processar_carga()