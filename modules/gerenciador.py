import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime


def get_subgrupo_id(grupo, subgrupo, DB_PATH):
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT id FROM subgrupos WHERE nome = ?", (subgrupo,))
    row = cur.fetchone()
    sub_id = None
    if row:
        sub_id = row[0]
    else:
        cur.execute("SELECT id FROM grupos WHERE nome = ?", (grupo,))
        row_g = cur.fetchone()
        if row_g: g_id = row_g[0]
        else:
            cur.execute("INSERT INTO grupos (nome) VALUES (?)", (grupo,))
            g_id = cur.lastrowid
        cur.execute("INSERT INTO subgrupos (grupo_id, nome, peso) VALUES (?, ?, 1.0)", (g_id, subgrupo))
        sub_id = cur.lastrowid
        conn.commit()
    conn.close()
    return sub_id

def render(DB_PATH):
    st.header("Gerenciador de Questões 🛠️")
    st.markdown("Busque questões por tema ou por palavra-chave para editar o gabarito, o enunciado ou removê-las do banco.")
    
    tab_busca, tab_tema, tab_add = st.tabs(["Busca por Texto", "Filtro por Tema", "Adicionar Questão"])
    
    if "gerenciador_results" not in st.session_state:
        st.session_state.gerenciador_results = pd.DataFrame()
        
    with tab_busca:
        termo = st.text_input("Digite um trecho da questão ou palavra-chave:")
        if st.button("Buscar por Texto", key="btn_busca_txt"):
            if termo.strip():
                terms = termo.strip().split()
                like_clauses = " AND ".join([f"enunciado LIKE '%{t}%'" for t in terms])
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(f"SELECT * FROM questoes WHERE {like_clauses} LIMIT 100", conn)
                conn.close()
                st.session_state.gerenciador_results = df
            else:
                st.warning("Digite algo para buscar.")
                
    with tab_tema:
        conn = sqlite3.connect(DB_PATH)
        df_g = pd.read_sql_query("SELECT id, nome FROM grupos ORDER BY nome", conn)
        grupo_sel = st.selectbox("Selecione o Grupo:", df_g['nome'].tolist() if not df_g.empty else [])
        
        if grupo_sel:
            g_id = df_g[df_g['nome'] == grupo_sel].iloc[0]['id']
            df_s = pd.read_sql_query(f"SELECT id, nome FROM subgrupos WHERE grupo_id = {g_id} ORDER BY nome", conn)
            sub_sel = st.selectbox("Selecione o Subgrupo:", df_s['nome'].tolist() if not df_s.empty else [])
            
            if st.button("Buscar por Tema", key="btn_busca_tema"):
                if sub_sel:
                    s_id = df_s[df_s['nome'] == sub_sel].iloc[0]['id']
                    df = pd.read_sql_query(f"SELECT * FROM questoes WHERE subgrupo_id = {s_id} LIMIT 100", conn)
                    st.session_state.gerenciador_results = df
        conn.close()
        
    with tab_add:
        st.subheader("Adicionar Nova Questão Manualmente")
        
        conn = sqlite3.connect(DB_PATH)
        df_g_add = pd.read_sql_query("SELECT id, nome FROM grupos ORDER BY nome", conn)
        df_todas_subs_add = pd.read_sql_query('SELECT s.id, s.grupo_id, g.nome as grupo, s.nome as subgrupo FROM subgrupos s JOIN grupos g ON s.grupo_id = g.id ORDER BY g.nome, s.nome', conn)
        conn.close()
        
        list_g_nomes_add = df_g_add['nome'].tolist() if not df_g_add.empty else []
        
        colG_add, colS_add = st.columns(2)
        with colG_add:
            novo_g_check = st.checkbox("➕ Nova Matéria (Grupo)", key="check_novo_g")
            if novo_g_check:
                add_g_nome = st.text_input("Digite a Nova Matéria", key="txt_novo_g")
            else:
                add_g_nome = st.selectbox("Grupo da Questão", list_g_nomes_add, key="add_g_nome")
        
        add_s_nomes = []
        if not novo_g_check and add_g_nome and not df_g_add.empty:
            if add_g_nome in df_g_add['nome'].values:
                add_g_id = df_g_add[df_g_add['nome'] == add_g_nome].iloc[0]['id']
                add_s_nomes = df_todas_subs_add[df_todas_subs_add['grupo_id'] == add_g_id]['subgrupo'].tolist()
            
        with colS_add:
            novo_s_check = st.checkbox("➕ Novo Tópico (Subgrupo)", key="check_novo_s")
            if novo_s_check:
                add_s_nome = st.text_input("Digite o Novo Tópico", key="txt_novo_s")
            else:
                add_s_nome = st.selectbox("Subgrupo / Tópico", add_s_nomes, key="add_s_nome")
        
        with st.form("form_add_questao", clear_on_submit=True):
            add_enun = st.text_area("Enunciado da Questão", height=150)
            
            colA, colB = st.columns(2)
            with colA:
                add_a = st.text_input("Alternativa A")
                add_b = st.text_input("Alternativa B")
                add_c = st.text_input("Alternativa C")
            with colB:
                add_d = st.text_input("Alternativa D")
                add_e = st.text_input("Alternativa E")
                add_gab = st.text_input("Gabarito Correto (A, B, C, D ou E)", max_chars=1)
                
            colBanca, colAno = st.columns(2)
            with colBanca:
                add_banca = st.text_input("Banca (ex: CESPE, FGV)")
            with colAno:
                add_ano = st.text_input("Ano (ex: 2024)")
                
            btn_add = st.form_submit_button("✅ Adicionar Questão ao Banco")
            
            if btn_add:
                if not add_enun or not add_gab or not add_s_nome or not add_g_nome:
                    st.error("Preencha ao menos a Matéria, Tópico, Enunciado e Gabarito!")
                else:
                    # Usando a função inteligente para buscar ou criar
                    add_s_id = get_subgrupo_id(add_g_nome, add_s_nome, DB_PATH)
                    
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute('''INSERT INTO questoes 
                        (enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito, subgrupo_id, banca, ano, valida)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (add_enun, add_a, add_b, add_c, add_d, add_e, add_gab.upper().strip(), int(add_s_id), add_banca, add_ano))
                    conn.commit()
                    conn.close()
                    st.success("Questão adicionada e validada com sucesso! (Nova matéria criada, se não existia).")
        
    st.markdown("---")
    df_res = st.session_state.gerenciador_results
    if not df_res.empty:
        st.success(f"Encontradas {len(df_res)} questões (mostrando até 100).")
        
        conn = sqlite3.connect(DB_PATH)
        df_todas_subs = pd.read_sql_query('SELECT s.id, s.grupo_id, g.nome as grupo, s.nome as subgrupo FROM subgrupos s JOIN grupos g ON s.grupo_id = g.id ORDER BY g.nome, s.nome', conn)
        df_g = pd.read_sql_query("SELECT id, nome FROM grupos ORDER BY nome", conn)
        conn.close()
        
        map_subs_to_group = {row['id']: row['grupo_id'] for _, row in df_todas_subs.iterrows()}
        
        for idx, row in df_res.iterrows():
            q_id = row['id']
            val = row.get('valida', 0)
            
            # Formata status
            if pd.isna(val) or val == 0:
                status_str = "⚪ Não Validada"
            elif val == 1:
                status_str = "🟢 Válida"
            elif val == -1:
                status_str = "🔴 Removida"
            else:
                status_str = "⚪ Desconhecido"
                
            enunciado_trunc = str(row['enunciado'])[:80] + "..."
            
            with st.expander(f"[Q{q_id}] {status_str} | {enunciado_trunc}"):
                
                colG, colS = st.columns(2)
                
                current_sub_id = row.get('subgrupo_id')
                curr_g_id = map_subs_to_group.get(current_sub_id, df_g.iloc[0]['id'])
                
                list_g_nomes = df_g['nome'].tolist()
                curr_g_nome = df_g[df_g['id'] == curr_g_id].iloc[0]['nome']
                idx_g = list_g_nomes.index(curr_g_nome) if curr_g_nome in list_g_nomes else 0
                
                with colG:
                    sel_g_nome = st.selectbox("Grupo (Salva automaticamente ao mudar)", list_g_nomes, index=idx_g, key=f"sel_g_{q_id}")
                    
                sel_g_id_real = df_g[df_g['nome'] == sel_g_nome].iloc[0]['id']
                df_s_filtered = df_todas_subs[df_todas_subs['grupo_id'] == sel_g_id_real].reset_index(drop=True)
                list_s_nomes = df_s_filtered['subgrupo'].tolist()
                
                idx_s = 0
                if sel_g_id_real == curr_g_id:
                    curr_s_nome_df = df_s_filtered[df_s_filtered['id'] == current_sub_id]
                    if not curr_s_nome_df.empty:
                        curr_s_nome = curr_s_nome_df.iloc[0]['subgrupo']
                        if curr_s_nome in list_s_nomes:
                            idx_s = list_s_nomes.index(curr_s_nome)
                
                with colS:
                    if list_s_nomes:
                        sel_s_nome = st.selectbox("Subgrupo / Tópico", list_s_nomes, index=idx_s, key=f"sel_s_{q_id}")
                        sel_s_id_real = df_s_filtered[df_s_filtered['subgrupo'] == sel_s_nome].iloc[0]['id']
                    else:
                        st.warning("Sem subgrupos neste grupo.")
                        sel_s_id_real = current_sub_id
                        
                with st.form(key=f"form_edit_{q_id}"):
                    novo_enun = st.text_area("Enunciado", row['enunciado'], height=100)
                    
                    colA, colB = st.columns(2)
                    with colA:
                        nova_a = st.text_input("Alternativa A", row.get('alternativa_a', ''))
                        nova_b = st.text_input("Alternativa B", row.get('alternativa_b', ''))
                        nova_c = st.text_input("Alternativa C", row.get('alternativa_c', ''))
                    with colB:
                        nova_d = st.text_input("Alternativa D", row.get('alternativa_d', ''))
                        nova_e = st.text_input("Alternativa E", row.get('alternativa_e', ''))
                        novo_gab = st.text_input("Gabarito Correto (A, B, C, D ou E)", row.get('gabarito', ''))
                        
                    col1, col2 = st.columns(2)
                    with col1:
                        btn_salvar = st.form_submit_button("Salvar Edições e Validar")
                    with col2:
                        btn_remover = st.form_submit_button("🗑️ Remover Questão (Invalidar)")
                        
                    if btn_salvar:
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute('''UPDATE questoes SET 
                            enunciado=?, alternativa_a=?, alternativa_b=?, alternativa_c=?, alternativa_d=?, alternativa_e=?, gabarito=?, subgrupo_id=?, valida=1
                            WHERE id=?''', (novo_enun, nova_a, nova_b, nova_c, nova_d, nova_e, novo_gab, int(sel_s_id_real), q_id))
                        conn.commit()
                        conn.close()
                        
                        # Atualiza localmente para refletir caso abra o expander de novo sem resquisar
                        st.session_state.gerenciador_results.at[idx, 'subgrupo_id'] = int(sel_s_id_real)
                        st.session_state.gerenciador_results.at[idx, 'enunciado'] = novo_enun
                        
                        st.success("Questão salva e validada! Pesquise novamente para atualizar a lista.")
                        
                    if btn_remover:
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (q_id,))
                        conn.commit()
                        conn.close()
                        st.warning("Questão invalidada! Pesquise novamente para atualizar a lista.")
    
    
