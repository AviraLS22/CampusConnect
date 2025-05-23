import qrcode
from PIL import Image
import streamlit as st

def generate_qr(link: str):
    qr = qrcode.make(link)
    st.image(qr, caption="Scan to give feedback")
