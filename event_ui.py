import streamlit as st
from supabase import create_client, Client
from datetime import date
import io

# Initialize Supabase client - replace with your own URL and anon key
SUPABASE_URL = "https://outnepujxzreneyifzpd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91dG5lcHVqeHpyZW5leWlmenBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMDQ4MjQsImV4cCI6MjA2MzU4MDgyNH0.5rjTX5v4ISJiWdA2KqssQWANa2X8j9gQ9QWnMjhzJuI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image(image_file):
    file_bytes = image_file.read()
    storage_path = f"uploads/{image_file.name}"

    try:
        # This will raise an error if the upload fails
        supabase.storage.from_("events").upload(
            storage_path, file_bytes, {"cacheControl": "3600"}
        )

        # Get the public URL
        public_url = supabase.storage.from_("events").get_public_url(storage_path)
        return public_url

    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None


def main():
    st.title("Admin Event Upload")

    with st.form("event_form"):
        name = st.text_input("Event Name", max_chars=100)
        description = st.text_area("Event Description")
        event_date = st.date_input("Event Date", min_value=date.today())
        image_file = st.file_uploader("Upload Event Image", type=["png", "jpg", "jpeg"])

        submitted = st.form_submit_button("Add Event")

        if submitted:
            if not name or not event_date:
                st.error("Event Name and Date are required!")
                return

            # Upload image to storage
            image_url = upload_image(image_file)

            # Insert event into database
            data = {
                "name": name,
                "description": description,
                "date": event_date.isoformat(),
                "image_url": image_url,
            }

            insert_resp = supabase.table("events").insert(data).execute()

            if insert_resp.get("error"):
                st.error(f"Error inserting event: {insert_resp['error']['message']}")
            else:
                st.success(f"Event '{name}' added successfully!")

if __name__ == "__main__":
    main()
