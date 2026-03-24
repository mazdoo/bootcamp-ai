import streamlit as st
import anthropic
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chatbot Claude", page_icon="💬")
st.title("💬 Chatbot Claude")

client = anthropic.Anthropic()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input utilisateur
if prompt := st.chat_input("Écris ton message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Claude réfléchit..."):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system="Tu es un assistant utile et concis. Réponds en français.",
                messages=st.session_state.messages
            )
            reply = response.content[0].text
            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})