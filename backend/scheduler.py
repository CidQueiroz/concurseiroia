import pandas as pd
from datetime import datetime, timedelta
from backend.db import get_supabase

def _get_peso_grupo(grupo_nome):
    if "Conhecimentos Específicos" in str(grupo_nome):
        return 2.5
    return 1.0

def inicializar_itens(user_id):
    supabase = get_supabase()
    item_resp = supabase.table("itens_estudo").select("id").execute().data
    aprendizado_resp = supabase.table("aprendizado_item").select("item_id").eq("user_id", user_id).execute().data
    
    existentes = {a["item_id"] for a in aprendizado_resp}
    
    novos = []
    for s in item_resp:
        if s["id"] not in existentes:
            novos.append({
                "user_id": user_id,
                "item_id": s["id"],
                "status": "NOVO"
            })
            existentes.add(s["id"])
            
    if novos:
        # Em lotes se for mt grande
        for i in range(0, len(novos), 50):
            supabase.table("aprendizado_item").insert(novos[i:i+50]).execute()

def calcular_prioridade(user_id, item_id):
    supabase = get_supabase()
    resp = supabase.table("aprendizado_item").select("*, itens_estudo!inner(subgrupos!inner(grupos!inner(nome)))").eq("user_id", user_id).eq("item_id", item_id).execute().data
    
    if not resp:
        return 0.0
        
    row = resp[0]
    grupo_nome = row['itens_estudo']['subgrupos']['grupos']['nome']
    peso = _get_peso_grupo(grupo_nome)
    
    ult_rev_str = row.get('ultima_revisao')
    if ult_rev_str:
        try:
            ultima_rev = datetime.fromisoformat(ult_rev_str.replace("Z", "+00:00")).replace(tzinfo=None)
            dias_sem_revisao = max(1.0, (datetime.now() - ultima_rev).days)
        except:
            dias_sem_revisao = 1.0
    else:
        dias_sem_revisao = 1.0
        
    tx_acerto = float(row.get('taxa_acerto', 0.0)) / 100.0 if row.get('taxa_acerto', 0.0) > 0 else 0.0
    fator_erro = max(0.1, 1.0 - tx_acerto)
    
    fator_dificuldade = float(row.get('fator_dificuldade', 1.0))
    
    prioridade = peso * dias_sem_revisao * fator_erro * fator_dificuldade
    
    supabase.table("aprendizado_item").update({"prioridade": prioridade}).eq("user_id", user_id).eq("item_id", item_id).execute()
    return prioridade

def agendar_revisao(user_id, item_id, acertou=True):
    supabase = get_supabase()
    steps = [1, 3, 7, 15, 30, 60]
    
    resp = supabase.table("aprendizado_item").select("numero_revisoes, status").eq("user_id", user_id).eq("item_id", item_id).execute().data
    if not resp: return
    
    numero_revisoes = resp[0].get('numero_revisoes', 0)
    status = resp[0].get('status', 'NOVO')
    
    if not acertou:
        novo_num_revisoes = max(0, numero_revisoes - 2)
        novo_status = 'REVISAO_1' if novo_num_revisoes > 0 else 'RETENCAO_INICIAL'
    else:
        novo_num_revisoes = numero_revisoes + 1
        if novo_num_revisoes == 1: novo_status = 'REVISAO_1'
        elif novo_num_revisoes == 2: novo_status = 'REVISAO_2'
        elif novo_num_revisoes >= 3: novo_status = 'REVISAO_3'
        else: novo_status = status
        
    idx_dias = min(novo_num_revisoes, len(steps)-1)
    dias_para_frente = steps[idx_dias]
    
    agora = datetime.utcnow()
    proxima = agora + timedelta(days=dias_para_frente)
    
    supabase.table("aprendizado_item").update({
        "numero_revisoes": novo_num_revisoes,
        "status": novo_status,
        "ultima_revisao": agora.isoformat(),
        "proxima_revisao": proxima.isoformat()
    }).eq("user_id", user_id).eq("item_id", item_id).execute()
    
    atualizar_dominio(user_id, item_id)
    calcular_prioridade(user_id, item_id)

def atualizar_dominio(user_id, item_id):
    supabase = get_supabase()
    resp = supabase.table("aprendizado_item").select("questoes_respondidas, taxa_acerto, numero_revisoes, ultima_revisao, dominado").eq("user_id", user_id).eq("item_id", item_id).execute().data
    if not resp: return
    
    row = resp[0]
    q_resp = row.get('questoes_respondidas', 0)
    tx = row.get('taxa_acerto', 0.0)
    n_rev = row.get('numero_revisoes', 0)
    ult_rev = row.get('ultima_revisao')
    dominado = row.get('dominado', False)
    
    novo_status = None
    data_dom = None
    
    if q_resp >= 10 and tx >= 90.0 and n_rev >= 3: # Reduzimos para 10 questoes pois é granular (por item)
        if ult_rev:
            try:
                dt_ult = datetime.fromisoformat(ult_rev.replace("Z", "+00:00")).replace(tzinfo=None)
                diff_days = (datetime.utcnow() - dt_ult).days
                if diff_days <= 30:
                    dominado = True
                    novo_status = 'DOMINADO'
                    data_dom = datetime.utcnow().isoformat()
            except: pass
            
    updates = {}
    if dominado and novo_status == 'DOMINADO':
        updates["dominado"] = True
        updates["status"] = novo_status
        updates["data_dominio"] = data_dom
        
    nivel = min(100, int((tx * 0.5) + (min(q_resp, 10) / 10.0 * 25) + (min(n_rev, 3) / 3.0 * 25)))
    if dominado: nivel = 100
    updates["nivel_dominio"] = nivel
    
    supabase.table("aprendizado_item").update(updates).eq("user_id", user_id).eq("item_id", item_id).execute()

