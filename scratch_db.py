import os
import json
import traceback
from dotenv import load_dotenv

try:
    from supabase import create_client
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Sign in with service role or admin email? No, the `.env` has no service role.
    # But I can sign in with `cydy.potter@gmail.com` using password `concurseiro123`? 
    # Or just `test_beljqx@example.com`
    # But RLS on aprendizado_item restricts viewing to user_id = auth.uid()!
    # Ah! "aprendizado_item" has RLS: `auth.uid() = user_id`.
    pass
except Exception as e:
    pass
