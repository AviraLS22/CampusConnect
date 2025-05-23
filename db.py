from supabase import create_client, Client

# Supabase credentials
url: str = "https://outnepujxzreneyifzpd.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91dG5lcHVqeHpyZW5leWlmenBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMDQ4MjQsImV4cCI6MjA2MzU4MDgyNH0.5rjTX5v4ISJiWdA2KqssQWANa2X8j9gQ9QWnMjhzJuI"

# Create the Supabase client
supabase: Client = create_client(url, key)
