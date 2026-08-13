import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Instância única global para não criar múltiplas conexões atoa
_supabase = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is not None:
        return _supabase
        
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env")
    
    _supabase = create_client(url, key)
    return _supabase
