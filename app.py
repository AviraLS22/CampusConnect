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
   
    from langchain_core.documents import Document
    dummy_doc = Document(page_content="dummy content", metadata={"source": "init"})
    vectorstore = FAISS.from_documents([dummy_doc], embeddings)
    vectorstore.save_local(VECTORSTORE_DIR)
   
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

st.markdown(
    """
    <style>
    .sit-title {
        font-size: 48px;
        font-weight: 700;
        color: #f0f8ff;
        text-align: center;
        margin-bottom: 0.3em;
    }
    .sit-subtitle {
        font-size: 20px;
        color: #f0f8ff;
        text-align: center;
        margin-bottom: 2em;
    }
    .event-card {
        background-color: #444;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4b9cd3;
        margin-bottom: 1rem;
    }
    </style>
    <div class='sit-title'>SITus AI 🎓</div>
    <div class='sit-subtitle'>Your Smart Campus Companion – Ask Questions, View Events, Stay Updated.</div>
    """,
    unsafe_allow_html=True
)


def show_calendar(events):
    st.header("📅 Upcoming Events Calendar")
    st.markdown("Browse upcoming events below. Select a month to filter.")

    events_by_date = {}
    for e in events:
        events_by_date.setdefault(e["date"], []).append(e)

    selected_date = st.date_input("Select Month", datetime.date.today())
    year, month = selected_date.year, selected_date.month

    # CSS for portrait cards
    st.markdown("""
        <style>
        .event-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
        }
        .event-card {
            background-color: #f9f9f9;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 1rem;
            width: 200px;
            text-align: center;
        }
        .event-card img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 8px;
        }
        .event-card h4 {
            margin-top: 0.5rem;
            font-size: 1.1rem;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    for date_str in sorted(events_by_date):
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if event_date.year == year and event_date.month == month:
            st.markdown(f"### 📆 {event_date.strftime('%B %d, %Y')}")
            st.markdown("<div class='event-grid'>", unsafe_allow_html=True)

            for event in events_by_date[date_str]:
                st.markdown(f"""
                    <div class='event-card'>
                        <img src="{event['image_url']}" alt="Event Image"/>
                        <h4>{event['name']}</h4>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

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
            try:
                answer = ask_question(query)
                if not answer or answer.strip() == "":
                   
                    answer = ask_event_question(query)
            except Exception as e:
                st.error("Error fetching answer from PDFs. Falling back to events DB.")
                answer = ask_event_question(query)

            st.write("💡", answer)


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


def show_feedback_form():
    st.header("💬 Feedback Form")
    st.markdown("We'd love to hear from you! Share your experience or suggestions.")

    with st.form("feedback_form"):
        name = st.text_input("Your Name (optional)")
        email = st.text_input("Email (optional)")
        message = st.text_area("Feedback", max_chars=500)
        rating = st.slider("How would you rate your experience?", 1, 5, 3)
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            if not message.strip():
                st.error("Feedback message is required.")
                return

            response = supabase.table("feedback").insert({
                "name": name,
                "email": email,
                "message": message,
                "rating": rating
            }).execute()

            if hasattr(response, "error") and response.error:
                st.error(f"Error submitting feedback: {response.error.message}")
            else:
                st.success("Thanks for your feedback!")

st.markdown("---")
with st.expander("💡 Leave a Feedback"):
    show_feedback_form()


