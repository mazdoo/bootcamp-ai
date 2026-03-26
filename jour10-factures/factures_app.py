import streamlit as st
import fitz
import anthropic
import json
import pandas as pd
import time
import io
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Extracteur de factures", page_icon="🧾", layout="wide")
st.title("🧾 Extracteur de factures PDF")
st.write("Upload tes factures PDF et Claude extrait automatiquement toutes les donnees.")

client = anthropic.Anthropic(timeout=120.0)

PROMPT_EXTRACTION = """Tu es un assistant specialise dans l'extraction de donnees de factures.

Extrais les informations et retourne UNIQUEMENT un objet JSON valide :

{
    "numero_facture": "string",
    "date": "JJ/MM/AAAA",
    "fournisseur": "string",
    "client": "string",
    "lignes": [{"description": "string", "quantite": 0, "prix_unitaire": 0.00, "total_ligne": 0.00}],
    "total_ht": 0.00,
    "tva": 0.00,
    "total_ttc": 0.00,
    "echeance": "string ou null"
}

Montants en nombres, dates en JJ/MM/AAAA. Retourne UNIQUEMENT le JSON."""

def extraire_facture(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texte = ""
    for page in doc:
        texte += page.get_text()
    doc.close()

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=PROMPT_EXTRACTION,
        messages=[{"role": "user", "content": f"Facture :\n\n{texte}"}]
    )
    reponse_texte = response.content[0].text.strip()
    if reponse_texte.startswith("```"):
        reponse_texte = reponse_texte.split("\n", 1)[1]
    if reponse_texte.endswith("```"):
        reponse_texte = reponse_texte[:-3]
    reponse_texte = reponse_texte.strip()
    try:
        return json.loads(reponse_texte)
    except json.JSONDecodeError:
        return None

# --- Upload ---
uploaded_files = st.sidebar.file_uploader(
    "Upload tes factures PDF",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files and "resultats" not in st.session_state:
    st.session_state.resultats = []
    progress = st.progress(0)
    status = st.empty()

    for i, fichier in enumerate(uploaded_files):
        status.write(f"Extraction de {fichier.name}...")
        pdf_bytes = fichier.read()
        donnees = extraire_facture(pdf_bytes)
        if donnees:
            donnees["fichier_source"] = fichier.name
            st.session_state.resultats.append(donnees)
        progress.progress((i + 1) / len(uploaded_files))
        if i < len(uploaded_files) - 1:
            time.sleep(3)

    status.write(f"{len(st.session_state.resultats)} factures extraites !")

# --- Affichage des resultats ---
if "resultats" in st.session_state and st.session_state.resultats:
    resultats = st.session_state.resultats

    recap = []
    for r in resultats:
        recap.append({
            "N Facture": r["numero_facture"],
            "Date": r["date"],
            "Fournisseur": r["fournisseur"],
            "Client": r["client"],
            "Total HT": r["total_ht"],
            "TVA": r["tva"],
            "Total TTC": r["total_ttc"]
        })

    df = pd.DataFrame(recap)

    st.subheader("Recapitulatif")
    st.dataframe(df, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Factures traitees", len(df))
    col2.metric("Total HT", f"{df['Total HT'].sum():,.2f} euros")
    col3.metric("Total TTC", f"{df['Total TTC'].sum():,.2f} euros")

    st.subheader("Detail des lignes")
    for r in resultats:
        with st.expander(f"{r['numero_facture']} - {r['fournisseur']}"):
            for ligne in r["lignes"]:
                st.write(f"- {ligne['description']} : {ligne['quantite']} x {ligne['prix_unitaire']} = {ligne['total_ligne']} euros")

    st.subheader("Export")
    detail = []
    for r in resultats:
        for ligne in r["lignes"]:
            detail.append({
                "N Facture": r["numero_facture"],
                "Fournisseur": r["fournisseur"],
                "Description": ligne["description"],
                "Quantite": ligne["quantite"],
                "Prix unitaire": ligne["prix_unitaire"],
                "Total ligne": ligne["total_ligne"]
            })
    df_detail = pd.DataFrame(detail)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Recapitulatif", index=False)
        df_detail.to_excel(writer, sheet_name="Detail lignes", index=False)

    st.download_button(
        label="Telecharger l'Excel complet",
        data=buffer.getvalue(),
        file_name="factures_extraites.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Reset ---
if st.sidebar.button("Nouvelles factures"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()