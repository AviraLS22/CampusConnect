import io
import qrcode
from PIL import Image
import streamlit as st

def generate_qr(link):
    qr = qrcode.make(link)
    
   
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)

    st.image(buf, caption="Scan to give feedback")
