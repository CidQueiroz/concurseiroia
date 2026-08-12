import json
import sqlite3

def run():
    with open('data/resumos/estudos.txt', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect('data/bancos/db_novo.sqlite')
    cur = conn.cursor()
    
    # 1. Create a special subgroup "FORA DO EDITAL" if it doesn't exist
    cur.execute("SELECT id FROM grupos WHERE nome = 'FORA DO EDITAL'")
    row = cur.fetchone()
    if row:
        g_fora_id = row[0]
    else:
        cur.execute("INSERT INTO grupos (nome) VALUES ('FORA DO EDITAL')")
        g_fora_id = cur.lastrowid
        
    cur.execute("SELECT id FROM subgrupos WHERE grupo_id = ? AND nome = 'DESCARTAR'", (g_fora_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO subgrupos (grupo_id, nome, peso) VALUES (?, 'DESCARTAR', 0.0)", (g_fora_id,))

    # 2. Insert the Edital Tree
    # Grupos 1 a 5 = Basic (peso 1.0), 6 a 16 = Específicos (peso 2.5)
    for index, item in enumerate(data['conteudo']):
        grupo_nome = item['grupo'].strip()
        is_basic = (index < 5)
        peso = 1.0 if is_basic else 2.5
        
        cur.execute("SELECT id FROM grupos WHERE nome = ?", (grupo_nome,))
        row = cur.fetchone()
        if row:
            g_id = row[0]
        else:
            cur.execute("INSERT INTO grupos (nome) VALUES (?)", (grupo_nome,))
            g_id = cur.lastrowid
            
        for sub in item['subgrupos']:
            sub_nome = sub['subgrupo'].strip()
            # If subgroup doesn't exist in this group, insert it
            cur.execute("SELECT id FROM subgrupos WHERE grupo_id = ? AND nome = ?", (g_id, sub_nome))
            s_row = cur.fetchone()
            if s_row:
                s_id = s_row[0]
                cur.execute("UPDATE subgrupos SET peso = ? WHERE id = ?", (peso, s_id))
            else:
                cur.execute("INSERT INTO subgrupos (grupo_id, nome, peso) VALUES (?, ?, ?)", (g_id, sub_nome, peso))
                
    conn.commit()
    conn.close()
    print("Edital setup completed successfully.")

if __name__ == '__main__':
    run()
