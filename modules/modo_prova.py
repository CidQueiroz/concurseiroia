import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime

def render(DB_PATH):
    st.header("Modo Prova 📝")
    
    import json
    STATE_FILE = "data/bancos/simulado_estado.json"
    
    def salvar_estado_simulado():
        if not st.session_state.get('prova_em_andamento'): return
        estado = {
            "df_prova": st.session_state.df_prova.to_dict(orient="records") if 'df_prova' in st.session_state else [],
            "questao_idx": st.session_state.questao_idx,
            "prova_respondido": st.session_state.get("prova_respondido", False),
            "prova_acertou": st.session_state.get("prova_acertou", False),
            
            "prova_chat_history": st.session_state.get("prova_chat_history", []),
            "prova_score_basic": st.session_state.get("prova_score_basic", 0.0),
            "prova_score_esp": st.session_state.get("prova_score_esp", 0.0),
            "prova_start_time": st.session_state.get("prova_start_time", None)
        }
        with open(STATE_FILE, "w") as f:
            json.dump(estado, f)
            
    # Checar se existe simulado salvo
    if os.path.exists(STATE_FILE) and not st.session_state.get('prova_em_andamento'):
        st.info("Você tem um simulado em andamento!")
        if st.button("Continuar Simulado Salvo", type="primary"):
            with open(STATE_FILE, "r") as f:
                estado = json.load(f)
            st.session_state.df_prova = pd.DataFrame(estado["df_prova"])
            st.session_state.questao_idx = estado["questao_idx"]
            st.session_state.prova_respondido = estado["prova_respondido"]
            st.session_state.prova_acertou = estado.get("prova_acertou", False)
            
            st.session_state.prova_chat_history = estado.get("prova_chat_history", [])
            st.session_state.prova_score_basic = estado.get("prova_score_basic", 0.0)
            st.session_state.prova_score_esp = estado.get("prova_score_esp", 0.0)
            st.session_state.prova_start_time = estado.get("prova_start_time", None)
            st.session_state.prova_em_andamento = True
            st.rerun()
            
    modo_prova = st.radio("Escolha a modalidade:", ["Prova por Tema", "Simulado Geral DATAPREV"], horizontal=True)
    
    from backend.database.queries import query_grupos_distintos
    conn = sqlite3.connect(DB_PATH, timeout=15)
    df_temas = pd.read_sql_query(query_grupos_distintos(), conn)
    
    tema_selecionado = None
    subgrupos_selecionados = []
    if modo_prova == "Prova por Tema":
        if not df_temas.empty:
            tema_selecionado = st.selectbox("Selecione o Tema:", df_temas['nome'].tolist())
            
            # Lê o mapa mental para pegar os subgrupos
            try:
                with open('data/resumos/mapa_mental.json', 'r', encoding='utf-8') as f:
                    mapa_mental = json.load(f)
                
                subgrupos_opcoes = []
                for item in mapa_mental.get('conteudo', []):
                    if item.get('grupo', '').strip() == tema_selecionado:
                        subgrupos_opcoes = [s.strip() for s in item.get('subgrupos', [])]
                        break
                        
                if subgrupos_opcoes:
                    subgrupos_selecionados = st.multiselect("Selecione os Subgrupos (Deixe vazio para ver todos):", subgrupos_opcoes)
            except Exception:
                pass
                
        else:
            st.warning("Nenhuma questão no banco de dados.")
            
    ineditas_apenas = st.checkbox("Somente questões inéditas (ainda não respondidas)", value=True, help="Desmarque para permitir questões que você já resolveu.")
    
    if modo_prova == "Prova por Tema" and tema_selecionado:
        st.markdown("---")
        st.markdown("**Gerador IA** (Opcional): Se o banco local estiver vazio ou se quiser testar conhecimentos novos.")
        if st.button("✨ Gerar Questão Inédita com IA para os temas selecionados", key="btn_gerar_ia_prova"):
            with st.spinner(f"Gerando questão inédita de {tema_selecionado}..."):
                from backend.llm import gerar_questao_inedita
                import random
                # Choose a subgroup randomly if multiple selected, otherwise use a generic term
                sub_escolhido = random.choice(subgrupos_selecionados) if subgrupos_selecionados else "Assuntos Gerais"
                nova_q = gerar_questao_inedita(tema_selecionado, sub_escolhido)
                if nova_q:
                    from modules.gerenciador import get_subgrupo_id
                    s_id = get_subgrupo_id(tema_selecionado, sub_escolhido, DB_PATH)
                    
                    conn_ia = sqlite3.connect(DB_PATH, timeout=15)
                    cur_ia = conn_ia.cursor()
                    alts = nova_q.get('alternativas', {})
                    if not alts:
                        alts = {"A": nova_q.get('a', 'N/A'), "B": nova_q.get('b', 'N/A'), "C": nova_q.get('c', 'N/A'), "D": nova_q.get('d', 'N/A'), "E": nova_q.get('e', 'N/A')}
                    cur_ia.execute("INSERT INTO questoes (subgrupo_id, banca, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito, valida) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", 
                                (s_id, "IA-Gerada", nova_q.get('enunciado', ''), alts.get("A", "N/A"), alts.get("B", "N/A"), alts.get("C", "N/A"), alts.get("D", "N/A"), alts.get("E", "N/A"), nova_q.get('gabarito', 'A')))
                    conn_ia.commit()
                    conn_ia.close()
                    st.success(f"Questão gerada e adicionada ao banco com sucesso! (Tema: {tema_selecionado} - {sub_escolhido}). Clique em 'Iniciar Novo Simulado' para respondê-la.")
                else:
                    st.error("Falha ao gerar questão. Verifique suas chaves de API (BYOK) ou o console.")

    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        iniciar = st.button("Iniciar Novo Simulado", type="primary")
    with col2:
        if st.button("Sair da Prova / Limpar"):
            st.session_state.prova_em_andamento = False
            if 'df_prova' in st.session_state: del st.session_state.df_prova
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            st.rerun()
    
    if iniciar:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            
        st.session_state.questao_idx = 0
        st.session_state.prova_em_andamento = True
        st.session_state.prova_respondido = False
        st.session_state.prova_chat_history = []
        st.session_state.prova_score_basic = 0.0
        st.session_state.prova_score_esp = 0.0
        
        if modo_prova == "Prova por Tema" and tema_selecionado:
            st.session_state.prova_start_time = None
            from backend.database.queries import query_prova_por_tema
            df_questoes = pd.read_sql_query(query_prova_por_tema(tema_selecionado, subgrupos_selecionados, ineditas_apenas), conn)
            df_questoes = df_questoes.drop_duplicates(subset=['enunciado'])
            st.session_state.df_prova = df_questoes.sample(frac=1).reset_index(drop=True)
            
        elif modo_prova == "Simulado Geral DATAPREV":
            st.session_state.prova_start_time = time.time()
            from backend.database.queries import query_simulado_geral
            df_todas = pd.read_sql_query(query_simulado_geral(ineditas_apenas), conn)
            df_todas = df_todas.drop_duplicates(subset=['enunciado'])
            
            dist = {
                "LÍNGUA PORTUGUESA": 12,
                "LÍNGUA INGLESA": 12,
                "RACIOCÍNIO LÓGICO MATEMÁTICO": 5,
                "ATUALIDADES E INTELIGÊNCIA ARTIFICIAL": 6,
                "LEGISLAÇÃO, SEGURANÇA E PROTEÇÃO DE DADOS": 5
            }
            
            dfs = []
            for d_nome, d_qtd in dist.items():
                df_cat = df_todas[df_todas['grupo_nome'] == d_nome]
                n_sample = min(len(df_cat), d_qtd)
                if n_sample > 0:
                    dfs.append(df_cat.sample(n_sample))
                    
            df_esp = df_todas[~df_todas['grupo_nome'].isin(dist.keys())]
            n_esp = min(len(df_esp), 30)
            if n_esp > 0:
                dfs.append(df_esp.sample(n_esp))
                
                if dfs:
                    df_simulado = pd.concat(dfs).sample(frac=1).reset_index(drop=True)
                    st.session_state.df_prova = df_simulado
                else:
                    st.session_state.df_prova = pd.DataFrame()
                    
            salvar_estado_simulado()
            
    conn.close()
    
    if st.session_state.get('prova_em_andamento') and 'df_prova' in st.session_state:
        df_prova = st.session_state.df_prova
        
        dist_basics = [
            "LÍNGUA PORTUGUESA", 
            "LÍNGUA INGLESA", 
            "RACIOCÍNIO LÓGICO MATEMÁTICO", 
            "ATUALIDADES E INTELIGÊNCIA ARTIFICIAL", 
            "LEGISLAÇÃO, SEGURANÇA E PROTEÇÃO DE DADOS"
        ]
        
        if not df_prova.empty:
            idx = st.session_state.questao_idx
            
            if idx < len(df_prova):
                q = df_prova.iloc[idx]
                respondido = st.session_state.get("prova_respondido", False)
                is_basic = str(q['grupo_nome']).strip().upper() in dist_basics
                peso = 1.0 if is_basic else 2.5
                
                
                if st.session_state.get('prova_start_time'):
                    elapsed = int(time.time() - st.session_state.prova_start_time)
                    td = datetime.timedelta(seconds=elapsed)
                    st.info(f"**⏱️ Tempo de Prova:** `{td}` *(atualizado a cada interação)*")
                    
                st.markdown("---")
                banca_str = q.get('banca', 'N/A')
                ano_raw = q.get('ano', 'N/A')
                import math
                if pd.isna(ano_raw) or ano_raw == 'N/A':
                    ano_str = 'N/A'
                else:
                    ano_str = str(int(ano_raw)) if isinstance(ano_raw, (float, int)) else str(ano_raw)
                st.caption(f"Questão {idx + 1} de {len(df_prova)} | Tema: {q['grupo_nome']} | Banca: {banca_str} | Ano: {ano_str} | Peso: {peso}")
                st.markdown(f"**{q['enunciado']}**")
                
                # Parse alternativas if it's a string
                alt = q.get('alternativas', '')
                opcoes = {}
                if isinstance(alt, str) and alt.startswith('{'):
                    try:
                        opcoes = json.loads(alt)
                    except: pass
                
                if not opcoes:
                    opcoes = {"A": q.get('alternativa_a', 'N/A'), "B": q.get('alternativa_b', 'N/A'), "C": q.get('alternativa_c', 'N/A'), "D": q.get('alternativa_d', 'N/A'), "E": q.get('alternativa_e', 'N/A')}
                
                resposta_usuario = st.radio("Selecione:", list(opcoes.keys()), format_func=lambda x: f"{x}) {opcoes[x]}", key=f"prova_radio_{idx}", disabled=respondido, index=None)
                
                if not respondido:
                    col_resp1, col_resp2, col_resp3 = st.columns([4, 4, 2])
                    with col_resp1:
                        btn_responder = st.button("Responder", type="primary", key=f"btn_conf_{idx}")
                    with col_resp2:
                        btn_mentoria_antes = st.button("Mentoria (Ajude-me a pensar)", key=f"btn_mentoria_prova_antes_{idx}")
                    with col_resp3:
                        btn_remover = st.button("🗑️ Remover Questão", key=f"btn_remover_prova_{idx}")
    
                    if btn_mentoria_antes and not st.session_state.get("prova_chat_history"):
                        from backend.llm import mentoria_ia
                        st.markdown("### 🧠 Mentoria IA")
                        with st.chat_message("assistant"):
                            gerador = mentoria_ia(q['enunciado'], opcoes, resposta_usuario, historico=[], stream=True)
                            with st.spinner("Tutor IA pensando..."):
                                resposta = st.write_stream(gerador)
                            st.session_state.prova_chat_history = [{"role": "assistant", "content": resposta}]
                        salvar_estado_simulado()
                    elif st.session_state.get("prova_chat_history"):
                        st.markdown("### 🧠 Mentoria IA")
                        for msg in st.session_state.prova_chat_history:
                            st.chat_message(msg["role"]).write(msg["content"])
                            
                    if st.session_state.get("prova_chat_history"):
                        if nova_duvida := st.chat_input("Ficou com alguma dúvida específica? Pergunte aqui...", key=f"chat_antes_{idx}"):
                            st.chat_message("user").write(nova_duvida)
                            st.session_state.prova_chat_history.append({"role": "user", "content": nova_duvida})
                            from backend.llm import mentoria_ia
                            with st.chat_message("assistant"):
                                gerador = mentoria_ia(q['enunciado'], opcoes, resposta_usuario, historico=st.session_state.prova_chat_history[:-1], stream=True)
                                with st.spinner("Tutor IA pensando..."):
                                    resposta = st.write_stream(gerador)
                                st.session_state.prova_chat_history.append({"role": "assistant", "content": resposta})
                            salvar_estado_simulado()
    
                    if btn_remover:
                        conn = sqlite3.connect(DB_PATH, timeout=15)
                        conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (int(q['id']),))
                        conn.commit()
                        
                        ids_atuais = tuple(st.session_state.df_prova['id'].tolist())
                        if len(ids_atuais) == 1:
                            ids_sql = f"({ids_atuais[0]})"
                        else:
                            ids_sql = str(ids_atuais)
                        
                        df_nova = pd.read_sql_query(f'''
                            SELECT q.*, s.nome as subgrupo_nome, g.nome as grupo_nome 
                            FROM questoes q
                            JOIN subgrupos s ON q.subgrupo_id = s.id
                            JOIN grupos g ON s.grupo_id = g.id
                            WHERE g.nome = ? AND (q.valida IS NULL OR q.valida != -1)
                            AND q.id NOT IN {ids_sql}
                            ORDER BY RANDOM() LIMIT 1
                        ''', conn, params=(q['grupo_nome'],))
                        
                        if not df_nova.empty:
                            st.session_state.df_prova.iloc[idx] = df_nova.iloc[0]
                            st.warning("Questão invalidada! Substituída por uma nova da mesma disciplina.")
                        else:
                            st.session_state.questao_idx += 1
                            st.warning("Questão invalidada! Sem substitutas disponíveis na disciplina. Avançando...")
                            
                        conn.close()
                        st.session_state.prova_chat_history = []
                        salvar_estado_simulado()
                        st.rerun()
    
                    if btn_responder:
                        if q.get('gabarito') in ['N/A', 'None'] or not q.get('gabarito'):
                            from backend.llm import resolver_gabarito_ia
                            with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                novo_gab = resolver_gabarito_ia(q['enunciado'], opcoes)
                                conn = sqlite3.connect(DB_PATH, timeout=15)
                                conn.execute("UPDATE questoes SET gabarito = ? WHERE id = ?", (novo_gab, int(q['id'])))
                                conn.commit()
                                conn.close()
                                # Update in memory
                                st.session_state.df_prova.at[idx, 'gabarito'] = novo_gab
                                q = st.session_state.df_prova.iloc[idx]
    
                        acertou = (str(resposta_usuario).strip().upper() == str(q.get('gabarito', '')).strip().upper())
                        
                        if acertou:
                            if is_basic:
                                st.session_state.prova_score_basic += 1.0
                            else:
                                st.session_state.prova_score_esp += 2.5
                        
                        conn = sqlite3.connect(DB_PATH, timeout=15)
                        cur = conn.cursor()
                        cur.execute("UPDATE questoes SET valida = 1 WHERE id = ?", (int(q['id']),))
                        cur.execute("INSERT INTO respostas (questao_id, acertou, tempo_segundos) VALUES (?, ?, ?)", (int(q['id']), bool(acertou), 0))
                        conn.commit()
                        
                        from backend.scheduler import processar_resposta
                        processar_resposta(int(q['id']), bool(acertou))
                        conn.close()
                        
                        st.session_state.prova_respondido = True
                        st.session_state.prova_acertou = acertou
                        st.session_state.prova_chat_history = []
                        salvar_estado_simulado()
                        st.rerun()
                else:
                    acertou = st.session_state.prova_acertou
                    if acertou:
                        st.success(f"Resposta Correta! (+{peso} pontos)")
                    else:
                        st.error("Você errou.")
                        
                    col_next1, col_next2, col_next3 = st.columns([4, 4, 2])
                    with col_next1:
                        btn_next = st.button("Próxima Questão", key=f"btn_next_{idx}")
                    with col_next2:
                        btn_mentoria = False
                        if not st.session_state.get("prova_chat_history"):
                            btn_mentoria = st.button("Mentoria (Explicar Resposta)", key=f"btn_prova_analisar_{idx}")
                    with col_next3:
                        btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_depois_prova_{idx}")
                        
                    if btn_mentoria and not st.session_state.get("prova_chat_history"):
                        from backend.llm import explicar_erro
                        gab = str(q.get('gabarito', '')).strip().upper()
                        texto_correta = f"{gab}) {opcoes.get(gab, 'N/A')}" if gab in opcoes else "N/A"
                        texto_marcada = f"{resposta_usuario}) {opcoes.get(resposta_usuario, 'N/A')}" if resposta_usuario in opcoes else "N/A"
                        st.markdown("### 🧠 Análise do Tutor")
                        with st.chat_message("assistant"):
                            gerador = explicar_erro(
                                q['enunciado'], 
                                texto_correta, 
                                texto_marcada, 
                                st.session_state.prova_acertou,
                                historico=[],
                                stream=True
                            )
                            with st.spinner("Tutor IA pensando..."):
                                resposta = st.write_stream(gerador)
                            st.session_state.prova_chat_history = [{"role": "assistant", "content": resposta}]
                        salvar_estado_simulado()
                    elif st.session_state.get("prova_chat_history"):
                        st.markdown("### 🧠 Análise do Tutor")
                        for msg in st.session_state.prova_chat_history:
                            st.chat_message(msg["role"]).write(msg["content"])
                            
                    if st.session_state.get("prova_chat_history"):
                        if nova_duvida := st.chat_input("Ficou com alguma dúvida? Pergunte aqui...", key=f"chat_depois_{idx}"):
                            st.chat_message("user").write(nova_duvida)
                            st.session_state.prova_chat_history.append({"role": "user", "content": nova_duvida})
                            from backend.llm import explicar_erro
                            gab = str(q.get('gabarito', '')).strip().upper()
                            texto_correta = f"{gab}) {opcoes.get(gab, 'N/A')}" if gab in opcoes else "N/A"
                            texto_marcada = f"{resposta_usuario}) {opcoes.get(resposta_usuario, 'N/A')}" if resposta_usuario in opcoes else "N/A"
                            with st.chat_message("assistant"):
                                gerador = explicar_erro(
                                    q['enunciado'], 
                                    texto_correta, 
                                    texto_marcada, 
                                    st.session_state.prova_acertou,
                                    historico=st.session_state.prova_chat_history[:-1],
                                    stream=True
                                )
                                with st.spinner("Tutor IA pensando..."):
                                    resposta = st.write_stream(gerador)
                                st.session_state.prova_chat_history.append({"role": "assistant", "content": resposta})
                            salvar_estado_simulado()
                        
                    if btn_next:
                        st.session_state.questao_idx += 1
                        st.session_state.prova_respondido = False
                        st.session_state.prova_chat_history = []
                        salvar_estado_simulado()
                        st.rerun()
                        
                    if btn_rem:
                        conn = sqlite3.connect(DB_PATH, timeout=15)
                        conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (int(q['id']),))
                        conn.commit()
                        
                        # Revert the score if the user answered correctly
                        if st.session_state.get("prova_acertou"):
                            if is_basic:
                                st.session_state.prova_score_basic -= 1.0
                            else:
                                st.session_state.prova_score_esp -= 2.5
                                
                        ids_atuais = tuple(st.session_state.df_prova['id'].tolist())
                        if len(ids_atuais) == 1:
                            ids_sql = f"({ids_atuais[0]})"
                        else:
                            ids_sql = str(ids_atuais)
                        
                        df_nova = pd.read_sql_query(f'''
                            SELECT q.*, s.nome as subgrupo_nome, g.nome as grupo_nome 
                            FROM questoes q
                            JOIN subgrupos s ON q.subgrupo_id = s.id
                            JOIN grupos g ON s.grupo_id = g.id
                            WHERE g.nome = ? AND (q.valida IS NULL OR q.valida != -1)
                            AND q.id NOT IN {ids_sql}
                            ORDER BY RANDOM() LIMIT 1
                        ''', conn, params=(q['grupo_nome'],))
                        
                        if not df_nova.empty:
                            st.session_state.df_prova.iloc[idx] = df_nova.iloc[0]
                            st.warning("Questão invalidada! Substituída por uma nova da mesma disciplina.")
                        else:
                            st.session_state.questao_idx += 1
                            st.warning("Questão invalidada! Sem substitutas disponíveis na disciplina. Avançando...")
                            
                        conn.close()
                        st.session_state.prova_respondido = False
                        st.session_state.prova_acertou = False
                        st.session_state.prova_chat_history = []
                        salvar_estado_simulado()
                        st.rerun()
            else:
                st.success("🎉 Você concluiu todas as questões da prova!")
                
                score_basic = st.session_state.get('prova_score_basic', 0.0)
                score_esp = st.session_state.get('prova_score_esp', 0.0)
                score_total = score_basic + score_esp
                
                if st.session_state.get('prova_start_time'):
                    total_elapsed = int(time.time() - st.session_state.prova_start_time)
                    td_total = datetime.timedelta(seconds=total_elapsed)
                    st.info(f"**Tempo total de realização:** `{td_total}`")
                    
                if os.path.exists(STATE_FILE):
                    if st.session_state.get('prova_start_time') and st.session_state.get('df_prova') is not None and len(st.session_state.df_prova) > 30:
                        # Salvar apenas se for um simulado de verdade (maior q 30 questoes) para nao flodar o grafico com testes
                        conn_sim = sqlite3.connect(DB_PATH, timeout=15)
                        conn_sim.execute("INSERT INTO historico_simulados (tempo_segundos, pontuacao_total) VALUES (?, ?)", (total_elapsed, score_total))
                        conn_sim.commit()
                        conn_sim.close()
                    os.remove(STATE_FILE)
                
                # Exibe a pontuação final apenas se for simulado ou se tiver respondido algo
                score_basic = st.session_state.get('prova_score_basic', 0.0)
                score_esp = st.session_state.get('prova_score_esp', 0.0)
                score_total = score_basic + score_esp
                
                st.markdown("### 🏆 Resultado Final do Simulado")
                colA, colB, colC = st.columns(3)
                colA.metric("Conhecimentos Básicos", f"{score_basic} / 40.0 pts")
                colB.metric("Conhecimentos Específicos", f"{score_esp} / 75.0 pts")
                colC.metric("PONTUAÇÃO TOTAL", f"{score_total} / 115.0 pts")
                
                st.progress(score_total / 115.0)
                
                if st.button("Fazer Nova Prova"):
                    st.session_state.prova_em_andamento = False
                    st.session_state.df_prova = None
                    st.rerun()
        else:
            st.warning("Não há questões suficientes no banco para este modo. Use a aba Hoje para gerar mais.")
    
    
