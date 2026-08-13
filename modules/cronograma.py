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
    
    from backend.scheduler import montar_plano_diario
    novos, revs = montar_plano_diario(user.id)
    
    # Se não houver itens a estudar, permitir escolher grupo
    if not novos and not revs:
        st.info("Seu cronograma atual está vazio (ou você concluiu tudo). Que tal focar em uma matéria específica?")
        grupos_resp = supabase.table("grupos").select("nome").execute().data
        if grupos_resp:
            opcoes = [g['nome'] for g in grupos_resp]
            grupo_escolhido = st.selectbox("Selecione um Grupo (Matéria) para focar hoje:", opcoes)
            if st.button("Gerar Cronograma para " + grupo_escolhido):
                # Puxar Itens deste grupo no Supabase
                itens_resp = supabase.table("itens_estudo").select("*, subgrupos!inner(nome, grupos!inner(nome))").eq("subgrupos.grupos.nome", grupo_escolhido).execute().data
                
                novos = []
                for i in itens_resp[:2]: # Pega os 2 primeiros itens para fingir o cronograma
                    novos.append({
                        "grupo_nome": i['subgrupos']['grupos']['nome'],
                        "subgrupo_nome": i['subgrupos']['nome'],
                        "item_nome": i['nome']
                    })
                st.success("Cronograma focado gerado! (Nota: esta visualização na aba é ilustrativa)")
    
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

