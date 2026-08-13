import re

with open("modules/modo_prova.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix subgrupos multiselect to include itens
old_subgrupos = """            if subgrupos_opcoes:
                subgrupos_selecionados = st.multiselect("Selecione os Subgrupos (Deixe vazio para ver todos):", subgrupos_opcoes)"""
new_subgrupos = """            itens_selecionados = []
            if subgrupos_opcoes:
                subgrupos_selecionados = st.multiselect("Selecione os Subgrupos (Deixe vazio para ver todos):", subgrupos_opcoes)
                if subgrupos_selecionados:
                    resp_itens = supabase.table("itens_estudo").select("nome, subgrupos!inner(nome)").in_("subgrupos.nome", subgrupos_selecionados).execute()
                    itens_opcoes = [i["nome"] for i in resp_itens.data]
                    if itens_opcoes:
                        itens_selecionados = st.multiselect("Selecione os Itens de Estudo (Deixe vazio para ver todos):", itens_opcoes)"""
content = content.replace(old_subgrupos, new_subgrupos)

# Fix carregar_questoes_supabase signature
content = content.replace(
    "def carregar_questoes_supabase(tema=None, ineditas=True, subs=None):",
    "def carregar_questoes_supabase(tema=None, ineditas=True, subs=None, itens_filtro=None):"
)

# Fix carregar_questoes_supabase query
old_query = """        query = supabase.table("questoes").select("*, subgrupos!inner(nome, grupos!inner(nome))")
        if tema:
            query = query.eq("subgrupos.grupos.nome", tema)"""
new_query = """        query = supabase.table("questoes").select("*, itens_estudo!inner(nome, subgrupos!inner(nome, grupos!inner(nome)))")
        if tema:
            query = query.eq("itens_estudo.subgrupos.grupos.nome", tema)"""
content = content.replace(old_query, new_query)

# Fix flattening
old_flatten = """        for q in data:
            q['item_nome'] = q['subgrupos']['nome']
            q['grupo_nome'] = q['subgrupos']['grupos']['nome']
            del q['subgrupos']
            
        df = pd.DataFrame(data)
        if not df.empty and subs:
            df = df[df['item_nome'].isin(subs)]"""
new_flatten = """        for q in data:
            q['item_nome'] = q['itens_estudo']['nome']
            q['subgrupo_nome'] = q['itens_estudo']['subgrupos']['nome']
            q['grupo_nome'] = q['itens_estudo']['subgrupos']['grupos']['nome']
            del q['itens_estudo']
            
        df = pd.DataFrame(data)
        if not df.empty:
            if subs:
                df = df[df['subgrupo_nome'].isin(subs)]
            if itens_filtro:
                df = df[df['item_nome'].isin(itens_filtro)]"""
content = content.replace(old_flatten, new_flatten)

# Fix function call
content = content.replace(
    "df_questoes = carregar_questoes_supabase(tema_selecionado, ineditas_apenas, subgrupos_selecionados)",
    "df_questoes = carregar_questoes_supabase(tema_selecionado, ineditas_apenas, subgrupos_selecionados, itens_selecionados)"
)

with open("modules/modo_prova.py", "w", encoding="utf-8") as f:
    f.write(content)
