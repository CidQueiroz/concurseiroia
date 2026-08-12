import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime

def render(DB_PATH):
    st.header("Conselho do Tutor: Diagnóstico de Evolução 🤖🩺")
    st.markdown("Identifique seus padrões de erro e receba um plano de ação cirúrgico.")
    
    periodo_str = st.selectbox("Selecione o período de análise:", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Todo o histórico"])
    dias_map = {"Últimos 7 dias": 7, "Últimos 15 dias": 15, "Últimos 30 dias": 30, "Todo o histórico": 9999}
    dias = dias_map[periodo_str]
    
    if st.button("Gerar Diagnóstico IA", type="primary"):
        with st.spinner("Extraindo dados do banco e consultando o Tutor IA... isso pode levar alguns segundos."):
            conn = sqlite3.connect(DB_PATH)
            
            # Estatísticas gerais do período
            query_stats = f"""
                SELECT 
                    COUNT(r.id) as total_respondidas,
                    SUM(CASE WHEN r.acertou THEN 1 ELSE 0 END) as total_acertos
                FROM respostas r
                WHERE r.data >= date('now', '-{dias} days')
            """
            cur = conn.cursor()
            cur.execute(query_stats)
            row_stats = cur.fetchone()
            total_resp = row_stats[0] or 0
            total_acertos = row_stats[1] or 0
            taxa_geral = (total_acertos / total_resp * 100) if total_resp > 0 else 0
            
            if total_resp < 5:
                st.warning("Histórico insuficiente neste período para um diagnóstico preciso. Responda mais questões!")
                conn.close()
            else:
                stats_str = f"Questões respondidas: {total_resp}\nAcertos: {total_acertos}\nTaxa de Acerto Geral: {taxa_geral:.1f}%\n\n"
                
                # Piores subgrupos (mínimo de 3 questões respondidas para não poluir com amostra pequena)
                query_piores = f"""
                    SELECT 
                        s.id, g.nome as grupo, s.nome as subgrupo,
                        COUNT(r.id) as qtd,
                        SUM(CASE WHEN r.acertou THEN 1 ELSE 0 END) * 100.0 / COUNT(r.id) as taxa
                    FROM respostas r
                    JOIN questoes q ON r.questao_id = q.id
                    JOIN subgrupos s ON q.subgrupo_id = s.id
                    JOIN grupos g ON s.grupo_id = g.id
                    WHERE r.data >= date('now', '-{dias} days')
                    AND s.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
                    AND g.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
                    GROUP BY s.id
                    HAVING qtd >= 3
                    ORDER BY taxa ASC
                    LIMIT 3
                """
                cur.execute(query_piores)
                piores = cur.fetchall()
                
                erros_detalhados = ""
                for pior in piores:
                    sub_id, grupo, subgrupo, qtd, taxa = pior
                    erros_detalhados += f"\n--- PONTO CRÍTICO: {grupo} > {subgrupo} (Taxa: {taxa:.1f}%) ---\n"
                    
                    # Pega o texto das questões erradas
                    q_erradas = f"""
                        SELECT q.enunciado, q.gabarito
                        FROM respostas r
                        JOIN questoes q ON r.questao_id = q.id
                        WHERE r.data >= date('now', '-{dias} days')
                        AND r.acertou = 0
                        AND q.subgrupo_id = {sub_id}
                        LIMIT 10
                    """
                    cur.execute(q_erradas)
                    for eq in cur.fetchall():
                        erros_detalhados += f"- Enunciado: {eq[0]}\n"
                        
                conn.close()
                
                if not erros_detalhados:
                    st.success("Não encontramos subgrupos com erros consistentes neste período! Ótimo trabalho.")
                else:
                    from backend.llm import conselho_tutor_ia
                    st.markdown("### 📝 Relatório do Tutor")
                    gerador = conselho_tutor_ia(stats_str, erros_detalhados, stream=True)
                    st.write_stream(gerador)
