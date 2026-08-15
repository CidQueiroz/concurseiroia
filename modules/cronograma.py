import streamlit as st
import pandas as pd
from backend.db import get_supabase

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        st.error("Faça login para acessar o Cronograma.")
        return

    st.header("Cronograma de Batalha 📅 (Motor AMV 2.0)")
    st.markdown("Esqueça tabelas rígidas! A Inteligência Artificial monta o seu cronograma diário todos os dias com base na sua **curva de esquecimento** (Spaced Repetition).")
    
    st.markdown("---")
    st.subheader("📚 Seleção de Matérias do Seu Perfil")
    
    # 1. Pegar grupos disponíveis no banco
    grupos_resp = supabase.table("grupos").select("nome").execute().data
    opcoes_disponiveis = [g['nome'] for g in grupos_resp] if grupos_resp else []
    
    # 2. Pegar os grupos que o usuário já tem
    resp_a = supabase.table("aprendizado_item").select("itens_estudo!inner(subgrupos!inner(grupos!inner(nome)))").eq("user_id", user.id).execute().data
    grupos_atuais = set()
    for a in resp_a:
        if a.get('itens_estudo') and a['itens_estudo'].get('subgrupos'):
            grupos_atuais.add(a['itens_estudo']['subgrupos']['grupos']['nome'])
            
    grupos_atuais_list = sorted(list(grupos_atuais))
    
    if grupos_atuais_list:
        st.success(f"Você está focado em **{len(grupos_atuais_list)}** matérias atualmente.")
        st.caption(", ".join(grupos_atuais_list))
    else:
        st.warning("⚠️ Você ainda não vinculou nenhuma matéria ao seu perfil. Selecione abaixo para começar os estudos!")
        
    novos_grupos = st.multiselect("Matérias (Grupos) que você quer estudar:", opcoes_disponiveis, default=grupos_atuais_list)
    
    if st.button("Atualizar Matérias do Perfil"):
        selecionados_set = set(novos_grupos)
        grupos_adicionar = selecionados_set - grupos_atuais
        grupos_remover = grupos_atuais - selecionados_set
        
        mudou = False
        
        if grupos_adicionar:
            from backend.scheduler import inicializar_itens
            with st.spinner("Vinculando itens de estudo e montando perfil de aprendizagem..."):
                inicializar_itens(user.id, novos_grupos=list(grupos_adicionar))
            mudou = True
            
        if grupos_remover:
            with st.spinner("Desvinculando matérias antigas..."):
                resp_itens = supabase.table("itens_estudo").select("id, subgrupos!inner(grupos!inner(nome))").in_("subgrupos.grupos.nome", list(grupos_remover)).execute().data
                ids_remover = [i['id'] for i in resp_itens]
                if ids_remover:
                    for i in range(0, len(ids_remover), 100):
                        supabase.table("aprendizado_item").delete().eq("user_id", user.id).in_("item_id", ids_remover[i:i+100]).execute()
            mudou = True
            
        if mudou:
            if "plano_diario" in st.session_state: del st.session_state["plano_diario"]
            st.success("Matérias atualizadas com sucesso! Vá para a aba **Hoje** para começar a estudar.")
            st.rerun()
        else:
            st.info("O seu perfil já possui as matérias que você selecionou e nenhuma foi removida.")
            
    st.markdown("---")
    
    st.subheader("Sua Agenda para Hoje")
    from backend.scheduler import montar_plano_diario
    novos, revs = montar_plano_diario(user.id)
    
    if not novos and not revs:
        st.info("Sua agenda para hoje está vazia.")
    
    # Montar agenda em DF
    agenda = []
    t_start = 8 # começa as 08:00
    for n in novos:
        agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Apreensão & Active Recall", "Tópico": f"{n.get('grupo_nome', '')} - {n.get('item_nome', '')}"})
        t_start += 1
        
    for r in revs:
        agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Revisão Espaçada (SRS)", "Tópico": f"{r.get('grupo_nome', '')} - {r.get('item_nome', '')}"})
        t_start += 1
        
    agenda.append({"Horário": f"{t_start:02d}:00", "Atividade": "Modo Prova (Resistência)", "Tópico": "Misto"})
    
    df_agenda = pd.DataFrame(agenda)
    st.dataframe(df_agenda, width="stretch", hide_index=True)
    
    st.markdown("---")
    
    is_admin = (user.email == "cydy.potter@gmail.com")
    if is_admin:
        st.subheader("Resumo de Questões no Banco 📚")
        
        try:
            # Puxa o resumo do supabase
            # Contagem de questoes por grupo
            questoes = supabase.table("questoes").select("valida, itens_estudo!inner(subgrupos!inner(grupos(nome)))").execute().data
            
            resumo = {}
            for q in questoes:
                grp = q['itens_estudo']['subgrupos']['grupos']['nome']
                val = q['valida']
                if grp not in resumo:
                    resumo[grp] = {"Grupo": grp, "Total": 0, "Validadas ✅": 0, "Não Validadas ⚠️": 0}
                    
                resumo[grp]["Total"] += 1
                if val == 1:
                    resumo[grp]["Validadas ✅"] += 1
                else:
                    resumo[grp]["Não Validadas ⚠️"] += 1
                    
            df_resumo = pd.DataFrame(list(resumo.values()))
            if not df_resumo.empty:
                st.dataframe(df_resumo, width="stretch", hide_index=True)
            else:
                st.info("O banco de dados ainda não possui estatísticas de questões.")
        except Exception as e:
            st.error(f"Erro ao carregar resumo de questões: {e}")

