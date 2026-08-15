import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# list users
resp = supabase.auth.admin.list_users()
users = resp.users
if not users:
    print("No users")
else:
    # get latest user
    users.sort(key=lambda u: u.created_at, reverse=True)
    new_user = users[0]
    print(f"Latest user: {new_user.email} (ID: {new_user.id})")
    
    # check aprendizado_item
    resp_ai = supabase.table("aprendizado_item").select("*").eq("user_id", new_user.id).execute().data
    print(f"Count of aprendizado_item for new user: {len(resp_ai)}")
    
    # check grupos read access with that user's token? We can't easily without their password.
    # but let's see if we can select grupos normally with service key
    resp_g = supabase.table("grupos").select("*").execute().data
    print(f"Count of grupos with service key: {len(resp_g)}")
