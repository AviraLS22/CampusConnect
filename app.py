import streamlit as st
from supabase import create_client, Client
from datetime import date
from config import validate_leader
from qa_chain import ask_question
from speech_to_text import transcribe_audio
from auth import sign_up, login
from dotenv import load_dotenv
import calendar
import datetime
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

SUPABASE_URL = "https://outnepujxzreneyifzpd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91dG5lcHVqeHpyZW5leWlmenBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMDQ4MjQsImV4cCI6MjA2MzU4MDgyNH0.5rjTX5v4ISJiWdA2KqssQWANa2X8j9gQ9QWnMjhzJuI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
VECTORSTORE_DIR = "vectorstore_index"
embeddings = OpenAIEmbeddings()



index_path = os.path.join(VECTORSTORE_DIR, "index.faiss")

if os.path.exists(index_path):
    vectorstore = FAISS.load_local(VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True)
else:
    # Create an empty FAISS index with dummy doc to avoid IndexError
    from langchain_core.documents import Document
    dummy_doc = Document(page_content="dummy content", metadata={"source": "init"})
    vectorstore = FAISS.from_documents([dummy_doc], embeddings)
    vectorstore.save_local(VECTORSTORE_DIR)
    # Delete dummy doc after saving to start clean
    vectorstore = FAISS.load_local(VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True)



for key, default in {
    "logged_in": False,
    "user_email": "",
    "club_leader_validated": False,
    "admin_mode": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def embed_and_store_event(name, description, event_date):
    content = f"Event Name: {name}\nDate: {event_date}\nDescription: {description}"
    metadata = {"name": name, "date": event_date}
    doc = Document(page_content=content, metadata=metadata)
    vectorstore.add_documents([doc])
    vectorstore.save_local(VECTORSTORE_DIR)

def show_login_signup():
    st.subheader("Admin Login or Signup")
    choice = st.radio("Choose Action:", ["Sign Up", "Login"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button(choice):
        if choice == "Sign Up":
            result = sign_up(email, password)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Signed up successfully! Please log in.")
        else:
            result = login(email, password)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Logged in successfully!")
                st.rerun()

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
    st.header("📤 Upload New Event")
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
            if hasattr(insert_resp, "error") and insert_resp.error:
                st.error(f"Error inserting event: {insert_resp.error.message}")
            else:
                st.success(f"Event '{name}' added successfully!")
                # Embed into vectorstore
                embed_and_store_event(name, description, event_date.isoformat())

def show_event_upload_section():
    st.subheader("🔐 Admin Upload Portal")
    if "show_upload_form" not in st.session_state:
        st.session_state.show_upload_form = False
    if st.button("Upload Upcoming Event"):
        st.session_state.show_upload_form = True
    if not st.session_state.logged_in:
        show_login_signup()
        return
    if st.session_state.show_upload_form:
        if not st.session_state.club_leader_validated:
            with st.form("validate_form"):
                email = st.text_input("Club Leader Email")
                code = st.text_input("Unique Club Code")
                validate_submitted = st.form_submit_button("Validate")
                if validate_submitted:
                    if validate_leader(email, code):
                        st.session_state.club_leader_validated = True
                        st.success("Club access validated! You may now upload events.")
                    else:
                        st.error("Invalid email or club code. Access denied.")
        else:
            st.success("Access granted.")
            upload_event_form()

def fetch_events():
    response = supabase.table("events").select("*").order("date", desc=False).execute()
    if hasattr(response, "error") and response.error:
        st.error(f"Error fetching events: {response.error.message}")
        return []
    return response.data or []

def show_calendar(events):
    st.header("📅 Upcoming Events Calendar")
    events_by_date = {}
    for e in events:
        events_by_date.setdefault(e["date"], []).append(e)
    today = datetime.date.today()
    year, month = today.year, today.month
    cal = calendar.monthcalendar(year, month)
    st.write(f"### {calendar.month_name[month]} {year}")
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.write("")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    st.markdown(f"**{day}**")
                    if date_str in events_by_date:
                        for event in events_by_date[date_str]:
                            st.markdown(f"- {event['name']}")

def ask_event_question(query):
    if not query:
        return "Please ask a valid question."
    results = vectorstore.similarity_search(query, k=2)
    if not results:
        return "No relevant event found."
    return results[0].page_content

def show_chatbot():
    st.header("🎓 SITus AI Chatbot")
    query = st.text_input("Ask a question:")
    use_voice = st.button("🎙️ Use Voice Input")
    if use_voice:
        with st.spinner("Listening..."):
            query = transcribe_audio()
    if query:
        with st.spinner("Searching..."):
            answer = ask_event_question(query)
            st.write("💡", answer)

st.title("SITus AI 🎓")
events = fetch_events()
show_calendar(events)
st.markdown("---")
show_chatbot()
st.markdown("---")

with st.expander("🔑 Admin: Upload Upcoming Event"):
    if not st.session_state.admin_mode:
        if st.button("Enter Admin Mode"):
            st.session_state.admin_mode = True
            st.rerun()
    else:
        show_event_upload_section()
        if st.sidebar.button("Logout Admin"):
            for key in ["logged_in", "user_email", "club_leader_validated", "admin_mode"]:
                st.session_state[key] = False
            st.rerun()
