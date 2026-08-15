import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
print(f"Key starts with: {key[:15] if key else 'None'}")
supabase = create_client(url, key)

# list users
try:
    resp = supabase.auth.admin.list_users()
    users = resp.users
    if not users:
        print("No users")
    else:
        # get latest user
        users.sort(key=lambda u: u.created_at, reverse=True)
        new_user = users[0]
        print(f"Latest user: {new_user.email} (ID: {new_user.id})")
        
        # we will authenticate as this user if we had password, but we don't.
        # let's just fetch grupos with the current key
        resp_g = supabase.table("grupos").select("*").execute().data
        print(f"Count of grupos with current key: {len(resp_g)}")
except Exception as e:
    print(f"Error: {e}")
    resp_g = supabase.table("grupos").select("*").execute().data
    print(f"Count of grupos with current key (no admin auth): {len(resp_g)}")

