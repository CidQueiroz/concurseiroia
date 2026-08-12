import sqlite3
import os

DB_PATH = 'data/bancos/db_novo.sqlite'

def init_db():
    pass

def save_batch(questoes_list):
    """Saves a batch of questions to the database using a transaction."""
    if not questoes_list:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executemany('''
        INSERT INTO questoes (
            enunciado, alternativa_a, alternativa_b, alternativa_c, 
            alternativa_d, alternativa_e, gabarito, banca, ano, subgrupo_id, origem, valida
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EstudeGratis', 1)
    ''', [(
        q.get('questao'), q.get('alternativa_a'), q.get('alternativa_b'), 
        q.get('alternativa_c'), q.get('alternativa_d'), q.get('alternativa_e'), q.get('gabarito'), 
        q.get('banca'), q.get('ano'), q.get('subgrupo_id')
    ) for q in questoes_list])
    
    conn.commit()
    conn.close()

def question_exists(enunciado):
    """Checks if a question already exists in the database by its enunciado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM questoes WHERE enunciado = ?', (enunciado,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
