import os
import sqlite3
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def migrate():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    email = input("Digite seu email do Supabase: ")
    senha = input("Digite sua senha do Supabase: ")
    
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        user_id = res.user.id
        print(f"✅ Logado com sucesso! User ID: {user_id}")
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return

    DB_PATH = "data/bancos/db_novo.sqlite"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    
    print("🧹 Limpando dados antigos da nuvem (via cascade)...")
    try:
        supabase.table("respostas").delete().neq("id", 0).execute()
        supabase.table("aprendizado_item").delete().neq("id", 0).execute()
        supabase.table("questoes").delete().neq("id", 0).execute()
        supabase.table("itens_estudo").delete().neq("id", 0).execute()
        supabase.table("subgrupos").delete().neq("id", 0).execute()
        supabase.table("grupos").delete().neq("id", 0).execute()
    except Exception as e:
        print(f"Aviso ao limpar: {e}")


    # 1. Grupos
    print("⏳ Migrando Grupos...")
    grupos_locais = cur.execute("SELECT * FROM grupos").fetchall()
    
    grupos_supa = supabase.table("grupos").select("*").execute().data
    grupo_nome_para_id_supa = {g["nome"]: g["id"] for g in grupos_supa}
    
    grupo_id_map = {} # map old_id -> new_id
    for g in grupos_locais:
        nome = g["nome"]
        if nome in grupo_nome_para_id_supa:
            grupo_id_map[g["id"]] = grupo_nome_para_id_supa[nome]
        else:
            data = {"nome": nome}
            resp = supabase.table("grupos").insert(data).execute()
            grupo_id_map[g["id"]] = resp.data[0]["id"]
    print(f"✅ {len(grupos_locais)} grupos processados.")

    # 2. Subgrupos
    print("⏳ Migrando Subgrupos...")
    subgrupos_locais = cur.execute("SELECT * FROM subgrupos").fetchall()
    
    subgrupos_supa = supabase.table("subgrupos").select("*").execute().data
    sub_chave_para_id_supa = {f'{s["grupo_id"]}_{s["nome"]}': s["id"] for s in subgrupos_supa}
    
    subgrupo_id_map = {}
    for s in subgrupos_locais:
        grupo_id_supa = grupo_id_map[s["grupo_id"]] if s["grupo_id"] in grupo_id_map else None
        chave = f'{grupo_id_supa}_{s["nome"]}'
        
        if chave in sub_chave_para_id_supa:
            subgrupo_id_map[s["id"]] = sub_chave_para_id_supa[chave]
        else:
            data = {
                "grupo_id": grupo_id_supa,
                "nome": s["nome"],
                "peso": int(float(s["peso"])) if s["peso"] is not None else 1
            }
            resp = supabase.table("subgrupos").insert(data).execute()
            subgrupo_id_map[s["id"]] = resp.data[0]["id"]
    print(f"✅ {len(subgrupos_locais)} subgrupos processados.")

    # 2.5 Itens de Estudo
    print("⏳ Migrando Itens de Estudo...")
    itens_locais = cur.execute("SELECT * FROM itens_estudo").fetchall()
    
    item_id_map = {}
    primeiro_item_por_subgrupo_supa = {} # Para atribuir questoes depois
    
    batch_size = 50
    for s in itens_locais:
        sub_supa = subgrupo_id_map.get(s["subgrupo_id"])
        if sub_supa:
            data = {
                "subgrupo_id": sub_supa,
                "nome": s["nome"]
            }
            resp = supabase.table("itens_estudo").insert(data).execute()
            novo_id = resp.data[0]["id"]
            item_id_map[s["id"]] = novo_id
            
            if sub_supa not in primeiro_item_por_subgrupo_supa:
                primeiro_item_por_subgrupo_supa[sub_supa] = novo_id

    print(f"✅ {len(itens_locais)} itens processados.")

    # 3. Questoes
    print("⏳ Migrando Questoes...")
    questoes = cur.execute("SELECT * FROM questoes").fetchall()
    questao_id_map = {}
    
    # Criar item_estudo "Geral" para subgrupos que não têm itens
    # assim as questoes não ficam orfãs se o subgrupo não teve itens extraídos
    for sub_supa_id in subgrupo_id_map.values():
        if sub_supa_id not in primeiro_item_por_subgrupo_supa:
            resp = supabase.table("itens_estudo").insert({"subgrupo_id": sub_supa_id, "nome": "Tópicos Gerais"}).execute()
            primeiro_item_por_subgrupo_supa[sub_supa_id] = resp.data[0]["id"]

    
    # Fetch all valid item_ids from Supabase just to be safe
    valid_itens = set(x['id'] for x in supabase.table("itens_estudo").select("id").execute().data)

    for i in range(0, len(questoes), batch_size):
        batch = questoes[i:i+batch_size]
        batch_data = []
        for q in batch:
            old_subgrupo_id = q["subgrupo_id"]
            new_subgrupo_id = subgrupo_id_map.get(old_subgrupo_id)
            
            # Tenta pegar o item_id direto se a questao ja tiver
            q_item_id = q["item_id"] if "item_id" in q.keys() else None
            new_item_id = None
            
            if q_item_id and q_item_id in item_id_map:
                new_item_id = item_id_map[q_item_id]
            else:
                # Fallback: atribui a questao ao primeiro item do subgrupo dela
                if new_subgrupo_id in primeiro_item_por_subgrupo_supa:
                    new_item_id = primeiro_item_por_subgrupo_supa[new_subgrupo_id]
            
            if new_item_id is not None:
                if new_item_id not in valid_itens:
                    print(f"Aviso: questao referenciando item_id {new_item_id} que nao existe no Supabase. Ignorando...")
                    continue
                batch_data.append({
                    "item_id": new_item_id,
                    "banca": q["banca"],
                    "ano": q["ano"],
                    "dificuldade": q["dificuldade"],
                    "enunciado": q["enunciado"],
                    "alternativa_a": q["alternativa_a"],
                    "alternativa_b": q["alternativa_b"],
                    "alternativa_c": q["alternativa_c"],
                    "alternativa_d": q["alternativa_d"],
                    "alternativa_e": q["alternativa_e"],
                    "gabarito": q["gabarito"]
                })
        
        if batch_data:
            resp = supabase.table("questoes").insert(batch_data).execute()
            for j, new_q in enumerate(resp.data):
                old_id = batch[j]["id"]
                questao_id_map[old_id] = new_q["id"]
        print(f"   Processadas {len(batch)} questões...")
    print(f"✅ {len(questoes)} questoes migradas.")

    # 4. Respostas (Private - requires user_id)
    print("⏳ Migrando Respostas...")
    respostas = cur.execute("SELECT * FROM respostas").fetchall()
    batch_data = []
    for r in respostas:
        if r["questao_id"] in questao_id_map:
            batch_data.append({
                "user_id": user_id,
                "questao_id": questao_id_map[r["questao_id"]],
                "acertou": r["acertou"],
                "tempo_segundos": r["tempo_segundos"],
                "data": r["data"]
            })
    if batch_data:
        for i in range(0, len(batch_data), batch_size):
            supabase.table("respostas").insert(batch_data[i:i+batch_size]).execute()
    print(f"✅ {len(batch_data)} respostas migradas.")

    # 5. Aprendizado Item (Estatísticas)
    print("⏳ Migrando Estatísticas de Aprendizado...")
    aprendizado = cur.execute("SELECT * FROM aprendizado_item").fetchall()
    
    aprendizado_supa = supabase.table("aprendizado_item").select("item_id").eq("user_id", user_id).execute().data
    itens_ids_existentes = {a["item_id"] for a in aprendizado_supa}
    
    batch_data = []
    for a in aprendizado:
        if a["item_id"] in item_id_map:
            new_item_id = item_id_map[a["item_id"]]
            if new_item_id not in itens_ids_existentes:
                batch_data.append({
                    "user_id": user_id,
                    "item_id": new_item_id,
                    "status": a["status"],
                    "nivel_dominio": int(float(a["nivel_dominio"])) if a["nivel_dominio"] is not None else 0,
                    "data_primeiro_estudo": a["data_primeiro_estudo"],
                    "ultima_revisao": a["ultima_revisao"],
                    "proxima_revisao": a["proxima_revisao"],
                    "numero_revisoes": int(float(a["numero_revisoes"])) if a["numero_revisoes"] is not None else 0,
                    "tempo_total_estudo": int(float(a["tempo_total_estudo"])) if a["tempo_total_estudo"] is not None else 0,
                    "questoes_respondidas": int(float(a["questoes_respondidas"])) if a["questoes_respondidas"] is not None else 0,
                    "questoes_corretas": int(float(a["questoes_corretas"])) if a["questoes_corretas"] is not None else 0,
                    "taxa_acerto": a["taxa_acerto"],
                    "fator_dificuldade": a["fator_dificuldade"],
                    "prioridade": a["prioridade"],
                    "dominado": bool(a["dominado"]),
                    "data_dominio": a["data_dominio"],
                    "resumo_bullets": a["resumo_bullets"]
                })
                itens_ids_existentes.add(new_item_id)
                
    if batch_data:
        for i in range(0, len(batch_data), batch_size):
            supabase.table("aprendizado_item").insert(batch_data[i:i+batch_size]).execute()
    print(f"✅ {len(batch_data)} estatisticas migradas.")

    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")

if __name__ == "__main__":
    migrate()
