import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import os
import datetime

def render(DB_PATH):
    st.header("Radar do Edital 📊")
    
    # Progresso do Banco
    conn_val = sqlite3.connect(DB_PATH, timeout=15)
    try:
        cur_val = conn_val.cursor()
        cur_val.execute("SELECT COUNT(*) FROM questoes WHERE valida = 1")
        validadas = cur_val.fetchone()[0]
        cur_val.execute("SELECT COUNT(*) FROM questoes WHERE valida = 0 OR valida IS NULL")
        nao_validadas = cur_val.fetchone()[0]
        cur_val.execute("SELECT COUNT(*) FROM questoes WHERE valida = -1")
        removidas = cur_val.fetchone()[0]
    except Exception:
        validadas = nao_validadas = removidas = 0
    conn_val.close()
    
    st.subheader("Progresso do Banco de Questões 🗃️")
    colV1, colV2, colV3 = st.columns(3)
    colV1.metric("Validadas ✅", validadas, help="Questões que você já respondeu ou editou.")
    colV2.metric("Aguardando Validação ⏳", nao_validadas, help="Questões inéditas no banco.")
    colV3.metric("Removidas 🗑️", removidas, help="Questões com defeito que foram descartadas.")
    st.markdown("---")
    
    st.subheader("Distribuição do Banco de Questões 📚")
    conn_dist = sqlite3.connect(DB_PATH, timeout=15)
    try:
        df_dist = pd.read_sql_query("""
            SELECT g.nome as "Grupo", s.nome as "Subgrupo", COUNT(q.id) as "Quantidade"
            FROM questoes q
            LEFT JOIN subgrupos s ON q.subgrupo_id = s.id
            LEFT JOIN grupos g ON s.grupo_id = g.id
            GROUP BY g.nome, s.nome
            ORDER BY "Quantidade" DESC
        """, conn_dist)
        st.dataframe(df_dist, width="stretch", hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar distribuição: {e}")
    conn_dist.close()
    
    st.markdown("---")
    
    conn = sqlite3.connect(DB_PATH, timeout=15)
    
    # Busca respostas (se a tabela ou views não existirem corretamente, pd pode falhar. Usamos try except generico apenas em caso de BD novo)
    try:
        df_resp = pd.read_sql_query("""
            SELECT r.id, r.questao_id, r.acertou, r.tempo_segundos, q.subgrupo_id, s.nome as subgrupo_nome, g.nome as grupo_nome
            FROM respostas r
            JOIN questoes q ON r.questao_id = q.id
            JOIN subgrupos s ON q.subgrupo_id = s.id
            JOIN grupos g ON s.grupo_id = g.id
            WHERE s.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
            AND g.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
        """, conn)
    except Exception:
        df_resp = pd.DataFrame()
        
    conn.close()
    
    total_q = len(df_resp) if not df_resp.empty else 0
    if total_q > 0:
        acertos = df_resp['acertou'].sum()
        tx_acerto = (acertos / total_q) * 100
    else:
        tx_acerto = 0
        
    """# Exibe métricas globais
    st.subheader("Visão Geral")
    col1, col2 = st.columns(2)
    col1.metric("Questões Respondidas", total_q)
    col2.metric("Taxa de Acerto Geral", f"{tx_acerto:.1f}%")
    
    st.markdown("---")"""
    # Fetch responses over time for the temporal graph
    conn = sqlite3.connect(DB_PATH, timeout=15)
    try:
        df_resp_tempo = pd.read_sql_query("""
            SELECT r.data, r.acertou, g.nome as grupo_nome
            FROM respostas r
            JOIN questoes q ON r.questao_id = q.id
            JOIN subgrupos s ON q.subgrupo_id = s.id
            JOIN grupos g ON s.grupo_id = g.id
            WHERE s.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
            AND g.nome NOT IN ('Fora do Edital', 'Não Classificado', 'NAO CLASSIFICADO')
            ORDER BY r.data ASC
        """, conn)
    except Exception:
        df_resp_tempo = pd.DataFrame()
    conn.close()
    
    # Puxar do banco os grupos e seus pesos médios (Básicos = 1.0, Específicos = 2.5)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    df_pesos = pd.read_sql_query("""
        SELECT g.nome, AVG(s.peso) as avg_peso 
        FROM grupos g 
        JOIN subgrupos s ON s.grupo_id = g.id 
        GROUP BY g.nome
    """, conn)
    conn.close()
    
    # 1.0 -> Básicos (Exibir nome da disciplina real)
    dist_basics = df_pesos[df_pesos['avg_peso'] <= 1.5]['nome'].tolist()
    # Específicos são todos os outros (agrupados sob "Conhecimentos Específicos")
    
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
            # Se for uma disciplina mapeada no edital (básicas), usa o nome dela.
            if gn in qtd_prova: 
                return gn
            # Todo o restante é agrupado em "Conhecimentos Específicos"
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
    
    # Montar a lista formatada com as básicas mapeadas no qtd_prova + Conhecimentos Específicos
    disciplinas_avaliadas = [k for k in qtd_prova.keys() if k != "Conhecimentos Específicos"] + ["Conhecimentos Específicos"]
    
    for disc in disciplinas_avaliadas:
        peso = 2.5 if disc == "Conhecimentos Específicos" else 1.0
        qtd = qtd_prova.get(disc, 0)
        max_pts = qtd * peso
        resp, acertos = get_stats(disc)
        taxa = (acertos / resp) if resp > 0 else 0.0
        proj = taxa * max_pts
        
        dados_disciplinas.append({
            "Disciplina": disc,
            "Respondidas": resp,
            "Acertos": acertos,
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
    if not df_resp_tempo.empty:
        # Convert date column to datetime
        df_resp_tempo['data'] = pd.to_datetime(df_resp_tempo['data'])
        df_resp_tempo['data_dia'] = df_resp_tempo['data'].dt.date
        
        # Group by day to get daily accuracy
        daily_acc = df_resp_tempo.groupby('data_dia').agg(
            total=('acertou', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
        
        # Convertendo a taxa de acerto para a projeção de pontos no edital (Max: 115 pts)
        daily_acc['Pontos no Dia'] = (daily_acc['acertos'] / daily_acc['total']) * 115
        
        # Calcula a pontuação geral acumulada ao longo do tempo
        daily_acc['total_acumulado'] = daily_acc['total'].cumsum()
        daily_acc['acertos_acumulados'] = daily_acc['acertos'].cumsum()
        daily_acc['Pontos Gerais'] = (daily_acc['acertos_acumulados'] / daily_acc['total_acumulado']) * 115
        
        # Usar formato datetime nativo do Pandas para o Altair processar corretamente o eixo X
        daily_acc['data_dia_dt'] = pd.to_datetime(daily_acc['data_dia'])
        
        import altair as alt
        
        # Melt dataframe para o formato longo que o Altair prefere
        df_melted = daily_acc.melt(
            id_vars=['data_dia_dt'], 
            value_vars=['Pontos no Dia', 'Pontos Gerais'], 
            var_name='Indicador', 
            value_name='Pontuação'
        )
        
        import datetime
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        datas_ticks = pd.date_range(start='2026-07-04', end=hoje).tolist()
        
        # Linha base dos dados
        chart = alt.Chart(df_melted).mark_line(point=True, interpolate='monotone').encode(
            x=alt.X('data_dia_dt:T', scale=alt.Scale(domain=['2026-07-04', hoje]), title='Data', axis=alt.Axis(values=datas_ticks, format='%d/%m', labelAngle=-45)),
            y=alt.Y('Pontuação:Q', scale=alt.Scale(domain=[0, 120], nice=False), title='Pontuação Projetada (Max: 115)', axis=alt.Axis(tickCount=24, labelOverlap=False)),
            color=alt.Color('Indicador:N', legend=alt.Legend(title=None, orient="bottom")),
            tooltip=[alt.Tooltip('data_dia_dt:T', title='Data', format='%d/%m/%Y'), 'Indicador', alt.Tooltip('Pontuação:Q', format='.1f')]
        )
        
        # Linha pontilhada vermelha indicando o teto de 115 pontos
        rule = alt.Chart(pd.DataFrame({'y': [115]})).mark_rule(color='#ff4b4b', strokeDash=[5, 5]).encode(y='y:Q')
        
        # Junta os gráficos e ajusta a altura para remover o espaço ocioso
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
    conn = sqlite3.connect(DB_PATH, timeout=15)
    df_amv2 = pd.read_sql_query('''
        SELECT 
            s.nome as Tópico,
            a.nivel_dominio as dominio_perc,
            a.taxa_acerto,
            a.questoes_respondidas,
            a.numero_revisoes,
            a.status
        FROM aprendizado_subgrupo a
        JOIN subgrupos s ON a.subgrupo_id = s.id
        WHERE a.status != 'NOVO'
        ORDER BY a.nivel_dominio DESC
    ''', conn)
    conn.close()
    
    if not df_amv2.empty:
        # Metricas AMV2
        dominados = len(df_amv2[df_amv2['status'] == 'DOMINADO'])
        em_aprendiz = len(df_amv2[df_amv2['status'].isin(['RETENCAO_INICIAL', 'REVISAO_1', 'REVISAO_2', 'REVISAO_3'])])
        atrasados = 0 # Pode calcular via sql proxima_revisao < now
        
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
        agg_resp = df_resp.groupby("subgrupo_nome").agg(
            total_questoes=('id', 'count'),
            acertos=('acertou', 'sum')
        ).reset_index()
        agg_resp['taxa_acerto'] = (agg_resp['acertos'] / agg_resp['total_questoes'] * 100).round(1)
    else:
        agg_resp = pd.DataFrame(columns=["subgrupo_nome", "total_questoes", "acertos", "taxa_acerto"])
        
    if not agg_resp.empty:
        df_raiox = agg_resp[["subgrupo_nome", "total_questoes", "taxa_acerto"]].sort_values("total_questoes", ascending=False)
        styled_raiox = df_raiox.style.set_properties(subset=['total_questoes'], **{'text-align': 'center'})
        
        st.dataframe(
            styled_raiox,
            column_config={
                "subgrupo_nome": "Tópico (Subgrupo)",
                "total_questoes": "Questões",
                "taxa_acerto": st.column_config.ProgressColumn("Acerto (%)", min_value=0, max_value=100, format="%f%%")
            },
            hide_index=True,
            width="stretch",
            height=(len(agg_resp) + 1) * 35 + 3
        )
    else:
        st.info("Ainda não há dados suficientes para gerar as estatísticas por tópico.")
        
    st.markdown("---")
    st.subheader("Tempo de Resolução dos Simulados ⏱️")
    
    conn = sqlite3.connect(DB_PATH, timeout=15)
    try:
        df_sim_time = pd.read_sql_query('''
            SELECT id, date(data) as data_simulado, tempo_segundos, pontuacao_total 
            FROM historico_simulados 
            ORDER BY data ASC
        ''', conn)
    except Exception:
        df_sim_time = pd.DataFrame()
    conn.close()
    
    if not df_sim_time.empty:
        # Convert seconds to minutes for the chart
        df_sim_time['Minutos'] = (df_sim_time['tempo_segundos'] / 60).round(1)
        # Format date
        df_sim_time['Data (ID)'] = df_sim_time.apply(lambda r: f"{pd.to_datetime(r['data_simulado']).strftime('%d/%m')} (Sim #{r['id']})", axis=1)
        
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
        st.info("Conclua Simulados Gerais na aba 'Modo Prova' para visualizar o histórico de tempo de resolução.")
