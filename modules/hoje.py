import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime

def render(DB_PATH):
    st.header("Plano de Operações Diárias (POD) 🎯")
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown("Bem-vindo ao AMV 2.0 (Motor Inteligente de Aprendizagem). O seu cronograma diário é montado on-the-fly pela Inteligência Artificial usando Spaced Repetition e Learning Analytics.")
    with col2:
        if st.button("🔄 Atualizar Plano"):
            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
            st.rerun()
            
    import json
    from backend.scheduler import montar_plano_diario, gravar_resumo, get_resumo, processar_resposta
    
    if "plano_diario" not in st.session_state:
        st.session_state["plano_diario"] = montar_plano_diario()
        
    lista_novos, lista_revs = st.session_state["plano_diario"]
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # BLOCO 1 E 2: CONTEÚDO NOVO E QUESTÕES
    # ---------------------------------------------------------
    st.subheader("Bloco 1 e 2: Apreensão de Conteúdo Novo")
    if not lista_novos:
        st.success("Não há conteúdos novos agendados para hoje. Parabéns!")
    
    for item in lista_novos:
        grupo = item['grupo_nome']
        subgrupo = item['subgrupo_nome']
        sid = item['subgrupo_id']
        idx = f"novo_{sid}"
        
        with st.expander(f"🆕 [NOVO] {grupo} - {subgrupo}", expanded=False):
            st.markdown(f"**Status Atual:** {item['status']}")
            
            k_fase = f"fase_{idx}"
            if k_fase not in st.session_state:
                st.session_state[k_fase] = "teoria"
            
            # --- FASE TEORIA ---
            if st.session_state[k_fase] == "teoria":
                conn_estudo = sqlite3.connect("data/bancos/conteudo_estudo.sqlite")
                cur_estudo = conn_estudo.cursor()
                try:
                    cur_estudo.execute("SELECT texto FROM conteudos WHERE grupo = ? AND subgrupo = ?", (grupo, subgrupo))
                    res = cur_estudo.fetchone()
                except:
                    res = None
                conn_estudo.close()
                
                if res and res[0]:
                    st.markdown(res[0])
                else:
                    st.info("Texto base não encontrado. Buscando via IA...")
                    if st.button("Gerar Resumo por IA", key=f"btn_gerar_teoria_{idx}"):
                        with st.spinner("Gerando conteúdo..."):
                            from backend.llm import gerar_conteudo_estudo
                            texto_gerado = gerar_conteudo_estudo(grupo, subgrupo)
                            conn_estudo2 = sqlite3.connect("data/bancos/conteudo_estudo.sqlite")
                            conn_estudo2.execute("CREATE TABLE IF NOT EXISTS conteudos (id INTEGER PRIMARY KEY, grupo TEXT, subgrupo TEXT, texto TEXT)")
                            conn_estudo2.execute("INSERT INTO conteudos (grupo, subgrupo, texto) VALUES (?, ?, ?)", (grupo, subgrupo, texto_gerado))
                            conn_estudo2.commit()
                            conn_estudo2.close()
                            st.rerun()
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Concluir Leitura (Ir para Active Recall)", key=f"btn_ler_{idx}"):
                        st.session_state[k_fase] = "recall"
                        st.rerun()
                with col2:
                    if st.button("🚫 Ignorar Tópico (Não cairá na prova)", key=f"btn_ignorar_{idx}"):
                        conn = sqlite3.connect(DB_PATH, timeout=15)
                        conn.execute("UPDATE aprendizado_subgrupo SET status = 'IGNORADO' WHERE subgrupo_id = ?", (sid,))
                        conn.commit()
                        conn.close()
                        if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
                        st.rerun()
            
            # --- FASE ACTIVE RECALL ---
            elif st.session_state[k_fase] == "recall":
                st.warning("🧠 **Active Recall**: Sem olhar o resumo, tente lembrar o que acabou de ler.")
                recall_text = st.text_area("Escreva tudo que você lembra deste conteúdo:", key=f"txt_recall_{idx}", height=150)
                if st.button("Salvar e Avançar", key=f"btn_recall_{idx}"):
                    st.session_state[k_fase] = "bullets"
                    st.rerun()
                    
            # --- FASE 5 BULLETS ---
            elif st.session_state[k_fase] == "bullets":
                st.info("📝 **Mini Resumo**: Resuma este assunto em no máximo cinco bullets para as futuras revisões.")
                bullets = st.text_area("Escreva seus bullets (usaremos nas revisões espaçadas):", key=f"txt_bullets_{idx}", height=100)
                if st.button("Gravar Resumo e Ir para Questões", key=f"btn_bullets_{idx}"):
                    gravar_resumo(sid, bullets)
                    st.session_state[k_fase] = "questoes"
                    st.success("Resumo gravado com sucesso!")
                    st.rerun()
                    
            # --- FASE QUESTÕES ---
            elif st.session_state[k_fase] == "questoes":
                st.success("Tudo pronto! Resolva as questões abaixo.")
                k_q = f"q_{idx}"
                k_resp = f"resp_{idx}"
                
                if k_q not in st.session_state:
                    conn = sqlite3.connect(DB_PATH, timeout=15)
                    df_q = pd.read_sql_query(f"SELECT * FROM questoes WHERE subgrupo_id = {sid} AND (valida IS NULL OR valida != 0) AND id NOT IN (SELECT questao_id FROM respostas) ORDER BY RANDOM() LIMIT 1", conn)
                    conn.close()
                    if not df_q.empty:
                        row_q = df_q.iloc[0]
                        alt_dict = {
                            "A": row_q.get('alternativa_a', 'N/A'),
                            "B": row_q.get('alternativa_b', 'N/A'),
                            "C": row_q.get('alternativa_c', 'N/A'),
                            "D": row_q.get('alternativa_d', 'N/A'),
                            "E": row_q.get('alternativa_e', 'N/A')
                        }
                        q_json = {
                            "id": int(row_q['id']),
                            "enunciado": row_q['enunciado'],
                            "alternativas": alt_dict,
                            "gabarito": row_q.get('gabarito', row_q.get('correta', 'A')),
                            "banca": row_q.get('banca', 'N/A')
                        }
                        st.session_state[k_q] = q_json
                    else:
                        st.session_state[k_q] = None
                        
                q_json = st.session_state[k_q]
                if q_json:
                    st.markdown(f"**Questão:** {q_json.get('enunciado', '')}")
                    opts = q_json.get('alternativas', {})
                    opt_list = []
                    for k, v in opts.items():
                        opt_list.append(f"{k}) {v}")
                    
                    choice = st.radio("Selecione a resposta:", opt_list, key=f"radio_{idx}", index=None)
                    
                    if not st.session_state.get(k_resp):
                        col1, col2, col3 = st.columns([4, 4, 2])
                        with col1:
                            btn_resp = st.button("Responder", key=f"btn_resp_{idx}")
                        with col2:
                            btn_mentoria_antes = st.button("Mentoria (Ajude-me a pensar)", key=f"btn_mentoria_antes_{idx}")
                        with col3:
                            btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_antes_{idx}")
                            
                        if btn_mentoria_antes:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA pensando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, choice[0] if choice else None))
                        
                        if btn_rem:
                            conn = sqlite3.connect(DB_PATH, timeout=15)
                            conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (q_json['id'],))
                            conn.commit()
                            conn.close()
                            del st.session_state[k_q]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                            
                        if q_json.get('gabarito') in ['N/A', 'None'] or not q_json.get('gabarito'):
                            st.info("⚠️ O gabarito desta questão não pôde ser lido do PDF. Quando você responder, a IA deduzirá a alternativa correta e a salvará no banco permanentemente.")
    
                        if btn_resp:
                            if choice:
                                if q_json.get('gabarito') in ['N/A', 'None'] or not q_json.get('gabarito'):
                                    from backend.llm import resolver_gabarito_ia
                                    with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                        novo_gab = resolver_gabarito_ia(q_json['enunciado'], q_json['alternativas'])
                                        conn = sqlite3.connect(DB_PATH, timeout=15)
                                        conn.execute("UPDATE questoes SET gabarito = ? WHERE id = ?", (novo_gab, q_json['id']))
                                        conn.commit()
                                        conn.close()
                                        q_json['gabarito'] = novo_gab
                                        st.session_state[k_q] = q_json
    
                                l_choice = choice[0]
                                acertou = (str(l_choice).strip().upper() == str(q_json.get('gabarito', '')).strip().upper())
                                
                                # Grava no DB de respostas legacy
                                conn = sqlite3.connect(DB_PATH, timeout=15)
                                conn.execute("UPDATE questoes SET valida = 1 WHERE id = ?", (q_json['id'],))
                                conn.execute("INSERT INTO respostas (questao_id, acertou, tempo_segundos) VALUES (?, ?, ?)", (q_json['id'], bool(acertou), 0))
                                conn.commit()
                                conn.close()
                                
                                # Processa na engine AMV 2.0
                                processar_resposta(q_json['id'], acertou)
                                
                                st.session_state[k_resp] = {"acertou": acertou, "gabarito": q_json['gabarito'], "letra": l_choice}
                                st.rerun()
                            else:
                                st.warning("Selecione uma alternativa.")
                    else:
                        r = st.session_state[k_resp]
                        if r['acertou']:
                            st.success("Resposta Correta! Muito bem.")
                        else:
                            st.error("Você errou.")
                        
                        col_d1, col_d2, col_d3 = st.columns([4, 4, 2])
                        with col_d1:
                            btn_next = st.button("Avançar para o Próximo Tópico", key=f"btn_next_{idx}")
                        with col_d2:
                            btn_mentoria = st.button("Mentoria (Ajude-me a pensar)", key=f"btn_analise_{idx}")
                        with col_d3:
                            btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_depois_{idx}")
                            
                        if btn_mentoria:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA analisando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, r['letra']))
                                
                        if btn_next:
                            del st.session_state[k_q]
                            del st.session_state[k_resp]
                            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
                            st.rerun()
                            
                        if btn_rem:
                            conn = sqlite3.connect(DB_PATH, timeout=15)
                            conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (q_json['id'],))
                            conn.commit()
                            conn.close()
                            del st.session_state[k_q]
                            del st.session_state[k_resp]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                else:
                    st.info("O banco local para este tema esgotou. Gerar uma inédita?")
                    if st.button("Gerar Questão Inédita (IA)", key=f"btn_gerar_{idx}"):
                        with st.spinner("Criando..."):
                            from backend.llm import gerar_questao_inedita
                            nova_q = gerar_questao_inedita(grupo, subgrupo)
                            if nova_q:
                                conn = sqlite3.connect(DB_PATH, timeout=15)
                                cur = conn.cursor()
                                alts = nova_q.get('alternativas', {})
                                cur.execute("INSERT INTO questoes (subgrupo_id, banca, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito, valida) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", 
                                            (sid, "IA-Gerada", nova_q.get('enunciado', ''), alts.get("A", "N/A"), alts.get("B", "N/A"), alts.get("C", "N/A"), alts.get("D", "N/A"), alts.get("E", "N/A"), nova_q.get('gabarito', 'A')))
                                conn.commit()
                                conn.close()
                                if k_q in st.session_state: del st.session_state[k_q]
                                st.rerun()
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # BLOCO 3: REVISÕES ESPAÇADAS
    # ---------------------------------------------------------
    st.subheader("Bloco 3: Revisões Inteligentes (Spaced Repetition)")
    if not lista_revs:
        st.success("Fila de revisões limpa! Você está em dia.")
        
    for item in lista_revs:
        grupo = item['grupo_nome']
        subgrupo = item['subgrupo_nome']
        sid = item['subgrupo_id']
        idx = f"rev_{sid}"
        
        with st.expander(f"🔄 [REVISAR] {grupo} - {subgrupo}", expanded=False):
            st.markdown(f"**Status:** {item['status']} | **Prioridade:** {item['prioridade']:.1f} | **Nível de Domínio:** {item['nivel_dominio']}%")
            
            k_rev_fase = f"rev_fase_{idx}"
            if k_rev_fase not in st.session_state:
                st.session_state[k_rev_fase] = "resumo"
                
            if st.session_state[k_rev_fase] == "resumo":
                resumo = get_resumo(sid)
                if resumo:
                    st.info("**Seus Bullets de Revisão:**\n" + resumo)
                else:
                    st.warning("Você não gravou bullets para este tema. Tente recordar a teoria geral.")
                
                st.markdown("Você lembra deste assunto?")
                if st.button("Lembro! (Ir para Questões)", key=f"btn_lembro_{idx}"):
                    st.session_state[k_rev_fase] = "questoes"
                    st.rerun()
                if st.button("Não lembro (Mostrar Teoria Completa)", key=f"btn_naolembro_{idx}"):
                    st.session_state[k_rev_fase] = "teoria"
                    st.rerun()
                    
            elif st.session_state[k_rev_fase] == "teoria":
                conn_estudo = sqlite3.connect("data/bancos/conteudo_estudo.sqlite")
                cur_estudo = conn_estudo.cursor()
                try:
                    cur_estudo.execute("SELECT texto FROM conteudos WHERE grupo = ? AND subgrupo = ?", (grupo, subgrupo))
                    res = cur_estudo.fetchone()
                except:
                    res = None
                conn_estudo.close()
                if res and res[0]:
                    st.markdown(res[0])
                if st.button("Concluir Revisão Teórica", key=f"btn_fim_teoria_{idx}"):
                    st.session_state[k_rev_fase] = "questoes"
                    st.rerun()
                    
            elif st.session_state[k_rev_fase] == "questoes":
                st.success("Tudo pronto! Resolva as questões abaixo para validar a revisão.")
                k_q = f"q_{idx}"
                k_resp = f"resp_{idx}"
                
                if k_q not in st.session_state:
                    conn = sqlite3.connect(DB_PATH, timeout=15)
                    df_q = pd.read_sql_query(f"SELECT * FROM questoes WHERE subgrupo_id = {sid} AND (valida IS NULL OR valida != 0) AND id NOT IN (SELECT questao_id FROM respostas) ORDER BY RANDOM() LIMIT 1", conn)
                    conn.close()
                    if not df_q.empty:
                        row_q = df_q.iloc[0]
                        alt_dict = {
                            "A": row_q.get('alternativa_a', 'N/A'),
                            "B": row_q.get('alternativa_b', 'N/A'),
                            "C": row_q.get('alternativa_c', 'N/A'),
                            "D": row_q.get('alternativa_d', 'N/A'),
                            "E": row_q.get('alternativa_e', 'N/A')
                        }
                        q_json = {
                            "id": int(row_q['id']),
                            "enunciado": row_q['enunciado'],
                            "alternativas": alt_dict,
                            "gabarito": row_q.get('gabarito', row_q.get('correta', 'A')),
                            "banca": row_q.get('banca', 'N/A')
                        }
                        st.session_state[k_q] = q_json
                    else:
                        st.session_state[k_q] = None
                        
                q_json = st.session_state[k_q]
                if q_json:
                    st.markdown(f"**Questão:** {q_json.get('enunciado', '')}")
                    opts = q_json.get('alternativas', {})
                    opt_list = []
                    for k, v in opts.items():
                        opt_list.append(f"{k}) {v}")
                    
                    choice = st.radio("Selecione a resposta:", opt_list, key=f"radio_{idx}", index=None)
                    
                    if not st.session_state.get(k_resp):
                        col1, col2, col3 = st.columns([4, 4, 2])
                        with col1:
                            btn_resp = st.button("Responder", key=f"btn_resp_{idx}")
                        with col2:
                            btn_mentoria_antes = st.button("Mentoria (Ajude-me a pensar)", key=f"btn_mentoria_antes_{idx}")
                        with col3:
                            btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_antes_{idx}")
                            
                        if btn_mentoria_antes:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA pensando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, choice[0] if choice else None))
                        
                        if btn_rem:
                            conn = sqlite3.connect(DB_PATH, timeout=15)
                            conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (q_json['id'],))
                            conn.commit()
                            conn.close()
                            del st.session_state[k_q]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                            
                        if q_json.get('gabarito') == 'N/A' or not q_json.get('gabarito'):
                            st.info("⚠️ O gabarito desta questão não pôde ser lido do PDF. Quando você responder, a IA deduzirá a alternativa correta e a salvará no banco permanentemente.")
    
                        if btn_resp:
                            if choice:
                                if q_json.get('gabarito') == 'N/A' or not q_json.get('gabarito'):
                                    from backend.llm import resolver_gabarito_ia
                                    with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                        novo_gab = resolver_gabarito_ia(q_json['enunciado'], q_json['alternativas'])
                                        conn = sqlite3.connect(DB_PATH, timeout=15)
                                        conn.execute("UPDATE questoes SET gabarito = ? WHERE id = ?", (novo_gab, q_json['id']))
                                        conn.commit()
                                        conn.close()
                                        q_json['gabarito'] = novo_gab
                                        st.session_state[k_q] = q_json
    
                                l_choice = choice[0]
                                acertou = (str(l_choice).strip().upper() == str(q_json.get('gabarito', '')).strip().upper())
                                
                                conn = sqlite3.connect(DB_PATH, timeout=15)
                                conn.execute("UPDATE questoes SET valida = 1 WHERE id = ?", (q_json['id'],))
                                conn.execute("INSERT INTO respostas (questao_id, acertou, tempo_segundos) VALUES (?, ?, ?)", (q_json['id'], bool(acertou), 0))
                                conn.commit()
                                conn.close()
                                
                                processar_resposta(q_json['id'], acertou)
                                
                                st.session_state[k_resp] = {"acertou": acertou, "gabarito": q_json['gabarito'], "letra": l_choice}
                                st.rerun()
                            else:
                                st.warning("Selecione uma alternativa.")
                    else:
                        r = st.session_state[k_resp]
                        if r['acertou']:
                            st.success("Resposta Correta! Revisão bem sucedida (algoritmo SRS atualizado).")
                        else:
                            st.error("Você errou. (O SRS reiniciará este tema para amanhã).")
                        
                        col_d1, col_d2, col_d3 = st.columns([4, 4, 2])
                        with col_d1:
                            btn_next = st.button("Avançar para o Próximo Tópico", key=f"btn_next_{idx}")
                        with col_d2:
                            btn_mentoria = st.button("Mentoria (Ajude-me a pensar)", key=f"btn_analise_{idx}")
                        with col_d3:
                            btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_depois_{idx}")
                            
                        if btn_mentoria:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA analisando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, r['letra']))
                                
                        if btn_next:
                            del st.session_state[k_q]
                            del st.session_state[k_resp]
                            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
                            st.rerun()
                            
                        if btn_rem:
                            conn = sqlite3.connect(DB_PATH, timeout=15)
                            conn.execute("UPDATE questoes SET valida = -1 WHERE id = ?", (q_json['id'],))
                            conn.commit()
                            conn.close()
                            del st.session_state[k_q]
                            del st.session_state[k_resp]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                else:
                    st.info("O banco local para este tema esgotou. Gerar uma inédita?")
                    if st.button("Gerar Questão Inédita (IA)", key=f"btn_gerar_{idx}"):
                        with st.spinner("Criando..."):
                            from backend.llm import gerar_questao_inedita
                            nova_q = gerar_questao_inedita(grupo, subgrupo)
                            if nova_q:
                                conn = sqlite3.connect(DB_PATH, timeout=15)
                                cur = conn.cursor()
                                alts = nova_q.get('alternativas', {})
                                cur.execute("INSERT INTO questoes (subgrupo_id, banca, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito, valida) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", 
                                            (sid, "IA-Gerada", nova_q.get('enunciado', ''), alts.get("A", "N/A"), alts.get("B", "N/A"), alts.get("C", "N/A"), alts.get("D", "N/A"), alts.get("E", "N/A"), nova_q.get('gabarito', 'A')))
                                conn.commit()
                                conn.close()
                                if k_q in st.session_state: del st.session_state[k_q]
                                st.rerun()
                                
    st.markdown("---")
    st.subheader("Bloco 4: Modo Prova")
    st.info("Após concluir a apreensão de novos temas e as revisões pendentes, vá para a aba **Modo Prova** para o treinamento misto de resistência!")
    
    
