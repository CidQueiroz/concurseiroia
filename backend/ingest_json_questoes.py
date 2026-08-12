import sqlite3
import json
import os

DB_PATH = 'data/bancos/db_novo.sqlite'
QUESTOES_PATH = 'data/questoes/questoes.txt'

def obter_ou_criar_grupo(cursor, nome_grupo):
    cursor.execute("SELECT id FROM grupos WHERE nome = ?", (nome_grupo.strip(),))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO grupos (nome) VALUES (?)", (nome_grupo.strip(),))
    return cursor.lastrowid

def obter_ou_criar_subgrupo(cursor, grupo_id, nome_subgrupo):
    cursor.execute("SELECT id FROM subgrupos WHERE grupo_id = ? AND nome = ?", (grupo_id, nome_subgrupo.strip()))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO subgrupos (grupo_id, nome) VALUES (?, ?)", (grupo_id, nome_subgrupo.strip()))
    return cursor.lastrowid

def inserir_questoes():
    if not os.path.exists(QUESTOES_PATH):
        print(f"Erro: Arquivo não encontrado em {QUESTOES_PATH}")
        return

    with open(QUESTOES_PATH, 'r', encoding='utf-8') as f:
        try:
            questoes_list = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Erro ao ler o arquivo JSON: {e}")
            return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    questoes_inseridas = 0

    for q in questoes_list:
        enunciado = q.get('questao', '')
        if not enunciado:
            continue

        # Evita duplicação básica (enunciado exato)
        cursor.execute("SELECT id FROM questoes WHERE enunciado = ?", (enunciado,))
        if cursor.fetchone():
            continue

        grupo_nome = q.get('grupo', 'Não Classificado')
        subgrupo_nome = q.get('subgrupo', 'Não Classificado')

        grupo_id = obter_ou_criar_grupo(cursor, grupo_nome)
        subgrupo_id = obter_ou_criar_subgrupo(cursor, grupo_id, subgrupo_nome)

        cursor.execute('''
            INSERT INTO questoes (
                subgrupo_id, banca, ano, enunciado, 
                alternativa_a, alternativa_b, alternativa_c, 
                alternativa_d, alternativa_e, gabarito, origem, valida
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'JSON', 1)
        ''', (
            subgrupo_id,
            q.get('banca', 'N/A'),
            q.get('ano', 2024),
            enunciado,
            q.get('alternativa_a', ''),
            q.get('alternativa_b', ''),
            q.get('alternativa_c', ''),
            q.get('alternativa_d', ''),
            q.get('alternativa_e', ''),
            q.get('gabarito', ''),
        ))
        questoes_inseridas += 1

    conn.commit()
    conn.close()
    print(f"{questoes_inseridas} questoes adicionadas com sucesso!")

if __name__ == '__main__':
    inserir_questoes()
