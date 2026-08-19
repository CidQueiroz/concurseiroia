import streamlit as st
import pandas as pd
import json
import time
import os
import datetime
from backend.db import get_supabase

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        st.error("Você precisa estar logado para acessar seu cronograma.")
        return
        
    is_admin = (user.email == "cydy.potter@gmail.com")
        
    st.header("Plano de Operações Diárias (POD) 🎯")
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown("Bem-vindo ao AMV 2.0 (Motor Inteligente de Aprendizagem). O seu cronograma diário é montado on-the-fly pela Inteligência Artificial usando Spaced Repetition e Learning Analytics.")
    with col2:
        if st.button("🔄 Atualizar Plano"):
            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
            st.rerun()
            
    from backend.scheduler import montar_plano_diario, gravar_resumo, get_resumo, processar_resposta
    
    if "plano_diario" not in st.session_state:
        st.session_state["plano_diario"] = montar_plano_diario(user.id)
        
    lista_novos, lista_revs = st.session_state["plano_diario"]
    
    if not lista_novos and not lista_revs:
        resp = supabase.table("aprendizado_item").select("item_id").eq("user_id", user.id).limit(1).execute().data
        if not resp:
            st.warning("⚠️ Você ainda não vinculou nenhuma matéria ao seu perfil!")
            st.info("Vá até a aba **Cronograma** no menu lateral para selecionar os grupos de estudo (matérias) que deseja focar.")
            st.stop()
            
    st.markdown("---")
    
    # ---------------------------------------------------------
    # BLOCO 1 E 2: CONTEÚDO NOVO E QUESTÕES
    # ---------------------------------------------------------
    st.subheader("Bloco 1 e 2: Apreensão de Conteúdo Novo")
    if not lista_novos:
        st.success("Não há conteúdos novos agendados para hoje. Parabéns!")
    
    for item in lista_novos:
        grupo = item['grupo_nome']
        subgrupo = item['item_nome']
        iid = item['item_id']
        idx = f"novo_{iid}"
        
        with st.expander(f"🆕 [NOVO] {grupo} - {subgrupo}", expanded=False):
            st.markdown(f"**Status Atual:** {item['status']}")
            
            k_fase = f"fase_{idx}"
            if k_fase not in st.session_state:
                st.session_state[k_fase] = "teoria"
            
            # --- FASE TEORIA ---
            if st.session_state[k_fase] == "teoria":
                k_teoria = f"teoria_{grupo}_{subgrupo}"
                res = st.session_state.get(k_teoria)
                
                if res:
                    st.markdown(res)
                else:
                    st.info("Texto base não encontrado. Buscando via IA...")
                    if st.button("Gerar Resumo por IA", key=f"btn_gerar_teoria_{idx}"):
                        with st.spinner("Gerando conteúdo..."):
                            from backend.llm import gerar_conteudo_estudo
                            texto_gerado = gerar_conteudo_estudo(grupo, subgrupo)
                            st.session_state[k_teoria] = texto_gerado
                            st.rerun()
                
                if st.button("Concluir Leitura (Ir para Active Recall)", key=f"btn_ler_{idx}"):
                    st.session_state[k_fase] = "recall"
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
                    gravar_resumo(user.id, iid, bullets)
                    st.session_state[k_fase] = "questoes"
                    st.success("Resumo gravado com sucesso!")
                    st.rerun()
                    
            # --- FASE QUESTÕES ---
            elif st.session_state[k_fase] == "questoes":
                st.success("Tudo pronto! Resolva as questões abaixo.")
                k_q = f"q_{idx}"
                k_resp = f"resp_{idx}"
                
                if k_q not in st.session_state:
                    # Fetch answered qs
                    resp_hist = supabase.table("respostas").select("questao_id").eq("user_id", user.id).execute().data
                    answered = set(r["questao_id"] for r in resp_hist)
                    
                    # Fetch active qs
                    todas = supabase.table("questoes").select("*").eq("item_id", iid).gte("valida", 0).execute().data
                    validas = [q for q in todas if q["id"] not in answered]
                    
                    if validas:
                        import random
                        row_q = random.choice(validas)
                        alt_dict = {
                            "A": row_q.get('alternativa_a', 'N/A'),
                            "B": row_q.get('alternativa_b', 'N/A'),
                            "C": row_q.get('alternativa_c', 'N/A'),
                            "D": row_q.get('alternativa_d', 'N/A'),
                            "E": row_q.get('alternativa_e', 'N/A')
                        }
                        q_json = {
                            "id": int(row_q['id']),
                            "enunciado": row_q.get('enunciado', ''),
                            "alternativas": alt_dict,
                            "gabarito": row_q.get('gabarito', 'A'),
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
                            btn_rem = False
                            if is_admin:
                                btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_antes_{idx}")
                            
                        if btn_mentoria_antes:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA pensando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, choice[0] if choice else None))
                        
                        if btn_rem:
                            supabase.table("questoes").update({"valida": -1}).eq("id", q_json['id']).execute()
                            del st.session_state[k_q]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                            
                        gab_correto = str(q_json.get('gabarito', '')).strip().upper()
                        if gab_correto in ['N/A', 'NONE', '']:
                            st.info("⚠️ O gabarito desta questão não pôde ser lido do PDF. Quando você responder, a IA deduzirá a alternativa correta e a salvará no banco permanentemente.")
    
                        if btn_resp:
                            if choice:
                                if gab_correto in ['N/A', 'NONE', '']:
                                    from backend.llm import resolver_gabarito_ia
                                    with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                        novo_gab = resolver_gabarito_ia(q_json['enunciado'], q_json['alternativas'])
                                        supabase.table("questoes").update({"gabarito": novo_gab}).eq("id", q_json['id']).execute()
                                        q_json['gabarito'] = novo_gab
                                        gab_correto = novo_gab
                                        st.session_state[k_q] = q_json
    
                                l_choice = choice[0]
                                acertou = (str(l_choice).strip().upper() == gab_correto)
                                
                                supabase.table("questoes").update({"valida": 1}).eq("id", q_json['id']).execute()
                                supabase.table("respostas").insert({
                                    "user_id": user.id,
                                    "questao_id": q_json['id'],
                                    "acertou": bool(acertou),
                                    "tempo_segundos": 0
                                }).execute()
                                
                                processar_resposta(user.id, q_json['id'], acertou)
                                
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
                        
                        col_d1, col_d2, col_d3, col_d4 = st.columns([3, 3, 3, 2])
                        with col_d1:
                            btn_next = st.button("Avançar para o Próximo Tópico", key=f"btn_next_{idx}")
                        with col_d2:
                            btn_mentoria = st.button("Mentoria (Ajude-me)", key=f"btn_analise_{idx}")
                        with col_d3:
                            btn_raiox = False
                            if not r['acertou']:
                                btn_raiox = st.button("🧠 Raio-X da Banca", key=f"btn_raiox_{idx}")
                        with col_d4:
                            btn_rem = False
                            if is_admin:
                                btn_rem = st.button("🗑️ Remover", key=f"btn_rem_depois_{idx}")
                            
                        if btn_mentoria:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA analisando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, r['letra']))
                                
                        if btn_raiox:
                            from backend.llm import analisar_banca_ia
                            from backend.scheduler import agendar_revisao
                            with st.spinner("Desconstruindo a armadilha..."):
                                b = q_json.get('banca', 'N/A')
                                if not b or b == 'N/A' or b == 'NONE': b = "Não Especificada"
                                analise_banca = analisar_banca_ia(b, q_json['enunciado'], opts, q_json.get('gabarito', 'A'))
                                st.error(analise_banca)
                                # Aplica penalidade retroativa (sobrepondo a revisão leve que já havia sido agendada)
                                agendar_revisao(user.id, item['item_id'], acertou=False, contem_pegadinha=True)
                                
                        if btn_next:
                            del st.session_state[k_q]
                            del st.session_state[k_resp]
                            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
                            st.rerun()
                            
                        if btn_rem:
                            supabase.table("questoes").update({"valida": -1}).eq("id", q_json['id']).execute()
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
                                alts = nova_q.get('alternativas', {})
                                nova_questao = {
                                    "item_id": int(iid),
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
        subgrupo = item['item_nome']
        iid = item['item_id']
        idx = f"rev_{iid}"
        
        with st.expander(f"🔄 [REVISAR] {grupo} - {subgrupo}", expanded=False):
            st.markdown(f"**Status:** {item['status']} | **Prioridade:** {item.get('prioridade', 0):.1f} | **Nível de Domínio:** {item.get('nivel_dominio', 0)}%")
            
            k_rev_fase = f"rev_fase_{idx}"
            if k_rev_fase not in st.session_state:
                st.session_state[k_rev_fase] = "resumo"
                
            if st.session_state[k_rev_fase] == "resumo":
                resumo = get_resumo(user.id, iid)
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
                k_teoria = f"teoria_{grupo}_{subgrupo}"
                res = st.session_state.get(k_teoria)
                
                if res:
                    st.markdown(res)
                else:
                    st.info("Texto base não encontrado na sessão atual. Buscando via IA...")
                    if st.button("Gerar Resumo por IA", key=f"btn_gerar_teoria_rev_{idx}"):
                        with st.spinner("Gerando conteúdo..."):
                            from backend.llm import gerar_conteudo_estudo
                            texto_gerado = gerar_conteudo_estudo(grupo, subgrupo)
                            st.session_state[k_teoria] = texto_gerado
                            st.rerun()
                if st.button("Concluir Revisão Teórica", key=f"btn_fim_teoria_{idx}"):
                    st.session_state[k_rev_fase] = "questoes"
                    st.rerun()
                    
            elif st.session_state[k_rev_fase] == "questoes":
                st.success("Tudo pronto! Resolva as questões abaixo para validar a revisão.")
                k_q = f"q_{idx}"
                k_resp = f"resp_{idx}"
                
                if k_q not in st.session_state:
                    resp_hist = supabase.table("respostas").select("questao_id").eq("user_id", user.id).execute().data
                    answered = set(r["questao_id"] for r in resp_hist)
                    todas = supabase.table("questoes").select("*").eq("item_id", iid).gte("valida", 0).execute().data
                    validas = [q for q in todas if q["id"] not in answered]
                    
                    if validas:
                        import random
                        row_q = random.choice(validas)
                        alt_dict = {
                            "A": row_q.get('alternativa_a', 'N/A'),
                            "B": row_q.get('alternativa_b', 'N/A'),
                            "C": row_q.get('alternativa_c', 'N/A'),
                            "D": row_q.get('alternativa_d', 'N/A'),
                            "E": row_q.get('alternativa_e', 'N/A')
                        }
                        q_json = {
                            "id": int(row_q['id']),
                            "enunciado": row_q.get('enunciado', ''),
                            "alternativas": alt_dict,
                            "gabarito": row_q.get('gabarito', 'A'),
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
                            btn_rem = False
                            if is_admin:
                                btn_rem = st.button("🗑️ Remover Questão", key=f"btn_rem_antes_{idx}")
                            
                        if btn_mentoria_antes:
                            from backend.llm import mentoria_ia
                            with st.spinner("Tutor IA pensando..."):
                                st.info(mentoria_ia(q_json['enunciado'], opts, choice[0] if choice else None))
                        
                        if btn_rem:
                            supabase.table("questoes").update({"valida": -1}).eq("id", q_json['id']).execute()
                            del st.session_state[k_q]
                            st.warning("Questão invalidada do banco de dados com sucesso!")
                            st.rerun()
                            
                        gab_correto = str(q_json.get('gabarito', '')).strip().upper()
                        if gab_correto in ['N/A', 'NONE', '']:
                            st.info("⚠️ O gabarito desta questão não pôde ser lido do PDF. Quando você responder, a IA deduzirá a alternativa correta e a salvará no banco permanentemente.")
    
                        if btn_resp:
                            if choice:
                                if gab_correto in ['N/A', 'NONE', '']:
                                    from backend.llm import resolver_gabarito_ia
                                    with st.spinner("🧠 IA resolvendo a questão para descobrir o gabarito..."):
                                        novo_gab = resolver_gabarito_ia(q_json['enunciado'], q_json['alternativas'])
                                        supabase.table("questoes").update({"gabarito": novo_gab}).eq("id", q_json['id']).execute()
                                        q_json['gabarito'] = novo_gab
                                        gab_correto = novo_gab
                                        st.session_state[k_q] = q_json
    
                                l_choice = choice[0]
                                acertou = (str(l_choice).strip().upper() == gab_correto)
                                
                                supabase.table("questoes").update({"valida": 1}).eq("id", q_json['id']).execute()
                                supabase.table("respostas").insert({
                                    "user_id": user.id,
                                    "questao_id": q_json['id'],
                                    "acertou": bool(acertou),
                                    "tempo_segundos": 0
                                }).execute()
                                
                                processar_resposta(user.id, q_json['id'], acertou)
                                
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
                            btn_rem = False
                            if is_admin:
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
                            supabase.table("questoes").update({"valida": -1}).eq("id", q_json['id']).execute()
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
                                alts = nova_q.get('alternativas', {})
                                nova_questao = {
                                    "item_id": int(iid),
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
                                if k_q in st.session_state: del st.session_state[k_q]
                                st.rerun()
                                
    st.markdown("---")
    st.subheader("Bloco 4: Modo Prova")
    st.info("Após concluir a apreensão de novos temas e as revisões pendentes, vá para a aba **Modo Prova** para o treinamento misto de resistência!")
