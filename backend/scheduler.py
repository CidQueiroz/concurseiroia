import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = 'data/bancos/db_novo.sqlite'

def _get_peso_grupo(grupo_nome):
    if "Conhecimentos Específicos" in grupo_nome:
        return 2.5
    return 1.0

def inicializar_subgrupos():
    """Garante que todos os subgrupos do banco tenham um registro de aprendizado correspondente."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    
    # Pega todos os subgrupos
    cur.execute("SELECT id FROM subgrupos")
    subgrupos = cur.fetchall()
    
    for (sid,) in subgrupos:
        cur.execute("INSERT OR IGNORE INTO aprendizado_subgrupo (subgrupo_id) VALUES (?)", (sid,))
        
    conn.commit()
    conn.close()

def calcular_prioridade(subgrupo_id):
    """Calcula a prioridade: Peso x Dias_Sem_Revisao x (1 - Tx_Acerto) x Dificuldade"""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    df = pd.read_sql_query(f"""
        SELECT a.*, g.nome as grupo_nome 
        FROM aprendizado_subgrupo a
        JOIN subgrupos s ON a.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
        WHERE a.subgrupo_id = {subgrupo_id}
    """, conn)
    conn.close()
    
    if df.empty:
        return 0.0
        
    row = df.iloc[0]
    peso = _get_peso_grupo(row['grupo_nome'])
    
    # Dias sem revisão
    if pd.notna(row['ultima_revisao']) and row['ultima_revisao']:
        try:
            ultima_rev = pd.to_datetime(row['ultima_revisao'])
            dias_sem_revisao = max(1.0, (datetime.now() - ultima_rev).days)
        except:
            dias_sem_revisao = 1.0
    else:
        dias_sem_revisao = 1.0 # default se nunca revisou
        
    # (1 - Tx_Acerto)
    tx_acerto = float(row['taxa_acerto']) / 100.0 if row['taxa_acerto'] > 0 else 0.0
    fator_erro = max(0.1, 1.0 - tx_acerto) # min 0.1 para nao zerar
    
    fator_dificuldade = float(row['fator_dificuldade'])
    
    prioridade = peso * dias_sem_revisao * fator_erro * fator_dificuldade
    
    # Atualiza no banco
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("UPDATE aprendizado_subgrupo SET prioridade = ? WHERE subgrupo_id = ?", (prioridade, subgrupo_id))
    conn.commit()
    conn.close()
    
    return prioridade

def agendar_revisao(subgrupo_id, acertou=True):
    """Calcula os steps D+1, D+3, D+7, D+15, D+30, D+60"""
    steps = [1, 3, 7, 15, 30, 60]
    
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT numero_revisoes, status FROM aprendizado_subgrupo WHERE subgrupo_id = ?", (subgrupo_id,))
    res = cur.fetchone()
    
    if not res:
        conn.close()
        return
        
    numero_revisoes, status = res
    
    if not acertou:
        # Se errou, volta para a revisão anterior ou D+1
        novo_num_revisoes = max(0, numero_revisoes - 2)
        novo_status = 'REVISAO_1' if novo_num_revisoes > 0 else 'RETENCAO_INICIAL'
    else:
        novo_num_revisoes = numero_revisoes + 1
        # Mapeia status
        if novo_num_revisoes == 1: novo_status = 'REVISAO_1'
        elif novo_num_revisoes == 2: novo_status = 'REVISAO_2'
        elif novo_num_revisoes >= 3: novo_status = 'REVISAO_3'
        else: novo_status = status
    
    idx_dias = min(novo_num_revisoes, len(steps)-1)
    dias_para_frente = steps[idx_dias]
    
    agora = datetime.now()
    proxima = agora + timedelta(days=dias_para_frente)
    
    cur.execute("""
        UPDATE aprendizado_subgrupo 
        SET numero_revisoes = ?, status = ?, ultima_revisao = ?, proxima_revisao = ?
        WHERE subgrupo_id = ?
    """, (novo_num_revisoes, novo_status, agora.strftime('%Y-%m-%d %H:%M:%S'), proxima.strftime('%Y-%m-%d %H:%M:%S'), subgrupo_id))
    
    conn.commit()
    conn.close()
    
    atualizar_dominio(subgrupo_id)
    calcular_prioridade(subgrupo_id)

def atualizar_dominio(subgrupo_id):
    """Verifica as travas (30+ questões, >=90% acerto, 3+ revisões) para DOMINADO."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("""
        SELECT questoes_respondidas, taxa_acerto, numero_revisoes, ultima_revisao 
        FROM aprendizado_subgrupo 
        WHERE subgrupo_id = ?
    """, (subgrupo_id,))
    res = cur.fetchone()
    
    if not res:
        conn.close()
        return
        
    q_resp, tx, n_rev, ult_rev = res
    
    dominado = 0
    novo_status = None
    data_dom = None
    
    if q_resp >= 30 and tx >= 90.0 and n_rev >= 3:
        if ult_rev:
            diff_days = (datetime.now() - datetime.strptime(ult_rev, '%Y-%m-%d %H:%M:%S')).days
            if diff_days <= 30:
                dominado = 1
                novo_status = 'DOMINADO'
                data_dom = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
    if dominado == 1:
        cur.execute("UPDATE aprendizado_subgrupo SET dominado = 1, status = ?, data_dominio = ? WHERE subgrupo_id = ?", (novo_status, data_dom, subgrupo_id))
        
    # Calcula nivel_dominio de 0 a 100 baseado em heurística para os outros status
    nivel = min(100, int((tx * 0.5) + (min(q_resp, 30) / 30.0 * 25) + (min(n_rev, 3) / 3.0 * 25)))
    if dominado == 1: nivel = 100
    cur.execute("UPDATE aprendizado_subgrupo SET nivel_dominio = ? WHERE subgrupo_id = ?", (nivel, subgrupo_id))
    
    conn.commit()
    conn.close()

def processar_resposta(questao_id, acertou):
    """Acionado quando o usuário responde uma questão. Atualiza todas as métricas."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    
    # 1. Obter subgrupo da questão
    cur.execute("SELECT subgrupo_id FROM questoes WHERE id = ?", (questao_id,))
    res = cur.fetchone()
    if not res:
        conn.close()
        return
    subgrupo_id = res[0]
    
    # 2. Obter estatísticas atuais
    cur.execute("""
        SELECT questoes_respondidas, questoes_corretas, status 
        FROM aprendizado_subgrupo WHERE subgrupo_id = ?
    """, (subgrupo_id,))
    estat_res = cur.fetchone()
    
    if not estat_res:
        inicializar_subgrupos()
        cur.execute("SELECT questoes_respondidas, questoes_corretas, status FROM aprendizado_subgrupo WHERE subgrupo_id = ?", (subgrupo_id,))
        estat_res = cur.fetchone()
        if not estat_res:
            conn.close()
            return
            
    q_resp, q_corretas, status = estat_res
    
    q_resp += 1
    if acertou:
        q_corretas += 1
        
    tx_acerto = (q_corretas / q_resp) * 100.0
    
    # 3. Atualizar Fator de Dificuldade
    if tx_acerto >= 80: fd = 0.5
    elif tx_acerto >= 60: fd = 0.8
    elif tx_acerto >= 40: fd = 1.2
    elif tx_acerto >= 20: fd = 1.5
    else: fd = 2.0
    
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cur.execute("""
        UPDATE aprendizado_subgrupo 
        SET questoes_respondidas = ?, questoes_corretas = ?, taxa_acerto = ?, fator_dificuldade = ?, ultima_revisao = ?
        WHERE subgrupo_id = ?
    """, (q_resp, q_corretas, tx_acerto, fd, agora, subgrupo_id))
    
    conn.commit()
    conn.close()
    
    # 4. Agendar próxima revisão ou avançar fluxo se aplicável
    if status in ['NOVO', 'RECONHECIMENTO']:
        avancar_status(subgrupo_id, 'RETENCAO_INICIAL')
    elif status.startswith('REVISAO') or status == 'RETENCAO_INICIAL':
        agendar_revisao(subgrupo_id, acertou)
    
    atualizar_dominio(subgrupo_id)
    calcular_prioridade(subgrupo_id)

