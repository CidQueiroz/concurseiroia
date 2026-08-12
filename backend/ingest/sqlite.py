import sqlite3

def salvar(lista):
    conn = sqlite3.connect("data/bancos/db_novo.sqlite", timeout=15)
    cur = conn.cursor()

    for q in lista:
        # Verifica se a questão já existe (usando os primeiros 60 caracteres)
        prefix = q.enunciado[:60].strip()
        cur.execute("SELECT id FROM questoes WHERE enunciado LIKE ?", (f"{prefix}%",))
        if cur.fetchone():
            continue

        # get_or_create_grupo ("Não Classificado")
        nome_grupo = "Não Classificado"
        cur.execute("SELECT id FROM grupos WHERE nome = ?", (nome_grupo,))
        row_grupo = cur.fetchone()
        if row_grupo:
            grupo_id = row_grupo[0]
        else:
            cur.execute("INSERT INTO grupos (nome) VALUES (?)", (nome_grupo,))
            grupo_id = cur.lastrowid

        # get_or_create_subgrupo (usamos o 'tema' temporariamente)
        cur.execute("SELECT id FROM subgrupos WHERE grupo_id = ? AND nome = ?", (grupo_id, q.tema))
        row_subgrupo = cur.fetchone()
        if row_subgrupo:
            subgrupo_id = row_subgrupo[0]
        else:
            cur.execute("INSERT INTO subgrupos (grupo_id, nome) VALUES (?, ?)", (grupo_id, q.tema))
            subgrupo_id = cur.lastrowid

        # insert_questao
        cur.execute("""
INSERT INTO questoes(
subgrupo_id,
banca,
ano,
enunciado,
alternativa_a,
alternativa_b,
alternativa_c,
alternativa_d,
alternativa_e,
gabarito
)
VALUES(
?,?,?,?,?,?,?,?,?,?
)
""",
(
subgrupo_id,
q.banca,
q.ano,
q.enunciado,
q.alternativas.get("A", "N/A"),
q.alternativas.get("B", "N/A"),
q.alternativas.get("C", "N/A"),
q.alternativas.get("D", "N/A"),
q.alternativas.get("E", "N/A"),
q.gabarito
)
)

    conn.commit()
    conn.close()