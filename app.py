import streamlit as st
from qa_chain import ask_question
from speech_to_text import transcribe_audio
from utils import generate_qr

st.title("🎓 Campus Connect AI")
st.subheader("Your Virtual College FAQ + Event Planner")

query = st.text_input("Ask a question:")
use_voice = st.button("🎙️ Use Voice Input")

if use_voice:
    with st.spinner("Listening..."):
        query = transcribe_audio()

if query:
    with st.spinner("Searching..."):
        answer = ask_question(query)
        st.write("💡", answer)

st.markdown("---")
st.markdown("### 📩 Feedback")
generate_qr("https://forms.gle/your-feedback-form")