def avancar_status(subgrupo_id, novo_status):
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    if novo_status == 'RECONHECIMENTO':
        cur.execute("UPDATE aprendizado_subgrupo SET status = ?, data_primeiro_estudo = ? WHERE subgrupo_id = ?", (novo_status, agora, subgrupo_id))
    else:
        cur.execute("UPDATE aprendizado_subgrupo SET status = ? WHERE subgrupo_id = ?", (novo_status, subgrupo_id))
    conn.commit()
    conn.close()

def gravar_resumo(subgrupo_id, texto_bullets):
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("UPDATE aprendizado_subgrupo SET resumo_bullets = ? WHERE subgrupo_id = ?", (texto_bullets, subgrupo_id))
    conn.commit()
    conn.close()
    
def get_resumo(subgrupo_id):
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT resumo_bullets FROM aprendizado_subgrupo WHERE subgrupo_id = ?", (subgrupo_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res and res[0] else ""

def montar_plano_diario():
    """
    Retorna 2 listas de dicionários: 
    - novos (2 assuntos status NOVO ou RECONHECIMENTO)
    - revisoes (X assuntos onde proxima_revisao <= HOJE ou null), ordenado por prioridade
    """
    inicializar_subgrupos()
    
    conn = sqlite3.connect(DB_PATH, timeout=15)
    
    # Recalcular prioridades
    cur = conn.cursor()
    cur.execute("SELECT subgrupo_id FROM aprendizado_subgrupo")
    for (sid,) in cur.fetchall():
        calcular_prioridade(sid)
        
    df_todos = pd.read_sql_query("""
        SELECT a.*, s.nome as subgrupo_nome, g.nome as grupo_nome 
        FROM aprendizado_subgrupo a
        JOIN subgrupos s ON a.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
        WHERE g.nome != 'Não Classificado'
    """, conn)
    conn.close()
    
    if df_todos.empty:
        return [], []
    
    hoje = datetime.now()
    
    # Assuntos Novos (Bloco 1 e 2)
    df_novos = df_todos[df_todos['status'].isin(['NOVO', 'RECONHECIMENTO'])]
    df_novos = df_novos.sort_values(by='prioridade', ascending=False).head(2)
    lista_novos = df_novos.to_dict('records')
    
    # Revisões (Bloco 3)
    df_revs = df_todos[~df_todos['status'].isin(['NOVO', 'RECONHECIMENTO', 'DOMINADO', 'IGNORADO'])]
    
    def is_due(dt_str):
        if not dt_str: return True
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S') <= hoje
        except:
            return True
            
    if df_revs.empty:
        lista_revs = []
    else:
        df_revs = df_revs[df_revs['proxima_revisao'].apply(is_due)]
        df_revs = df_revs.sort_values(by='prioridade', ascending=False).head(5)
        lista_revs = df_revs.to_dict('records')
    
    return lista_novos, lista_revs
