import streamlit as st
import pandas as pd
from backend.db import get_supabase

def get_subgrupo_id(grupo, subgrupo):
    supabase = get_supabase()
    
    # 1. Busca ou cria o Grupo
    resp_g = supabase.table("grupos").select("id").eq("nome", grupo).execute()
    if resp_g.data:
        g_id = resp_g.data[0]["id"]
    else:
        resp_ins_g = supabase.table("grupos").insert({"nome": grupo}).execute()
        g_id = resp_ins_g.data[0]["id"]
        
    # 2. Busca ou cria o Subgrupo
    resp_s = supabase.table("subgrupos").select("id").eq("grupo_id", g_id).eq("nome", subgrupo).execute()
    if resp_s.data:
        sub_id = resp_s.data[0]["id"]
    else:
        resp_ins_s = supabase.table("subgrupos").insert({"grupo_id": g_id, "nome": subgrupo, "peso": 1}).execute()
        sub_id = resp_ins_s.data[0]["id"]
        
    return sub_id

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    is_admin = (user and user.email == "cydy.potter@gmail.com")

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
                query = supabase.table("questoes").select("*")
                for t in terms:
                    query = query.ilike("enunciado", f"%{t}%")
                resp = query.limit(100).execute()
                st.session_state.gerenciador_results = pd.DataFrame(resp.data)
            else:
                st.warning("Digite algo para buscar.")
                
    with tab_tema:
        df_g = pd.DataFrame(supabase.table("grupos").select("id, nome").order("nome").execute().data)
        grupo_sel = st.selectbox("Selecione o Grupo:", df_g['nome'].tolist() if not df_g.empty else [])
        
        if grupo_sel:
            g_id = df_g[df_g['nome'] == grupo_sel].iloc[0]['id']
            df_s = pd.DataFrame(supabase.table("subgrupos").select("id, nome").eq("grupo_id", g_id).order("nome").execute().data)
            sub_sel = st.selectbox("Selecione o Subgrupo:", df_s['nome'].tolist() if not df_s.empty else [])
            
            if st.button("Buscar por Tema", key="btn_busca_tema"):
                if sub_sel:
                    s_id = int(df_s[df_s['nome'] == sub_sel].iloc[0]['id'])
                    resp = supabase.table("questoes").select("*").eq("item_id", s_id).limit(100).execute()
                    st.session_state.gerenciador_results = pd.DataFrame(resp.data)
                    
    with tab_add:
        st.subheader("Adicionar Nova Questão Manualmente")
        
        df_g_add = pd.DataFrame(supabase.table("grupos").select("id, nome").order("nome").execute().data)
        
        # Buscar todos os subgrupos com seus grupos
        subs_raw = supabase.table("subgrupos").select("id, grupo_id, nome, grupos(nome)").execute().data
        todas_subs_list = []
        for s in subs_raw:
            if s.get("grupos"):
                todas_subs_list.append({
                    "id": s["id"], "grupo_id": s["grupo_id"], 
                    "grupo": s["grupos"]["nome"], "subgrupo": s["nome"]
                })
        df_todas_subs_add = pd.DataFrame(todas_subs_list)
        
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
                if not df_todas_subs_add.empty:
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
                    add_s_id = get_subgrupo_id(add_g_nome, add_s_nome)
                    
                    nova_questao = {
                        "enunciado": add_enun,
                        "alternativa_a": add_a,
                        "alternativa_b": add_b,
                        "alternativa_c": add_c,
                        "alternativa_d": add_d,
                        "alternativa_e": add_e,
                        "gabarito": add_gab.upper().strip(),
                        "item_id": int(add_s_id),
                        "banca": add_banca,
                        "ano": int(add_ano) if add_ano.isdigit() else None,
                        "valida": 1
                    }
                    supabase.table("questoes").insert(nova_questao).execute()
                    st.success("Questão adicionada e validada com sucesso! (Nova matéria criada, se não existia).")
        
    st.markdown("---")
    df_res = st.session_state.gerenciador_results
    if not df_res.empty:
        st.success(f"Encontradas {len(df_res)} questões (mostrando até 100).")
        
        # Recarregar os grupos
        df_g = pd.DataFrame(supabase.table("grupos").select("id, nome").order("nome").execute().data)
        subs_raw = supabase.table("subgrupos").select("id, grupo_id, nome, grupos(nome)").execute().data
        todas_subs_list = []
        for s in subs_raw:
            if s.get("grupos"):
                todas_subs_list.append({
                    "id": s["id"], "grupo_id": s["grupo_id"], 
                    "grupo": s["grupos"]["nome"], "subgrupo": s["nome"]
                })
        df_todas_subs = pd.DataFrame(todas_subs_list)
        
        map_subs_to_group = {row['id']: row['grupo_id'] for _, row in df_todas_subs.iterrows()} if not df_todas_subs.empty else {}
        
        for idx, row in df_res.iterrows():
            q_id = row['id']
            val = row.get('valida', 0)
            
            if pd.isna(val) or val == 0:
                status_str = "⚪ Não Validada"
            elif val == 1:
                status_str = "🟢 Válida"
            elif val == -1:
                status_str = "🔴 Removida"
            else:
                status_str = "⚪ Desconhecido"
                
            enunciado_trunc = str(row.get('enunciado', ''))[:80] + "..."
            
            with st.expander(f"[Q{q_id}] {status_str} | {enunciado_trunc}"):
                
                colG, colS = st.columns(2)
                
                current_sub_id = row.get('subgrupo_id')
                curr_g_id = map_subs_to_group.get(current_sub_id, df_g.iloc[0]['id'] if not df_g.empty else None)
                
                list_g_nomes = df_g['nome'].tolist() if not df_g.empty else []
                curr_g_nome = ""
                if curr_g_id and not df_g.empty:
                    match_g = df_g[df_g['id'] == curr_g_id]
                    if not match_g.empty:
                        curr_g_nome = match_g.iloc[0]['nome']
                        
                idx_g = list_g_nomes.index(curr_g_nome) if curr_g_nome in list_g_nomes else 0
                
                with colG:
                    sel_g_nome = st.selectbox("Grupo (Salva automaticamente ao mudar)", list_g_nomes, index=idx_g, key=f"sel_g_{q_id}")
                    
                if sel_g_nome:
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
                        novo_enun = st.text_area("Enunciado", row.get('enunciado', ''), height=100)
                        
                        colA, colB = st.columns(2)
                        with colA:
                            nova_a = st.text_input("Alternativa A", row.get('alternativa_a', '') or '')
                            nova_b = st.text_input("Alternativa B", row.get('alternativa_b', '') or '')
                            nova_c = st.text_input("Alternativa C", row.get('alternativa_c', '') or '')
                        with colB:
                            nova_d = st.text_input("Alternativa D", row.get('alternativa_d', '') or '')
                            nova_e = st.text_input("Alternativa E", row.get('alternativa_e', '') or '')
                            novo_gab = st.text_input("Gabarito Correto (A, B, C, D ou E)", row.get('gabarito', '') or '')
                            
                        # CONTROLE DE ADMIN VISUAL
                        col1, col2 = st.columns(2)
                        with col1:
                            btn_salvar = st.form_submit_button("Salvar Edições e Validar")
                        
                        btn_remover = False
                        if is_admin:
                            with col2:
                                btn_remover = st.form_submit_button("🗑️ Remover Questão (Invalidar)")
                            
                        if btn_salvar:
                            update_data = {
                                "enunciado": novo_enun,
                                "alternativa_a": nova_a,
                                "alternativa_b": nova_b,
                                "alternativa_c": nova_c,
                                "alternativa_d": nova_d,
                                "alternativa_e": nova_e,
                                "gabarito": novo_gab,
                                "item_id": int(sel_s_id_real),
                                "valida": 1
                            }
                            supabase.table("questoes").update(update_data).eq("id", q_id).execute()
                            
                            st.session_state.gerenciador_results.at[idx, 'subgrupo_id'] = int(sel_s_id_real)
                            st.session_state.gerenciador_results.at[idx, 'enunciado'] = novo_enun
                            
                            st.success("Questão salva e validada! Pesquise novamente para atualizar a lista.")
                            
                        if btn_remover:
                            supabase.table("questoes").update({"valida": -1}).eq("id", q_id).execute()
                            st.warning("Questão invalidada! Pesquise novamente para atualizar a lista.")
