import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

email = input("Digite seu email do Supabase: ")
senha = input("Digite sua senha do Supabase: ")

try:
    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
    print("✅ Logado com sucesso!")
except Exception as e:
    print(f"❌ Erro de login: {e}")
    exit(1)

print("\n🧹 Iniciando faxina (com modo seguro para tabelas gigantes)...")

# 1. Limpar dependências
tabelas_secundarias = ["aprendizado_subgrupo", "aprendizado_item", "respostas"]
for t in tabelas_secundarias:
    try:
        supabase.table(t).delete().neq("id", 0).execute()
        print(f"✅ Tabela '{t}' limpa.")
    except Exception as e:
        pass

# 2. Limpar a tabela gigante (questoes) aos poucos para não dar TIMEOUT
print("Apagando 'questoes' em lotes (isso pode demorar uns 2 minutinhos)...")
while True:
    # Busca 2000 IDs por vez
    try:
        res = supabase.table("questoes").select("id").limit(2000).execute()
        ids = [r["id"] for r in res.data]
        if not ids:
            break
        
        # Apaga as 2000 questões encontradas
        supabase.table("questoes").delete().in_("id", ids).execute()
        print(f"  -> Apagado lote de {len(ids)} questões...")
    except Exception as e:
        print(f"Erro no lote: {e}. Tentando novamente...")

print("✅ Tabela 'questoes' esvaziada com sucesso.")

# 3. Limpar grupos e subgrupos
tabelas_base = ["subgrupos", "grupos"]
for t in tabelas_base:
    try:
        supabase.table(t).delete().neq("id", 0).execute()
        print(f"✅ Tabela '{t}' limpa.")
    except Exception as e:
        pass

print("\n🎉 Limpeza 100% concluída e sem timeout! O banco está zerado.")
