import streamlit as st
import pandas as pd
import datetime
from backend.db import get_supabase

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        st.error("Faça login para ver seu diagnóstico.")
        return

    st.header("Conselho do Tutor: Diagnóstico de Evolução 🤖🩺")
    st.markdown("Identifique seus padrões de erro e receba um plano de ação cirúrgico.")
    
    periodo_str = st.selectbox("Selecione o período de análise:", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Todo o histórico"])
    dias_map = {"Últimos 7 dias": 7, "Últimos 15 dias": 15, "Últimos 30 dias": 30, "Todo o histórico": 9999}
    dias = dias_map[periodo_str]
    
    if st.button("Gerar Diagnóstico IA", type="primary"):
        with st.spinner("Extraindo dados do Supabase e consultando o Tutor IA..."):
            data_corte = (datetime.datetime.utcnow() - datetime.timedelta(days=dias)).isoformat()
            
            # Puxa respostas
            resp_historico = supabase.table("respostas").select(
                "acertou, questoes!inner(enunciado, gabarito, itens_estudo!inner(nome, subgrupos!inner(nome, grupos!inner(nome))))"
            ).eq("user_id", user.id).gte("data", data_corte).execute().data
            
            total_resp = len(resp_historico)
            total_acertos = sum(1 for r in resp_historico if r["acertou"])
            taxa_geral = (total_acertos / total_resp * 100) if total_resp > 0 else 0
            
            if total_resp < 5:
                st.warning("Histórico insuficiente neste período para um diagnóstico preciso. Responda mais questões!")
            else:
                stats_str = f"Questões respondidas: {total_resp}\nAcertos: {total_acertos}\nTaxa de Acerto Geral: {taxa_geral:.1f}%\n\n"
                
                # Agrupar erros por item/subgrupo
                df = []
                for r in resp_historico:
                    q = r["questoes"]
                    item = q["itens_estudo"]
                    sub = item["subgrupos"]
                    grp = sub["grupos"]
                    df.append({
                        "grupo": grp["nome"],
                        "subgrupo": sub["nome"],
                        "item": item["nome"],
                        "acertou": r["acertou"],
                        "enunciado": q["enunciado"]
                    })
                
                df = pd.DataFrame(df)
                
                # Piores itens
                agrupado = df.groupby(["grupo", "subgrupo", "item"]).agg(
                    qtd=("acertou", "count"),
                    acertos=("acertou", "sum")
                ).reset_index()
                
                agrupado["taxa"] = (agrupado["acertos"] / agrupado["qtd"]) * 100
                agrupado = agrupado[agrupado["qtd"] >= 2].sort_values("taxa", ascending=True).head(3)
                
                erros_detalhados = ""
                for _, row in agrupado.iterrows():
                    erros_detalhados += f"\n--- PONTO CRÍTICO: {row['grupo']} > {row['subgrupo']} > {row['item']} (Taxa de acerto: {row['taxa']:.1f}%) ---\n"
                    # Pegar exemplos de questoes erradas
                    erradas_item = df[(df["item"] == row["item"]) & (df["acertou"] == False)].head(5)
                    for _, err_row in erradas_item.iterrows():
                        erros_detalhados += f"- Enunciado: {err_row['enunciado']}\n"
                
                if not erros_detalhados:
                    st.success("Não encontramos Itens de Estudo com erros consistentes neste período! Ótimo trabalho.")
                else:
                    from backend.llm import conselho_tutor_ia
                    st.markdown("### 📝 Relatório do Tutor")
                    gerador = conselho_tutor_ia(stats_str, erros_detalhados, stream=True)
                    st.write_stream(gerador)

