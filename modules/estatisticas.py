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
    
    is_admin = (user.email == "cydy.potter@gmail.com")
    
    if is_admin:
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
        
    # 4. Métricas de Desempenho por Matéria (apenas vinculadas)
    resp_a = supabase.table("aprendizado_item").select("itens_estudo!inner(subgrupos!inner(grupos!inner(nome)))").eq("user_id", user.id).execute().data
    grupos_atuais = set()
    for a in resp_a:
        if a.get('itens_estudo') and a['itens_estudo'].get('subgrupos'):
            grupos_atuais.add(a['itens_estudo']['subgrupos']['grupos']['nome'])
            
    st.subheader("Métricas de Desempenho por Matéria 📊")
    
    if not df_resp.empty and grupos_atuais:
        df_resp_linked = df_resp[df_resp['grupo_nome'].isin(grupos_atuais)]
        agg_disc = df_resp_linked.groupby('grupo_nome').agg(
            respondidas=('id', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
        
        dados_disciplinas = []
        for g in sorted(list(grupos_atuais)):
            resp_g = 0
            acrt_g = 0
            row = agg_disc[agg_disc['grupo_nome'] == g]
            if not row.empty:
                resp_g = int(row['respondidas'].iloc[0])
                acrt_g = int(row['acertos'].iloc[0])
            
            taxa = (acrt_g / resp_g * 100) if resp_g > 0 else 0.0
            
            dados_disciplinas.append({
                "Disciplina": g,
                "Respondidas": resp_g,
                "Acertos": acrt_g,
                "% de Acerto": f"{taxa:.1f}%"
            })
            
        df_disc = pd.DataFrame(dados_disciplinas)
        
        total_resp = df_disc['Respondidas'].sum()
        total_acertos = df_disc['Acertos'].sum()
        total_taxa = (total_acertos / total_resp * 100) if total_resp > 0 else 0.0
        
        df_disc.loc[len(df_disc)] = {
            "Disciplina": "TOTAL (Média Geral)", 
            "Respondidas": total_resp, 
            "Acertos": total_acertos, 
            "% de Acerto": f"{total_taxa:.1f}%"
        }
        
        styled_df_disc = df_disc.style.set_properties(
            subset=['Respondidas', 'Acertos', '% de Acerto'], 
            **{'text-align': 'center'}
        )
        st.dataframe(styled_df_disc, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma matéria vinculada ou nenhuma resposta registrada para as matérias atuais.")
        
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
        
        daily_acc['Acerto Dia (%)'] = (daily_acc['acertos'] / daily_acc['total']) * 100
        
        daily_acc['total_acumulado'] = daily_acc['total'].cumsum()
        daily_acc['acertos_acumulados'] = daily_acc['acertos'].cumsum()
        daily_acc['Acerto Geral (%)'] = (daily_acc['acertos_acumulados'] / daily_acc['total_acumulado']) * 100
        
        daily_acc['data_dia_dt'] = pd.to_datetime(daily_acc['data_dia'], format='mixed', utc=True)
        
        import altair as alt
        
        df_melted = daily_acc.melt(
            id_vars=['data_dia_dt'], 
            value_vars=['Acerto Dia (%)', 'Acerto Geral (%)'], 
            var_name='Indicador', 
            value_name='Taxa de Acerto (%)'
        )
        
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        min_date = df_resp_tempo['data_dia_dt'].min().strftime('%Y-%m-%d') if 'data_dia_dt' in df_resp_tempo and not df_resp_tempo.empty else '2026-07-04'
        
        datas_ticks = pd.date_range(start=min_date, end=hoje).tolist()
        
        chart = alt.Chart(df_melted).mark_line(point=True, interpolate='monotone').encode(
            x=alt.X('data_dia_dt:T', scale=alt.Scale(domain=[min_date, hoje]), title='Data', axis=alt.Axis(values=datas_ticks, format='%d/%m', labelAngle=-45)),
            y=alt.Y('Taxa de Acerto (%):Q', scale=alt.Scale(domain=[0, 100], nice=False), title='Taxa de Acerto (%)', axis=alt.Axis(tickCount=10, labelOverlap=False)),
            color=alt.Color('Indicador:N', legend=alt.Legend(title=None, orient="bottom")),
            tooltip=[alt.Tooltip('data_dia_dt:T', title='Data', format='%d/%m/%Y'), 'Indicador', alt.Tooltip('Taxa de Acerto (%):Q', format='.1f')]
        )
        
        # Linha de Meta (80%)
        rule = alt.Chart(pd.DataFrame({'y': [80]})).mark_rule(color='#ff4b4b', strokeDash=[5, 5]).encode(y='y:Q')
        
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
