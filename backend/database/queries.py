def query_subgrupos_ordenados():
    return "SELECT * FROM subgrupos ORDER BY peso DESC"

def query_cronograma_hoje(hoje: str):
    return f"SELECT * FROM cronograma WHERE data_estudo = '{hoje}'"

def query_conteudos_distintos():
    return "SELECT DISTINCT grupo, subgrupo FROM conteudos ORDER BY grupo, subgrupo"

def query_conteudo_texto(grupo: str, subgrupo: str):
    return f"SELECT texto FROM conteudos WHERE grupo = '{grupo}' AND subgrupo = '{subgrupo}'"

def query_questoes_por_subgrupo(subgrupo: str):
    return f"""
        SELECT q.* 
        FROM questoes q
        JOIN subgrupos s ON q.subgrupo_id = s.id
        WHERE s.nome = '{subgrupo}'
        AND (q.valida IS NULL OR q.valida >= 0)
        AND q.id NOT IN (SELECT questao_id FROM respostas)
        ORDER BY q.origem = 'EstudeGratis' DESC, q.valida DESC, RANDOM() LIMIT 1
    """

def query_grupos_distintos():
    return """
        SELECT DISTINCT g.nome 
        FROM questoes q 
        JOIN subgrupos s ON q.subgrupo_id = s.id 
        JOIN grupos g ON s.grupo_id = g.id 
        WHERE g.nome != 'Não Classificado'
        ORDER BY g.nome
    """

def query_prova_por_tema(tema_selecionado: str, subgrupos_selecionados=None, ineditas_apenas: bool = True):
    base_query = f"""
        SELECT q.*, s.nome as subgrupo_nome, g.nome as grupo_nome
        FROM questoes q
        JOIN subgrupos s ON q.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
        WHERE g.nome = '{tema_selecionado}' AND g.nome NOT IN ('Não Classificado', 'FORA DO EDITAL') AND (q.valida IS NULL OR q.valida >= 0)
    """
    if subgrupos_selecionados:
        s_nomes = ','.join(f"'{s}'" for s in subgrupos_selecionados)
        base_query += f" AND s.nome IN ({s_nomes})"
        
    if ineditas_apenas:
        base_query += " AND q.id NOT IN (SELECT questao_id FROM respostas)"
        
    base_query += " ORDER BY q.origem = 'EstudeGratis' DESC, q.valida DESC, RANDOM() LIMIT 200"
    return base_query

def query_simulado_geral(ineditas_apenas: bool = True):
    base_query = """
        SELECT q.*, s.nome as subgrupo_nome, g.nome as grupo_nome
        FROM questoes q
        JOIN subgrupos s ON q.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
        WHERE g.nome NOT IN ('Não Classificado', 'FORA DO EDITAL') 
        AND (q.valida IS NULL OR q.valida >= 0)
    """
    if ineditas_apenas:
        base_query += " AND q.id NOT IN (SELECT questao_id FROM respostas)"
        
    base_query += " ORDER BY q.origem = 'EstudeGratis' DESC, RANDOM()"
    return base_query

def query_respostas_historico():
    return """
        SELECT r.id, r.questao_id, r.acertou, r.tempo_segundos, q.subgrupo_id, s.nome as subgrupo_nome, g.nome as grupo_nome
        FROM respostas r
        JOIN questoes q ON r.questao_id = q.id
        JOIN subgrupos s ON q.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
    """

def query_estudos_historico():
    return """
        SELECT e.id, 
               e.inicio, 
               e.fim, 
               (strftime('%s', e.fim) - strftime('%s', e.inicio)) / 60.0 as tempo_min,
               e.subgrupo_id,
               s.nome as subgrupo_nome,
               g.nome as grupo_nome
        FROM eventos_estudo e
        JOIN subgrupos s ON e.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
        WHERE e.fim IS NOT NULL
    """

def query_respostas_com_data():
    return """
        SELECT r.data, r.acertou, g.nome as grupo_nome
        FROM respostas r
        JOIN questoes q ON r.questao_id = q.id
        JOIN subgrupos s ON q.subgrupo_id = s.id
        JOIN grupos g ON s.grupo_id = g.id
    """

def query_dominio_subgrupos():
    return '''
        SELECT 
            s.nome as Subgrupo,
            g.nome as Grupo,
            COUNT(r.id) as Total_Respondidas,
            SUM(CASE WHEN r.acertou THEN 1 ELSE 0 END) as Total_Acertos,
            (CAST(SUM(CASE WHEN r.acertou THEN 1 ELSE 0 END) AS FLOAT) / COUNT(r.id)) * 100 as Taxa_Acerto
        FROM subgrupos s
        JOIN grupos g ON s.grupo_id = g.id
        LEFT JOIN questoes q ON q.subgrupo_id = s.id
        LEFT JOIN respostas r ON r.questao_id = q.id
        GROUP BY s.id
        HAVING Total_Respondidas > 0
    '''

def query_cronograma_completo():
    return "SELECT data_estudo as Data, slot_numero as Slot, grupo as Grupo, subgrupo as 'Subgrupo/Tema' FROM cronograma ORDER BY data_estudo, slot_numero"

def query_todos_grupos():
    return "SELECT id, nome FROM grupos WHERE nome NOT IN ('Não Classificado', 'Simulados') ORDER BY nome"

def query_subgrupos_por_grupo(grupo_id: int):
    return f"SELECT id, nome FROM subgrupos WHERE grupo_id = {grupo_id} ORDER BY nome"

def query_resumo_questoes_por_grupo():
    return '''
        SELECT 
            g.nome as Grupo,
            COUNT(q.id) as Total,
            SUM(CASE WHEN q.valida = 1 THEN 1 ELSE 0 END) as Validadas,
            SUM(CASE WHEN q.valida = 0 THEN 1 ELSE 0 END) as 'Não Validadas'
        FROM grupos g
        LEFT JOIN subgrupos s ON s.grupo_id = g.id
        LEFT JOIN questoes q ON q.subgrupo_id = s.id
        GROUP BY g.id, g.nome
        HAVING Total > 0
        ORDER BY Total DESC
    '''
