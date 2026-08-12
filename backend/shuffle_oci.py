import json
import sqlite3
import random

random.seed()

# Update TXT
with open('data/questoes/questoes.txt', 'r', encoding='utf-8') as f:
    data = json.load(f)

for q in data:
    if q.get('subgrupo') == 'OCI':
        gabarito_letra = q.get('gabarito', '').upper()
        # mapear de A..E para a key correspondente
        if not gabarito_letra or gabarito_letra not in ['A', 'B', 'C', 'D', 'E']:
            continue
        
        letras = ['a', 'b', 'c', 'd', 'e']
        correct_key = f'alternativa_{gabarito_letra.lower()}'
        correct_text = q.get(correct_key)
        
        # Coletar todas as alternativas
        alts = [q.get(f'alternativa_{l}', '') for l in letras]
        
        # Se alguma estiver vazia (não deveria), podemos ignorar o shuffle pra essa
        if not correct_text:
            continue
            
        random.shuffle(alts)
        
        # Reatribuir
        for i, l in enumerate(letras):
            q[f'alternativa_{l}'] = alts[i]
            if alts[i] == correct_text:
                q['gabarito'] = l.upper()

with open('data/questoes/questoes.txt', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Update Database
try:
    conn = sqlite3.connect('data/bancos/db_novo.sqlite', timeout=30)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito FROM questoes WHERE subgrupo_id = 1296")
    rows = cursor.fetchall()
    
    for row in rows:
        q_id = row[0]
        gabarito_letra = row[6].upper() if row[6] else ''
        if not gabarito_letra or gabarito_letra not in ['A', 'B', 'C', 'D', 'E']:
            continue
            
        idx_correct = ord(gabarito_letra) - ord('A') + 1
        correct_text = row[idx_correct]
        
        alts = list(row[1:6])
        if not correct_text:
            continue
            
        random.shuffle(alts)
        
        new_gabarito = chr(alts.index(correct_text) + ord('A'))
        
        cursor.execute('''UPDATE questoes 
                          SET alternativa_a = ?, alternativa_b = ?, 
                              alternativa_c = ?, alternativa_d = ?, alternativa_e = ?,
                              gabarito = ?
                          WHERE id = ?''', (alts[0], alts[1], alts[2], alts[3], alts[4], new_gabarito, q_id))
    
    conn.commit()
    conn.close()
    print("Alternativas embaralhadas com sucesso!")
except Exception as ex:
    print(f"Erro no banco: {ex}")

