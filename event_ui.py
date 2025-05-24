import streamlit as st
from supabase import create_client, Client
from datetime import date
from config import validate_leader  # import validation
import io

SUPABASE_URL = "https://outnepujxzreneyifzpd.supabase.co"
SUPABASE_KEY = "your_supabase_key_here"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image(image_file):
    if image_file is None:
        return None
    file_bytes = image_file.read()
    storage_path = f"uploads/{image_file.name}"

    try:
        supabase.storage.from_("events").upload(storage_path, file_bytes, {"cacheControl": "3600"})
        public_url = supabase.storage.from_("events").get_public_url(storage_path)
        return public_url
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def upload_event_form():
    st.header("Upload New Event")

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

            image_url = upload_image(image_file)

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

def main():
    st.title("Admin Event Upload")

    if st.button("Upload Upcoming Event"):
        with st.form("validate_form"):
            email = st.text_input("Enter your club leader email")
            code = st.text_input("Enter your unique club code")
            validate_submitted = st.form_submit_button("Validate")

            if validate_submitted:
                if validate_leader(email, code):
                    st.success("Validated! You may now upload events.")
                    upload_event_form()
                else:
                    st.error("Invalid email or unique code. Access denied.")

if __name__ == "__main__":
    main()
