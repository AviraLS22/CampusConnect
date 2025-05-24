import streamlit as st
from auth import sign_up, login

st.title("Admin Authentication")

choice = st.radio("Choose Action:", ["Sign Up", "Login"])

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button(choice):
    if choice == "Sign Up":
        result = sign_up(email, password)
        if 'error' in result:
            st.error(result['error'])
        else:
            st.success("Signed up successfully! Please log in.")
    else:
        result = login(email, password)
        if 'error' in result:
            st.error(result['error'])
        else:
            st.success("Logged in successfully!")
            