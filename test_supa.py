import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

grupos_remover = ["LÍNGUA INGLESA"]
resp = supabase.table("itens_estudo").select("id, subgrupos!inner(grupos!inner(nome))").in_("subgrupos.grupos.nome", grupos_remover).execute()
ids = [r['id'] for r in resp.data]
print(f"Encontrou {len(ids)} itens para remover")
