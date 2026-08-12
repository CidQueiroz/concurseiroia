import re
import sqlite3
import json

pattern = r'(?i)\s*\b(fátic[oa]s?|faticamente|OSPF L7 P2P|OSPF L7|OSPF L2|P2P|na matriz BGP|da matriz BGP|matriz BGP|Matriz L7 BGP|ceg[oa]s? L4 tempora(?:l|is)|ceg[oa]s? L4|ceg[oa]s? tempora(?:l|is)|dogmátic[oa]s?|dogmaticamente|analógic[oa]s?|transaciona(?:l|is) L4|tempora(?:l|is))\b'

def clean_text(text):
    if not isinstance(text, str):
        return text
    cleaned = re.sub(pattern, '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\s+([.,!?:;])', r'\1', cleaned)
    cleaned = cleaned.replace('( )', '').replace('()', '')
    return cleaned

# Update questoes.txt
with open('data/questoes/questoes.txt', 'r', encoding='utf-8') as f:
    data = json.load(f)

for q in data:
    if q.get('subgrupo') == 'OCI':
        for key in ['questao', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e']:
            if key in q and q[key]:
                q[key] = clean_text(q[key])

with open('data/questoes/questoes.txt', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Update database
try:
    conn = sqlite3.connect('data/bancos/db_novo.sqlite', timeout=30)
    cursor = conn.cursor()
    cursor.execute("SELECT id, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e FROM questoes WHERE subgrupo_id = 1296")
    rows = cursor.fetchall()
    
    for row in rows:
        q_id = row[0]
        enunciado = clean_text(row[1])
        a = clean_text(row[2])
        b = clean_text(row[3])
        c = clean_text(row[4])
        d = clean_text(row[5])
        e = clean_text(row[6])
        cursor.execute('''UPDATE questoes 
                          SET enunciado = ?, alternativa_a = ?, alternativa_b = ?, 
                              alternativa_c = ?, alternativa_d = ?, alternativa_e = ?
                          WHERE id = ?''', (enunciado, a, b, c, d, e, q_id))
    
    conn.commit()
    conn.close()
    print("Sucesso! Perguntas do OCI limpas tanto no TXT quanto no Banco de Dados.")
except Exception as ex:
    print(f"Erro ao acessar banco: {ex}")
