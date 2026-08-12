import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime


def get_assuntos(DB_PATH):
    from backend.database.queries import query_subgrupos_ordenados
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect(DB_PATH, timeout=15)
    df = pd.read_sql_query(query_subgrupos_ordenados(), conn)
    conn.close()
    return df

def render(DB_PATH):
    st.header("Cronograma de Batalha 📅 (Motor AMV 2.0)")
    st.markdown("Esqueça tabelas rígidas! A Inteligência Artificial monta o seu cronograma diário todos os dias com base na sua **curva de esquecimento** (Spaced Repetition).")
    
    from backend.scheduler import montar_plano_diario
    novos, revs = montar_plano_diario()
    
    # Montar agenda em DF
    import pandas as pd
    agenda = []
    t_start = 8 # começa as 08:00
    for n in novos:
        agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Apreensão & Active Recall", "Tópico": f"{n['grupo_nome']} - {n['subgrupo_nome']}"})
        t_start += 1
        
    for r in revs:
        agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Revisão Espaçada (SRS)", "Tópico": f"{r['grupo_nome']} - {r['subgrupo_nome']}"})
        t_start += 1
        
    agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Modo Prova (Resistência)", "Tópico": "Misto"})
    
    df_agenda = pd.DataFrame(agenda)
    st.dataframe(df_agenda, width="stretch", hide_index=True)
    
    st.markdown("---")
    st.subheader("Resumo de Questões no Banco 📚")
    
    conn_db = sqlite3.connect(DB_PATH, timeout=15)
    from backend.database.queries import query_resumo_questoes_por_grupo
    try:
        df_resumo = pd.read_sql_query(query_resumo_questoes_por_grupo(), conn_db)
        if not df_resumo.empty:
            st.dataframe(
                df_resumo, 
                column_config={
                    "Grupo": "Disciplina (Grupo)",
                    "Total": "Total de Questões",
                    "Validadas": "Validadas ✅",
                    "Não Validadas": "Não Validadas ⚠️"
                },
                width="stretch", 
                hide_index=True
            )
        else:
            st.info("O banco de dados ainda não possui estatísticas de questões.")
    except Exception as e:
        st.error(f"Erro ao carregar resumo de questões: {e}")
    conn_db.close()
    
    
