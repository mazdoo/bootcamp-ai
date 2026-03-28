import streamlit as st
import fitz
import anthropic
import pandas as pd
import json
import io
import sys
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="BookKeeper AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

client = anthropic.Anthropic(timeout=120.0)

# --- SIDEBAR ---
st.sidebar.title("📚 BookKeeper AI")
st.sidebar.write("Assistant intelligent pour la comptabilite")
st.sidebar.divider()

# --- FONCTIONS UTILITAIRES ---
def nettoyer_json(texte):
    texte = texte.strip()
    if texte.startswith("```"):
        texte = texte.split("\n", 1)[1]
    if texte.endswith("```"):
        texte = texte[:-3]
    return texte.strip()

def lire_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texte = ""
    for page in doc:
        texte += page.get_text()
    doc.close()
    return texte

def appel_claude(system_prompt, user_message, max_tokens=1024):
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

# --- ONGLETS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🧾 Extraction factures",
    "💬 Chat fichiers",
    "📂 Classification",
    "🔄 Reconciliation"
])

# ==========================================
# MODULE 1 : EXTRACTION DE FACTURES
# ==========================================
with tab1:
    st.header("🧾 Extraction automatique de factures PDF")
    st.write("Upload tes factures et Claude extrait toutes les donnees en un clic.")

    PROMPT_FACTURE = """Tu es un assistant specialise dans l'extraction de donnees de factures.
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

    factures_upload = st.file_uploader(
        "Upload tes factures PDF",
        type=["pdf"],
        accept_multiple_files=True,
        key="factures"
    )

    if factures_upload and "factures_result" not in st.session_state:
        if st.button("Extraire les donnees", key="btn_factures"):
            st.session_state.factures_result = []
            progress = st.progress(0)

            for i, fichier in enumerate(factures_upload):
                st.write(f"Extraction de {fichier.name}...")
                texte = lire_pdf(fichier.read())
                reponse = appel_claude(PROMPT_FACTURE, f"Facture :\n\n{texte}")
                reponse = nettoyer_json(reponse)
                try:
                    data = json.loads(reponse)
                    data["fichier"] = fichier.name
                    st.session_state.factures_result.append(data)
                except:
                    pass
                progress.progress((i + 1) / len(factures_upload))
                if i < len(factures_upload) - 1:
                    time.sleep(3)
            st.rerun()

    if "factures_result" in st.session_state and st.session_state.factures_result:
        resultats = st.session_state.factures_result

        recap = [{
            "N Facture": r["numero_facture"],
            "Date": r["date"],
            "Fournisseur": r["fournisseur"],
            "Client": r["client"],
            "Total HT": r["total_ht"],
            "TVA": r["tva"],
            "Total TTC": r["total_ttc"]
        } for r in resultats]

        df = pd.DataFrame(recap)
        st.dataframe(df, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Factures", len(df))
        col2.metric("Total HT", f"{df['Total HT'].sum():,.2f} EUR")
        col3.metric("Total TTC", f"{df['Total TTC'].sum():,.2f} EUR")

        # Detail
        for r in resultats:
            with st.expander(f"{r['numero_facture']} — {r['fournisseur']}"):
                for ligne in r["lignes"]:
                    st.write(f"- {ligne['description']} : {ligne['quantite']} x {ligne['prix_unitaire']} = {ligne['total_ligne']} EUR")

        # Export Excel
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
            df_detail.to_excel(writer, sheet_name="Detail", index=False)

        st.download_button(
            label="Telecharger l'Excel",
            data=buffer.getvalue(),
            file_name="factures_extraites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.button("Reset factures", key="reset_factures"):
        st.session_state.pop("factures_result", None)
        st.rerun()

# ==========================================
# MODULE 2 : CHAT SUR FICHIERS
# ==========================================
with tab2:
    st.header("💬 Chat avec tes fichiers Excel/CSV")
    st.write("Upload un fichier et pose tes questions en francais.")

    chat_file = st.file_uploader("Upload un fichier", type=["csv", "xlsx"], key="chat_file")

    if chat_file and "chat_df" not in st.session_state:
        if chat_file.name.endswith(".csv"):
            st.session_state.chat_df = pd.read_csv(chat_file)
        else:
            st.session_state.chat_df = pd.read_excel(chat_file)

        df = st.session_state.chat_df
        st.session_state.chat_info = f"""DataFrame 'df' charge.
COLONNES : {df.columns.tolist()}
TYPES : {df.dtypes.to_dict()}
LIGNES : {len(df)}
APERCU :
{df.head(5).to_string()}
VALEURS UNIQUES :
{chr(10).join(f'- {col}: {df[col].nunique()} valeurs' for col in df.columns if df[col].dtype == 'object')}
"""

    if "chat_df" in st.session_state:
        with st.expander("Apercu des donnees"):
            st.dataframe(st.session_state.chat_df.head(10), use_container_width=True)

    tools = [{
        "name": "executer_pandas",
        "description": "Execute du code pandas sur le DataFrame 'df'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code pandas. Le DataFrame s'appelle 'df'."}
            },
            "required": ["code"]
        }
    }]

    def executer_pandas(code):
        try:
            if "\n" not in code and not code.startswith("print"):
                result = eval(code, {"df": st.session_state.chat_df, "pd": pd, "__builtins__": __builtins__})
                return str(result)
            else:
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                exec(code, {"df": st.session_state.chat_df, "pd": pd, "__builtins__": __builtins__})
                sys.stdout = old_stdout
                return buffer.getvalue() or "Code execute"
        except Exception as e:
            return f"Erreur : {e}"

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []

    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Pose ta question sur les donnees...", key="chat_input"):
        if "chat_df" not in st.session_state:
            st.warning("Upload un fichier d'abord !")
        else:
            st.session_state.chat_display.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyse..."):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})

                    while True:
                        response = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=1024,
                            system=f"""Tu es un assistant comptable expert.
