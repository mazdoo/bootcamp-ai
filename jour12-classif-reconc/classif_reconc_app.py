import streamlit as st
import fitz
import anthropic
import pandas as pd
import json
import io
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="BookKeeper AI", page_icon="📚", layout="wide")
st.title("📚 BookKeeper AI — Classification & Reconciliation")

client = anthropic.Anthropic(timeout=120.0)

tab1, tab2 = st.tabs(["📂 Classification", "🔄 Reconciliation"])

# ==========================================
# TAB 1 : CLASSIFICATION
# ==========================================
with tab1:
    st.header("Classification automatique de documents")

    uploaded_docs = st.file_uploader(
        "Upload tes documents",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="classif"
    )

    if uploaded_docs and st.button("Classifier les documents"):
        PROMPT_CLASSIF = """Analyse le document et retourne UNIQUEMENT un JSON :
{
    "type_document": "facture | devis | bon_de_commande | releve_bancaire | contrat | note_de_frais | autre",
    "confiance": 0.95,
    "fournisseur_ou_emetteur": "nom ou null",
    "date": "date ou null",
    "montant_principal": 0.00,
    "resume": "resume en une phrase"
}
Retourne UNIQUEMENT le JSON."""

        resultats = []
        progress = st.progress(0)

        for i, fichier in enumerate(uploaded_docs):
            st.write(f"Classification de {fichier.name}...")
            pdf_bytes = fichier.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texte = ""
            for page in doc:
                texte += page.get_text()
            doc.close()

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=PROMPT_CLASSIF,
                messages=[{"role": "user", "content": f"Document :\n\n{texte[:3000]}"}]
            )
            reponse_texte = response.content[0].text.strip()
            if reponse_texte.startswith("```"):
                reponse_texte = reponse_texte.split("\n", 1)[1]
            if reponse_texte.endswith("```"):
                reponse_texte = reponse_texte[:-3]
            try:
                data = json.loads(reponse_texte.strip())
                data["fichier"] = fichier.name
                resultats.append(data)
            except:
                pass

            progress.progress((i + 1) / len(uploaded_docs))
            if i < len(uploaded_docs) - 1:
                time.sleep(3)

        if resultats:
            df = pd.DataFrame(resultats)
            st.subheader("Resultats")
            st.dataframe(df[["fichier", "type_document", "confiance", "resume", "montant_principal"]], use_container_width=True)

            for r in resultats:
                with st.expander(f"{r['fichier']} -> {r['type_document']}"):
                    st.write(f"Emetteur : {r.get('fournisseur_ou_emetteur', 'N/A')}")
                    st.write(f"Date : {r.get('date', 'N/A')}")
                    st.write(f"Montant : {r.get('montant_principal', 'N/A')} EUR")
                    st.write(f"Resume : {r['resume']}")

# ==========================================
# TAB 2 : RECONCILIATION
# ==========================================
with tab2:
    st.header("Reconciliation de donnees")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fichier 1 (Journal)")
        file1 = st.file_uploader("Upload le journal comptable", type=["csv", "xlsx"], key="file1")

    with col2:
        st.subheader("Fichier 2 (Releve)")
        file2 = st.file_uploader("Upload le releve bancaire", type=["csv", "xlsx"], key="file2")

    if file1 and file2 and st.button("Lancer la reconciliation"):
        with st.spinner("Reconciliation en cours..."):
            # Charger les fichiers
            if file1.name.endswith(".csv"):
                journal = pd.read_csv(file1)
            else:
                journal = pd.read_excel(file1)

            if file2.name.endswith(".csv"):
                releve = pd.read_csv(file2)
            else:
                releve = pd.read_excel(file2)

            # Envoyer les deux fichiers a Claude pour analyse
            prompt = f"""Voici deux fichiers a reconcilier :

FICHIER 1 - JOURNAL COMPTABLE :
{journal.to_string(index=False)}

FICHIER 2 - RELEVE BANCAIRE :
{releve.to_string(index=False)}

Analyse ces deux fichiers et :
1. Identifie les ecritures qui correspondent entre les deux fichiers (par date et montant)
2. Liste les ecritures presentes dans le journal mais absentes du releve
3. Liste les operations presentes dans le releve mais absentes du journal
4. Calcule le solde de chaque fichier
5. Donne des recommandations

Formate ta reponse clairement avec des sections."""

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system="Tu es un expert comptable specialise en reconciliation bancaire. Reponds en francais.",
                messages=[{"role": "user", "content": prompt}]
            )

            # Afficher les donnees
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Journal comptable")
                st.dataframe(journal, use_container_width=True)
            with col2:
                st.subheader("Releve bancaire")
                st.dataframe(releve, use_container_width=True)

            # Afficher l'analyse
            st.subheader("Analyse de reconciliation")
            st.write(response.content[0].text)