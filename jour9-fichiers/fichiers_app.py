import streamlit as st
import pandas as pd
import anthropic
import fitz
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Analyse Fichiers", page_icon="📊", layout="wide")
st.title("📊 Analyse de fichiers avec Claude")

client = anthropic.Anthropic()

# --- SIDEBAR : Upload ---
st.sidebar.header("📁 Upload")
file_type = st.sidebar.radio("Type de fichier", ["Excel/CSV", "PDF"])

uploaded_file = None
if file_type == "Excel/CSV":
    uploaded_file = st.sidebar.file_uploader("Upload", type=["csv", "xlsx"])
else:
    uploaded_file = st.sidebar.file_uploader("Upload", type=["pdf"])

# --- TRAITEMENT DU FICHIER ---
if uploaded_file and "file_data" not in st.session_state:
    with st.spinner("Lecture du fichier..."):
        if file_type == "Excel/CSV":
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.session_state.file_data = df.to_string()
            st.session_state.df = df
            st.session_state.file_type = "tableau"

        else:  # PDF
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texte = ""
            for page in doc:
                texte += page.get_text()
            doc.close()

            st.session_state.file_data = texte
            st.session_state.file_type = "pdf"

    st.sidebar.success("✅ Fichier chargé !")

# --- AFFICHAGE DES DONNÉES ---
if "file_data" in st.session_state:
    with st.expander("📋 Aperçu du fichier", expanded=True):
        if st.session_state.file_type == "tableau":
            st.dataframe(st.session_state.df, use_container_width=True)
        else:
            st.text(st.session_state.file_data[:2000])

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Pose ta question sur le fichier..."):
    if "file_data" not in st.session_state:
        st.warning("⬅️ Upload un fichier d'abord !")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=f"""Tu es un assistant comptable expert.
Analyse ce fichier et réponds aux questions.
Sois précis avec les chiffres. Réponds en français.

CONTENU DU FICHIER :
{st.session_state.file_data}""",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.content[0].text
                st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

# --- BOUTON RESET ---
if st.sidebar.button("🔄 Nouveau fichier"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()