Utilise l'outil executer_pandas pour analyser les donnees.
Reponds en francais avec des chiffres precis.
{st.session_state.chat_info}""",
                            tools=tools,
                            messages=st.session_state.chat_messages
                        )

                        if response.stop_reason == "end_turn":
                            reply = "".join(b.text for b in response.content if b.type == "text")
                            st.write(reply)
                            st.session_state.chat_messages.append({"role": "assistant", "content": response.content})
                            st.session_state.chat_display.append({"role": "assistant", "content": reply})
                            break

                        if response.stop_reason == "tool_use":
                            st.session_state.chat_messages.append({"role": "assistant", "content": response.content})
                            tool_results = []
                            for block in response.content:
                                if block.type == "tool_use":
                                    resultat = executer_pandas(block.input["code"])
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": resultat
                                    })
                            st.session_state.chat_messages.append({"role": "user", "content": tool_results})

    if st.button("Reset chat", key="reset_chat"):
        for k in ["chat_df", "chat_info", "chat_messages", "chat_display"]:
            st.session_state.pop(k, None)
        st.rerun()

# ==========================================
# MODULE 3 : CLASSIFICATION
# ==========================================
with tab3:
    st.header("📂 Classification automatique de documents")
    st.write("Upload des documents et Claude les classe par type.")

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

    classif_files = st.file_uploader(
        "Upload tes documents",
        type=["pdf"],
        accept_multiple_files=True,
        key="classif"
    )

    if classif_files and st.button("Classifier", key="btn_classif"):
        resultats_classif = []
        progress = st.progress(0)

        for i, fichier in enumerate(classif_files):
            st.write(f"Classification de {fichier.name}...")
            texte = lire_pdf(fichier.read())
            reponse = appel_claude(PROMPT_CLASSIF, f"Document :\n\n{texte[:3000]}")
            reponse = nettoyer_json(reponse)
            try:
                data = json.loads(reponse)
                data["fichier"] = fichier.name
                resultats_classif.append(data)
            except:
                pass
            progress.progress((i + 1) / len(classif_files))
            if i < len(classif_files) - 1:
                time.sleep(3)

        if resultats_classif:
            df_classif = pd.DataFrame(resultats_classif)
            st.dataframe(
                df_classif[["fichier", "type_document", "confiance", "resume", "montant_principal"]],
                use_container_width=True
            )
            for r in resultats_classif:
                with st.expander(f"{r['fichier']} -> {r['type_document']}"):
                    st.write(f"Emetteur : {r.get('fournisseur_ou_emetteur', 'N/A')}")
                    st.write(f"Date : {r.get('date', 'N/A')}")
                    st.write(f"Montant : {r.get('montant_principal', 'N/A')} EUR")
                    st.write(f"Resume : {r['resume']}")

# ==========================================
# MODULE 4 : RECONCILIATION
# ==========================================
with tab4:
    st.header("🔄 Reconciliation de donnees")
    st.write("Compare deux fichiers pour identifier correspondances et ecarts.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fichier 1")
        reconc_file1 = st.file_uploader("Journal comptable", type=["csv", "xlsx"], key="reconc1")

    with col2:
        st.subheader("Fichier 2")
        reconc_file2 = st.file_uploader("Releve bancaire", type=["csv", "xlsx"], key="reconc2")

    if reconc_file1 and reconc_file2 and st.button("Reconcilier", key="btn_reconc"):
        with st.spinner("Reconciliation en cours..."):
            if reconc_file1.name.endswith(".csv"):
                journal = pd.read_csv(reconc_file1)
            else:
                journal = pd.read_excel(reconc_file1)

            if reconc_file2.name.endswith(".csv"):
                releve = pd.read_csv(reconc_file2)
            else:
                releve = pd.read_excel(reconc_file2)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Journal")
                st.dataframe(journal, use_container_width=True)
            with col2:
                st.subheader("Releve")
                st.dataframe(releve, use_container_width=True)

            prompt_reconc = f"""Voici deux fichiers a reconcilier :

JOURNAL COMPTABLE :
{journal.to_string(index=False)}

RELEVE BANCAIRE :
{releve.to_string(index=False)}

Analyse et :
1. Identifie les ecritures correspondantes (par date et montant)
2. Liste celles presentes dans le journal mais absentes du releve
3. Liste celles presentes dans le releve mais absentes du journal
4. Calcule les soldes
5. Donne des recommandations

Formate clairement avec des sections."""

            reponse = appel_claude(
                "Tu es un expert comptable specialise en reconciliation bancaire. Reponds en francais.",
                prompt_reconc,
                max_tokens=2048
            )

            st.subheader("Analyse")
            st.write(reponse)