import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

email = "test_beljqx@example.com"
password = "TestPassword123!"

try:
    print("Signing in...")
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print("Signed in")
    user_id = res.user.id
    
    resp_a = supabase.table("aprendizado_item").select("*").eq("user_id", user_id).execute().data
    print(f"aprendizado_item count: {len(resp_a)}")
    
    resp_g = supabase.table("grupos").select("nome").execute().data
    print(f"grupos count: {len(resp_g)}")
    
except Exception as e:
    print(f"Error: {e}")

