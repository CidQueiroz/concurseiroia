import streamlit as st
import pandas as pd
import datetime
from backend.db import get_supabase

def render(DB_PATH=None):
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        st.error("Você precisa estar logado para ver as estatísticas.")
        return
        
    st.header("Radar do Edital 📊")
    
    # 1. Progresso do Banco (Global, não depende do user)
    total_q = supabase.table("questoes").select("id", count="exact").execute().count or 0
    validadas = supabase.table("questoes").select("id", count="exact").eq("valida", 1).execute().count or 0
    removidas = supabase.table("questoes").select("id", count="exact").eq("valida", -1).execute().count or 0
    nao_validadas = total_q - validadas - removidas
    
    st.subheader("Progresso do Banco de Questões 🗃️")
    colV1, colV2, colV3 = st.columns(3)
    colV1.metric("Validadas ✅", validadas, help="Questões validadas (com gabarito revisado).")
    colV2.metric("Aguardando Validação ⏳", nao_validadas, help="Questões inéditas no banco (sem gabarito ou geradas por IA).")
    colV3.metric("Removidas 🗑️", removidas, help="Questões com defeito que foram descartadas.")
    st.markdown("---")
    
    # 2. Distribuição do Banco
    st.subheader("Distribuição do Banco de Questões 📚")
    resp_dist = supabase.table("questoes").select("id, itens_estudo(nome, subgrupos(nome, grupos(nome)))").execute().data
    
    dist_data = []
    for q in resp_dist:
        if q.get('itens_estudo') and q['itens_estudo'].get('subgrupos') and q['itens_estudo']['subgrupos'].get('grupos'):
            dist_data.append({
                "Grupo": q['itens_estudo']['subgrupos']['grupos']['nome'],
                "Subgrupo": q['itens_estudo']['subgrupos']['nome'],
                "Item": q['itens_estudo']['nome'],
                "id": q['id']
            })
    
    df_dist_raw = pd.DataFrame(dist_data)
    if not df_dist_raw.empty:
        df_dist = df_dist_raw.groupby(['Grupo', 'Subgrupo']).agg(Quantidade=('id', 'count')).reset_index()
        df_dist = df_dist.sort_values("Quantidade", ascending=False)
        st.dataframe(df_dist, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma questão no banco.")
        
    st.markdown("---")
    
    # 3. Buscando respostas do Usuario logado
    resp_respostas = supabase.table("respostas").select("id, questao_id, acertou, tempo_segundos, data, questoes(itens_estudo(nome, subgrupos(nome, grupos(nome))))").eq("user_id", user.id).execute().data
    
    resp_data = []
    for r in resp_respostas:
        if r.get('questoes') and r['questoes'].get('itens_estudo') and r['questoes']['itens_estudo'].get('subgrupos') and r['questoes']['itens_estudo']['subgrupos'].get('grupos'):
            g_nome = r['questoes']['itens_estudo']['subgrupos']['grupos']['nome']
            s_nome = r['questoes']['itens_estudo']['subgrupos']['nome']
            i_nome = r['questoes']['itens_estudo']['nome']
            
            if g_nome.upper() not in ['FORA DO EDITAL', 'NÃO CLASSIFICADO', 'NAO CLASSIFICADO']:
                resp_data.append({
                    "id": r['id'],
                    "questao_id": r['questao_id'],
                    "acertou": r['acertou'],
                    "tempo_segundos": r['tempo_segundos'],
                    "data": r['data'],
                    "grupo_nome": g_nome,
                    "subgrupo_nome": s_nome,
                    "item_nome": i_nome
                })
                
    df_resp = pd.DataFrame(resp_data)
    
    total_q = len(df_resp) if not df_resp.empty else 0
    if total_q > 0:
        acertos = df_resp['acertou'].sum()
        tx_acerto = (acertos / total_q) * 100
    else:
        tx_acerto = 0
        
    # 4. Projeção de Nota
    resp_sub_pesos = supabase.table("subgrupos").select("peso, grupos(nome)").execute().data
    pesos_data = []
    for s in resp_sub_pesos:
        if s.get('grupos'):
            pesos_data.append({"nome": s['grupos']['nome'], "peso": s['peso']})
    
    df_pesos_raw = pd.DataFrame(pesos_data)
    if not df_pesos_raw.empty:
        df_pesos = df_pesos_raw.groupby('nome').agg(avg_peso=('peso', 'mean')).reset_index()
    else:
        df_pesos = pd.DataFrame(columns=['nome', 'avg_peso'])
        
    qtd_prova = {
        "LÍNGUA PORTUGUESA": 12, 
        "LÍNGUA INGLESA": 12, 
        "RACIOCÍNIO LÓGICO MATEMÁTICO": 5, 
        "ATUALIDADES E INTELIGÊNCIA ARTIFICIAL": 6, 
        "LEGISLAÇÃO ACERCA DE SEGURANÇA DA INFORMAÇÃO E PROTEÇÃO DE DADOS": 5,
        "Conhecimentos Específicos": 30
    }
    
    agg_disc = pd.DataFrame()
    if not df_resp.empty:
        def get_disciplina(row):
            gn = str(row['grupo_nome']).strip().upper()
            if gn in qtd_prova: 
                return gn
            # Trata LEGISLAÇÃO, SEGURANÇA E PROTEÇÃO DE DADOS como LEGISLAÇÃO ACERCA DE... se houver nome reduzido
            if gn == "LEGISLAÇÃO, SEGURANÇA E PROTEÇÃO DE DADOS":
                return "LEGISLAÇÃO ACERCA DE SEGURANÇA DA INFORMAÇÃO E PROTEÇÃO DE DADOS"
            return "Conhecimentos Específicos"
            
        df_resp['disciplina'] = df_resp.apply(get_disciplina, axis=1)
        agg_disc = df_resp.groupby('disciplina').agg(
            respondidas=('id', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
    
    def get_stats(disc):
        if not agg_disc.empty:
            row = agg_disc[agg_disc['disciplina'] == disc]
            if not row.empty:
                return int(row['respondidas'].iloc[0]), int(row['acertos'].iloc[0])
        return 0, 0
    
    dados_disciplinas = []
    total_proj = 0.0
    
    disciplinas_avaliadas = [k for k in qtd_prova.keys() if k != "Conhecimentos Específicos"] + ["Conhecimentos Específicos"]
    
    for disc in disciplinas_avaliadas:
        peso = 2.5 if disc == "Conhecimentos Específicos" else 1.0
        qtd = qtd_prova.get(disc, 0)
        max_pts = qtd * peso
        resp, acrt = get_stats(disc)
        taxa = (acrt / resp) if resp > 0 else 0.0
        proj = taxa * max_pts
        
        dados_disciplinas.append({
            "Disciplina": disc,
            "Respondidas": resp,
            "Acertos": acrt,
            "% de Acerto": f"{(taxa * 100):.1f}%" if resp > 0 else "0.0%",
            "Pontuação Projetada": round(proj, 2)
        })
        
        total_proj += proj
        
    df_disc = pd.DataFrame(dados_disciplinas)
    
    total_resp = df_disc['Respondidas'].sum()
    total_acertos = df_disc['Acertos'].sum()
    total_taxa = (total_acertos / total_resp * 100) if total_resp > 0 else 0.0
    
    df_disc.loc[len(df_disc)] = {
        "Disciplina": "TOTAL (Projeção do Simulado)", 
        "Respondidas": total_resp, 
        "Acertos": total_acertos, 
        "% de Acerto": f"{total_taxa:.1f}%",
        "Pontuação Projetada": round(total_proj, 2)
    }
    
    st.subheader("Projeção de Pontuação Real da Prova 🏆")
    st.markdown("A tabela abaixo mapeia suas respostas e calcula qual seria sua nota exata **se a prova fosse hoje**, de acordo com os pesos do Edital (Total de 115 pts).")
    
    styled_df_disc = df_disc.style.set_properties(
        subset=['Respondidas', 'Acertos', '% de Acerto', 'Pontuação Projetada'], 
        **{'text-align': 'center'}
    )
    st.dataframe(styled_df_disc, width="stretch", hide_index=True)
        
    st.markdown("---")
    st.markdown("<h3 style='margin-top: 0px; margin-bottom: -30px;'>Evolução Temporal 📈</h3>", unsafe_allow_html=True)
    if not df_resp.empty:
        df_resp_tempo = df_resp.copy()
        df_resp_tempo['data'] = pd.to_datetime(df_resp_tempo['data'], format='mixed', utc=True).dt.tz_localize(None)
        df_resp_tempo['data_dia'] = df_resp_tempo['data'].dt.date
        
        daily_acc = df_resp_tempo.groupby('data_dia').agg(
            total=('acertou', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
        
        daily_acc['Pontos no Dia'] = (daily_acc['acertos'] / daily_acc['total']) * 115
        
        daily_acc['total_acumulado'] = daily_acc['total'].cumsum()
        daily_acc['acertos_acumulados'] = daily_acc['acertos'].cumsum()
        daily_acc['Pontos Gerais'] = (daily_acc['acertos_acumulados'] / daily_acc['total_acumulado']) * 115
        
        daily_acc['data_dia_dt'] = pd.to_datetime(daily_acc['data_dia'], format='mixed', utc=True)
        
        import altair as alt
        
        df_melted = daily_acc.melt(
            id_vars=['data_dia_dt'], 
            value_vars=['Pontos no Dia', 'Pontos Gerais'], 
            var_name='Indicador', 
            value_name='Pontuação'
        )
        
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        # Determinar a primeira data de resposta real ou fallback
        min_date = df_resp_tempo['data_dia_dt'].min().strftime('%Y-%m-%d') if 'data_dia_dt' in df_resp_tempo and not df_resp_tempo.empty else '2026-07-04'
        
        datas_ticks = pd.date_range(start=min_date, end=hoje).tolist()
        
        chart = alt.Chart(df_melted).mark_line(point=True, interpolate='monotone').encode(
            x=alt.X('data_dia_dt:T', scale=alt.Scale(domain=[min_date, hoje]), title='Data', axis=alt.Axis(values=datas_ticks, format='%d/%m', labelAngle=-45)),
            y=alt.Y('Pontuação:Q', scale=alt.Scale(domain=[0, 120], nice=False), title='Pontuação Projetada (Max: 115)', axis=alt.Axis(tickCount=24, labelOverlap=False)),
            color=alt.Color('Indicador:N', legend=alt.Legend(title=None, orient="bottom")),
            tooltip=[alt.Tooltip('data_dia_dt:T', title='Data', format='%d/%m/%Y'), 'Indicador', alt.Tooltip('Pontuação:Q', format='.1f')]
        )
        
        rule = alt.Chart(pd.DataFrame({'y': [115]})).mark_rule(color='#ff4b4b', strokeDash=[5, 5]).encode(y='y:Q')
        
        final_chart = (chart + rule).properties(
            height=600,
            padding={"top": 0, "bottom": 0}
        ).configure_view(
            strokeWidth=0,
            stroke="transparent"
        )
        
        st.altair_chart(final_chart, use_container_width=True)
    else:
        st.info("Responda mais questões para visualizar seu gráfico de evolução.")
    
    st.markdown("---")
    st.subheader("Índice de Domínio (AMV 2.0) 🧠")
    
    resp_amv = supabase.table("aprendizado_item").select("*, itens_estudo(nome)").eq("user_id", user.id).neq("status", "NOVO").order("nivel_dominio", desc=True).execute().data
    
    amv_data = []
    for a in resp_amv:
        if a.get('itens_estudo'):
            amv_data.append({
                "Tópico": a['itens_estudo']['nome'],
                "dominio_perc": a['nivel_dominio'],
                "taxa_acerto": a['taxa_acerto'],
                "questoes_respondidas": a['questoes_respondidas'],
                "numero_revisoes": a['numero_revisoes'],
                "status": a['status']
            })
            
    df_amv2 = pd.DataFrame(amv_data)
    
    if not df_amv2.empty:
        dominados = len(df_amv2[df_amv2['status'] == 'DOMINADO'])
        em_aprendiz = len(df_amv2[df_amv2['status'].isin(['RETENCAO_INICIAL', 'REVISAO_1', 'REVISAO_2', 'REVISAO_3'])])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Subgrupos Dominados 🏆", dominados)
        c2.metric("Em Aprendizagem 📈", em_aprendiz)
        c3.metric("Reconhecimento Inic 🔍", len(df_amv2[df_amv2['status'] == 'RECONHECIMENTO']))
        
        def get_class(acc):
            if acc >= 95: return 'Dominado'
            if acc >= 80: return 'Especialista'
            if acc >= 60: return 'Avançado'
            if acc >= 40: return 'Intermediário'
            if acc >= 20: return 'Aprendiz'
            return 'Iniciante'
            
        df_amv2['Nível'] = df_amv2['dominio_perc'].apply(get_class)
        df_amv2['Índice'] = df_amv2['dominio_perc'].apply(lambda x: f"{x}%")
        df_amv2['Acertos'] = df_amv2['taxa_acerto'].apply(lambda x: f"{x:.1f}%")
        df_amv2['Questões'] = df_amv2['questoes_respondidas'].astype(int)
        df_amv2['Revisões'] = df_amv2['numero_revisoes'].astype(int)
        df_amv2['Status AMV'] = df_amv2['status']
        
        colunas_exibir = ['Tópico', 'Nível', 'Índice', 'Acertos', 'Questões', 'Revisões', 'Status AMV']
        colunas_center = ['Nível', 'Índice', 'Acertos', 'Questões', 'Revisões', 'Status AMV']
        styled_amv2 = df_amv2[colunas_exibir].style.set_properties(subset=colunas_center, **{'text-align': 'center'})
        
        st.dataframe(styled_amv2, width="stretch", hide_index=True, height=(len(df_amv2) + 1) * 35 + 3)
    else:
        st.info("Ainda não há dados no motor de aprendizagem. Comece a estudar!")
    
    st.markdown("---")
    st.subheader("Desempenho por Tópico (Raio-X)")
    
    if not df_resp.empty:
        df_resp_raiox = df_resp.copy()
        df_resp_raiox['topico_completo'] = df_resp_raiox['subgrupo_nome'] + ' ➔ ' + df_resp_raiox['item_nome']
        
        agg_resp = df_resp_raiox.groupby("topico_completo").agg(
            total_questoes=('id', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
        agg_resp['taxa_acerto'] = (agg_resp['acertos'] / agg_resp['total_questoes'] * 100).round(1)
    else:
        agg_resp = pd.DataFrame(columns=["topico_completo", "total_questoes", "acertos", "taxa_acerto"])
        
    if not agg_resp.empty:
        df_raiox = agg_resp[["topico_completo", "total_questoes", "taxa_acerto"]].sort_values("total_questoes", ascending=False)
        styled_raiox = df_raiox.style.set_properties(subset=['total_questoes'], **{'text-align': 'center'})
        
        st.dataframe(
            styled_raiox,
            column_config={
                "topico_completo": "Tópico (Subgrupo ➔ Item)",
                "total_questoes": "Questões",
                "taxa_acerto": st.column_config.ProgressColumn("Acerto (%)", min_value=0, max_value=100, format="%f%%")
            },
            hide_index=True,
            width="stretch",
            height=(len(agg_resp) + 1) * 35 + 3
        )
    else:
        st.info("Ainda não há dados suficientes para gerar as estatísticas por tópico.")
        
    '''st.markdown("---")
    st.subheader("Tempo de Resolução dos Simulados ⏱️")
    
    resp_sim = supabase.table("historico_simulados").select("*").eq("user_id", user.id).order("data", desc=False).execute().data
    df_sim_time = pd.DataFrame(resp_sim)
    
    if not df_sim_time.empty:
        df_sim_time['data'] = pd.to_datetime(df_sim_time['data'], format='mixed', utc=True).dt.tz_localize(None)
        df_sim_time['data_simulado'] = df_sim_time['data'].dt.date
        
        df_sim_time['Minutos'] = (df_sim_time['tempo_segundos'] / 60).round(1)
        df_sim_time['Data (ID)'] = df_sim_time.apply(lambda r: f"{r['data_simulado'].strftime('%d/%m')} (Sim #{r['id']})", axis=1)
        
        import altair as alt
        
        chart_time = alt.Chart(df_sim_time).mark_bar(color='#1f77b4').encode(
            x=alt.X('Minutos:Q', title='Tempo Total (minutos)'),
            y=alt.Y('Data (ID):N', title='Data do Simulado', sort=None),
            tooltip=[alt.Tooltip('Data (ID):N', title='Simulado'), 
                     alt.Tooltip('Minutos:Q', title='Minutos Decorridos'),
                     alt.Tooltip('pontuacao_total:Q', title='Pontuação Obtida')]
        ).properties(
            height=max(200, len(df_sim_time) * 40),
        )
        
        st.altair_chart(chart_time, use_container_width=True)
    else:
        st.info("Conclua Simulados Gerais na aba 'Modo Prova' para visualizar o histórico de tempo de resolução.")'''
