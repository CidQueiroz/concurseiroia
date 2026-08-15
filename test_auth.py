import os
import random
import string
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Create a random user
rand_str = ''.join(random.choices(string.ascii_lowercase, k=6))
email = f"test_{rand_str}@example.com"
password = "TestPassword123!"

try:
    print(f"Creating user {email}...")
    res = supabase.auth.sign_up({"email": email, "password": password})
    print("Sign up success.")
    
    # Try reading grupos
    resp_g = supabase.table("grupos").select("*").execute().data
    print(f"Count of grupos for new auth user: {len(resp_g)}")
    
except Exception as e:
    print(f"Error: {e}")

