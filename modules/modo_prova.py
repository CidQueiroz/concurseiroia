import streamlit as st
import pandas as pd
import json
import time
import os
import datetime
import random
from backend.db import get_supabase

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        st.error("Você precisa estar logado para acessar o Modo Prova.")
        return
        
    is_admin = (user.email == "cydy.potter@gmail.com")

    st.header("Modo Prova 📝")
    
    resp_user = supabase.table("aprendizado_item").select("item_id").eq("user_id", user.id).limit(1).execute().data
    if not resp_user or len(resp_user) == 0:
        st.warning("⚠️ Você precisa vincular matérias ao seu perfil antes de usar o Modo Prova.")
        st.info("Acesse a aba **Cronograma** no menu lateral para escolher suas matérias.")
        return
    
    # Em vez de salvar arquivo local, usaremos state em memória ou um state file por user_id. 
    # Para o MVP do Supabase, session_state é suficiente, mas se o arquivo for necessário:
    STATE_FILE = f"data/bancos/simulado_estado_{user.id}.json"
    os.makedirs("data/bancos", exist_ok=True)
    
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
            
    modo_prova = "Prova por Tema"
    
    # Carregar apenas Grupos vinculados ao usuário
    resp_a = supabase.table("aprendizado_item").select("itens_estudo!inner(subgrupos!inner(grupos!inner(nome)))").eq("user_id", user.id).execute().data
    grupos_atuais = set()
    for a in resp_a:
        if a.get('itens_estudo') and a['itens_estudo'].get('subgrupos'):
            grupos_atuais.add(a['itens_estudo']['subgrupos']['grupos']['nome'])
            
    df_temas = pd.DataFrame([{"nome": g} for g in sorted(list(grupos_atuais))])
    tema_selecionado = None
    subgrupos_selecionados = []
    
    if modo_prova == "Prova por Tema":
        if not df_temas.empty:
            tema_selecionado = st.selectbox("Selecione o Tema:", df_temas['nome'].tolist())
            
            # Carrega subgrupos dinamicamente do BD
            resp_sub = supabase.table("subgrupos").select("nome, grupos!inner(nome)").eq("grupos.nome", tema_selecionado).execute()
            subgrupos_opcoes = [s["nome"] for s in resp_sub.data]
            
            itens_selecionados = []
            if subgrupos_opcoes:
                subgrupos_selecionados = st.multiselect("Selecione os Subgrupos (Deixe vazio para ver todos):", subgrupos_opcoes)
                if subgrupos_selecionados:
                    resp_itens = supabase.table("itens_estudo").select("nome, subgrupos!inner(nome)").in_("subgrupos.nome", subgrupos_selecionados).execute()
                    itens_opcoes = [i["nome"] for i in resp_itens.data]
                    if itens_opcoes:
                        itens_selecionados = st.multiselect("Selecione os Itens de Estudo (Deixe vazio para ver todos):", itens_opcoes)
        else:
            st.warning("Nenhuma questão no banco de dados.")
            
    ineditas_apenas = st.checkbox("Somente questões inéditas (ainda não respondidas)", value=True, help="Desmarque para permitir questões que você já resolveu.")
    
    if modo_prova == "Prova por Tema" and tema_selecionado:
        st.markdown("---")
        st.markdown("**Gerador IA** (Opcional): Se o banco local estiver vazio ou se quiser testar conhecimentos novos.")
        if st.button("✨ Gerar Questão Inédita com IA para os temas selecionados", key="btn_gerar_ia_prova"):
            with st.spinner(f"Gerando questão inédita de {tema_selecionado}..."):
                from backend.llm import gerar_questao_inedita
                sub_escolhido = random.choice(subgrupos_selecionados) if subgrupos_selecionados else "Assuntos Gerais"
                nova_q = gerar_questao_inedita(tema_selecionado, sub_escolhido)
                if nova_q:
                    from modules.gerenciador import get_subgrupo_id
                    s_id = get_subgrupo_id(tema_selecionado, sub_escolhido)
                    
                    alts = nova_q.get('alternativas', {})
                    if not alts:
                        alts = {"A": nova_q.get('a', 'N/A'), "B": nova_q.get('b', 'N/A'), "C": nova_q.get('c', 'N/A'), "D": nova_q.get('d', 'N/A'), "E": nova_q.get('e', 'N/A')}
                        
                    nova_questao = {
                        "item_id": int(s_id),
                        "banca": "IA-Gerada",
                        "enunciado": nova_q.get('enunciado', ''),
                        "alternativa_a": alts.get("A", "N/A"),
                        "alternativa_b": alts.get("B", "N/A"),
                        "alternativa_c": alts.get("C", "N/A"),
                        "alternativa_d": alts.get("D", "N/A"),
                        "alternativa_e": alts.get("E", "N/A"),
                        "gabarito": nova_q.get('gabarito', 'A'),
                        "valida": 1
                    }
                    supabase.table("questoes").insert(nova_questao).execute()
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
            
    def carregar_questoes_supabase(tema=None, ineditas=True, subs=None, itens_filtro=None):
        query = supabase.table("questoes").select("*, itens_estudo!inner(nome, subgrupos!inner(nome, grupos!inner(nome)))")
        if tema:
            query = query.eq("itens_estudo.subgrupos.grupos.nome", tema)
        
        # O supabase rest client não tem limit() sem order que traga as mais aleatórias de forma barata, então puxamos as válidas
        # limit(1000)
        data = query.execute().data
        
        if ineditas:
            # Puxar IDs respondidos por este usuario
            resp_historico = supabase.table("respostas").select("questao_id").eq("user_id", user.id).execute()
            respondidas = set([r["questao_id"] for r in resp_historico.data])
            data = [q for q in data if q["id"] not in respondidas]
            
        # Filtrar as invalidadas
        data = [q for q in data if q.get("valida", 1) >= 0]
            
        # Flatten para pandas
        for q in data:
            q['item_nome'] = q['itens_estudo']['nome']
            q['subgrupo_nome'] = q['itens_estudo']['subgrupos']['nome']
            q['grupo_nome'] = q['itens_estudo']['subgrupos']['grupos']['nome']
            del q['itens_estudo']
            
        df = pd.DataFrame(data)
        if not df.empty:
            if subs:
                df = df[df['subgrupo_nome'].isin(subs)]
            if itens_filtro:
                df = df[df['item_nome'].isin(itens_filtro)]
            
        return df

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
            df_questoes = carregar_questoes_supabase(tema_selecionado, ineditas_apenas, subgrupos_selecionados, itens_selecionados)
            if not df_questoes.empty:
                df_questoes = df_questoes.drop_duplicates(subset=['enunciado'])
                st.session_state.df_prova = df_questoes.sample(frac=1).reset_index(drop=True).head(200) # limite de 200 pro front
            else:
                st.session_state.df_prova = pd.DataFrame()
                    
        salvar_estado_simulado()
            
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
                is_basic = str(q.get('grupo_nome', '')).strip().upper() in dist_basics
                peso = 1.0
                
                if st.session_state.get('prova_start_time'):
                    elapsed = int(time.time() - st.session_state.prova_start_time)
                    td = datetime.timedelta(seconds=elapsed)
                    st.info(f"**⏱️ Tempo de Prova:** `{td}` *(atualizado a cada interação)*")
                    
                st.markdown("---")
                banca_str = q.get('banca', 'N/A')
                ano_raw = q.get('ano', 'N/A')
                if pd.isna(ano_raw) or ano_raw == 'N/A':
                    ano_str = 'N/A'
                else:
                    ano_str = str(int(ano_raw)) if isinstance(ano_raw, (float, int)) else str(ano_raw)
                st.caption(f"Questão {idx + 1} de {len(df_prova)} | Tema: {q.get('grupo_nome', '')} | Banca: {banca_str} | Ano: {ano_str} | Peso: {peso}")
                st.markdown(f"**{q.get('enunciado', '')}**")
                
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
                        btn_remover = False
                        if is_admin:
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
                        supabase.table("questoes").update({"valida": -1}).eq("id", int(q['id'])).execute()
                        st.session_state.questao_idx += 1
                        st.warning("Questão invalidada! Avançando para a próxima...")
                        st.session_state.prova_chat_history = []
                        salvar_estado_simulado()
                        st.rerun()
    
                    if btn_responder:
                        gab_correto = str(q.get('gabarito', '')).strip().upper()
                        if gab_correto in ['N/A', 'NONE', '']:
                            from backend.llm import resolver_gabarito_ia
                            with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                novo_gab = resolver_gabarito_ia(q['enunciado'], opcoes)
                                supabase.table("questoes").update({"gabarito": novo_gab}).eq("id", int(q['id'])).execute()
                                st.session_state.df_prova.at[idx, 'gabarito'] = novo_gab
                                gab_correto = novo_gab
    
                        acertou = (str(resposta_usuario).strip().upper() == gab_correto)
                        
                        if acertou:
                            if is_basic:
                                st.session_state.prova_score_basic += 1.0
                            else:
                                st.session_state.prova_score_esp += 1.0
                        
                        supabase.table("questoes").update({"valida": 1}).eq("id", int(q['id'])).execute()
                        supabase.table("respostas").insert({
                            "user_id": user.id,
                            "questao_id": int(q['id']),
                            "acertou": bool(acertou),
                            "tempo_segundos": 0
                        }).execute()
                        
                        # Atualizar stats no banco (pode usar scheduler, mas via supabase python)
                        # No MVP manteremos simples
                        
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
                        
                    col_next1, col_next2, col_next3, col_next4 = st.columns([3, 3, 3, 2])
                    with col_next1:
                        btn_next = st.button("Próxima Questão", key=f"btn_next_{idx}")
                    with col_next2:
                        btn_mentoria = False
                        if not st.session_state.get("prova_chat_history"):
                            btn_mentoria = st.button("Mentoria", key=f"btn_prova_analisar_{idx}")
                    with col_next3:
                        btn_raiox = False
                        if not acertou and not st.session_state.get("prova_chat_history"):
                            btn_raiox = st.button("🧠 Raio-X da Banca", key=f"btn_raiox_prova_{idx}")
                    with col_next4:
                        btn_rem = False
                        if is_admin:
                            btn_rem = st.button("🗑️ Remover", key=f"btn_rem_depois_prova_{idx}")
                        
                    if btn_raiox and not st.session_state.get("prova_chat_history"):
                        from backend.llm import analisar_banca_ia
                        b = q.get('banca', 'N/A')
                        if not b or b == 'N/A' or b == 'NONE': b = "Não Especificada"
                        st.markdown("### 🧠 Raio-X da Banca")
                        with st.spinner("Desconstruindo a armadilha..."):
                            analise_banca = analisar_banca_ia(b, q.get('enunciado', ''), opcoes, q.get('gabarito', 'A'))
                            st.error(analise_banca)
                            st.session_state.prova_chat_history = [{"role": "assistant", "content": analise_banca}]
                        salvar_estado_simulado()
                    elif btn_mentoria and not st.session_state.get("prova_chat_history"):
                        from backend.llm import explicar_erro
                        gab = str(q.get('gabarito', '')).strip().upper()
                        texto_correta = f"{gab}) {opcoes.get(gab, 'N/A')}" if gab in opcoes else "N/A"
                        texto_marcada = f"{resposta_usuario}) {opcoes.get(resposta_usuario, 'N/A')}" if resposta_usuario in opcoes else "N/A"
                        st.markdown("### 🧠 Análise do Tutor")
                        with st.chat_message("assistant"):
                            gerador = explicar_erro(
                                q.get('enunciado', ''), 
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
                                    q.get('enunciado', ''), 
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
                        supabase.table("questoes").update({"valida": -1}).eq("id", int(q['id'])).execute()
                        if st.session_state.get("prova_acertou"):
                            if is_basic:
                                st.session_state.prova_score_basic -= 1.0
                            else:
                                st.session_state.prova_score_esp -= 1.0
                        st.session_state.questao_idx += 1
                        st.session_state.prova_respondido = False
                        st.session_state.prova_acertou = False
                        st.session_state.prova_chat_history = []
                        st.warning("Questão invalidada! Avançando...")
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
                        supabase.table("historico_simulados").insert({
                            "user_id": user.id,
                            "tempo_segundos": total_elapsed,
                            "pontuacao_total": score_total
                        }).execute()
                    os.remove(STATE_FILE)
                
                st.markdown("### 🏆 Resultado Final do Simulado")
                colA, colB, colC = st.columns(3)
                colA.metric("Conhecimentos Básicos (Pontos)", f"{score_basic}")
                colB.metric("Conhecimentos Específicos (Pontos)", f"{score_esp}")
                colC.metric("PONTUAÇÃO TOTAL", f"{score_total}")
                
                if st.button("Fazer Nova Prova"):
                    st.session_state.prova_em_andamento = False
                    st.session_state.df_prova = None
                    st.rerun()
        else:
            st.warning("Não há questões suficientes no banco para este modo. Use a aba Hoje para gerar mais.")
