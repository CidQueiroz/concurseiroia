import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# use the user we just created
email = "test_beljqx@example.com"
password = "TestPassword123!"

try:
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    
    resp_i = supabase.table("itens_estudo").select("id").execute().data
    print(f"Count of itens_estudo: {len(resp_i)}")
    
    resp_s = supabase.table("subgrupos").select("id").execute().data
    print(f"Count of subgrupos: {len(resp_s)}")
    
except Exception as e:
    print(f"Error: {e}")