def processar_resposta(user_id, questao_id, acertou):
    supabase = get_supabase()
    resp_q = supabase.table("questoes").select("item_id").eq("id", questao_id).execute().data
    if not resp_q or not resp_q[0].get('item_id'): 
        return # Caso a questão não tenha item_id associado, não processa
    
    item_id = resp_q[0]['item_id']
    
    resp_a = supabase.table("aprendizado_item").select("questoes_respondidas, questoes_corretas, status").eq("user_id", user_id).eq("item_id", item_id).execute().data
    if not resp_a:
        inicializar_itens(user_id)
        resp_a = supabase.table("aprendizado_item").select("questoes_respondidas, questoes_corretas, status").eq("user_id", user_id).eq("item_id", item_id).execute().data
        if not resp_a: return
        
    row = resp_a[0]
    q_resp = row.get('questoes_respondidas', 0)
    q_corretas = row.get('questoes_corretas', 0)
    status = row.get('status', 'NOVO')
    
    q_resp += 1
    if acertou:
        q_corretas += 1
        
    tx_acerto = (q_corretas / q_resp) * 100.0
    
    if tx_acerto >= 80: fd = 0.5
    elif tx_acerto >= 60: fd = 0.8
    elif tx_acerto >= 40: fd = 1.2
    elif tx_acerto >= 20: fd = 1.5
    else: fd = 2.0
    
    agora = datetime.utcnow().isoformat()
    
    supabase.table("aprendizado_item").update({
        "questoes_respondidas": q_resp,
        "questoes_corretas": q_corretas,
        "taxa_acerto": tx_acerto,
        "fator_dificuldade": fd,
        "ultima_revisao": agora
    }).eq("user_id", user_id).eq("item_id", item_id).execute()
    
    if status in ['NOVO', 'RECONHECIMENTO']:
        avancar_status(user_id, item_id, 'RETENCAO_INICIAL')
    elif status.startswith('REVISAO') or status == 'RETENCAO_INICIAL':
        agendar_revisao(user_id, item_id, acertou)
        
    atualizar_dominio(user_id, item_id)
    calcular_prioridade(user_id, item_id)

def avancar_status(user_id, item_id, novo_status):
    supabase = get_supabase()
    agora = datetime.utcnow().isoformat()
    updates = {"status": novo_status}
    if novo_status == 'RECONHECIMENTO':
        updates["data_primeiro_estudo"] = agora
        
    supabase.table("aprendizado_item").update(updates).eq("user_id", user_id).eq("item_id", item_id).execute()

def gravar_resumo(user_id, item_id, texto_bullets):
    supabase = get_supabase()
    supabase.table("aprendizado_item").update({"resumo_bullets": texto_bullets}).eq("user_id", user_id).eq("item_id", item_id).execute()

def get_resumo(user_id, item_id):
    supabase = get_supabase()
    resp = supabase.table("aprendizado_item").select("resumo_bullets").eq("user_id", user_id).eq("item_id", item_id).execute().data
    if resp and resp[0].get('resumo_bullets'):
        return resp[0]['resumo_bullets']
    return ""

def montar_plano_diario(user_id):
    inicializar_itens(user_id)
    supabase = get_supabase()
    
    # Recalcular prioridades
    resp_ids = supabase.table("aprendizado_item").select("item_id").eq("user_id", user_id).execute().data
    for s in resp_ids:
        calcular_prioridade(user_id, s['item_id'])
        
    df_todos_raw = supabase.table("aprendizado_item").select("*, itens_estudo!inner(nome, subgrupos!inner(nome, grupos!inner(nome)))").eq("user_id", user_id).execute().data
    
    data_list = []
    for a in df_todos_raw:
        if a.get('itens_estudo') and a['itens_estudo'].get('subgrupos'):
            if a['itens_estudo']['subgrupos']['grupos']['nome'] != 'Não Classificado':
                a['item_nome'] = a['itens_estudo']['nome']
                a['subgrupo_nome'] = a['itens_estudo']['subgrupos']['nome']
                a['grupo_nome'] = a['itens_estudo']['subgrupos']['grupos']['nome']
                del a['itens_estudo']
                data_list.append(a)
                
    df_todos = pd.DataFrame(data_list)
    if df_todos.empty:
        return [], []
        
    hoje = datetime.utcnow().replace(tzinfo=None)
    
    df_novos = df_todos[df_todos['status'].isin(['NOVO', 'RECONHECIMENTO'])]
    df_novos = df_novos.sort_values(by='prioridade', ascending=False).head(2)
    lista_novos = df_novos.to_dict('records')
    
    df_revs = df_todos[~df_todos['status'].isin(['NOVO', 'RECONHECIMENTO', 'DOMINADO', 'IGNORADO'])]
    
    def is_due(dt_str):
        if not dt_str: return True
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None) <= hoje
        except:
            return True
            
    if df_revs.empty:
        lista_revs = []
    else:
        df_revs = df_revs[df_revs['proxima_revisao'].apply(is_due)]
        df_revs = df_revs.sort_values(by='prioridade', ascending=False).head(5)
        lista_revs = df_revs.to_dict('records')
        
    return lista_novos, lista_revs
