import streamlit as st
import anthropic
import pandas as pd
import json
import io
import sys
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chat Excel", page_icon="💬", layout="wide")
st.title("💬 Chat avec tes fichiers Excel/CSV")

client = anthropic.Anthropic(timeout=120.0)

# --- Upload ---
uploaded_file = st.sidebar.file_uploader(
    "Upload un fichier",
    type=["csv", "xlsx"]
)

if uploaded_file and "df" not in st.session_state:
    with st.spinner("Lecture du fichier..."):
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state.df = df

        st.session_state.info_fichier = f"""DataFrame 'df' charge.
COLONNES : {df.columns.tolist()}
TYPES : {df.dtypes.to_dict()}
LIGNES : {len(df)}
APERCU :
{df.head(5).to_string()}
VALEURS UNIQUES PAR COLONNE :
{chr(10).join(f'- {col}: {df[col].nunique()} valeurs uniques' for col in df.columns if df[col].dtype == 'object')}
"""
    st.sidebar.success(f"{len(df)} lignes chargees !")

# --- Apercu ---
if "df" in st.session_state:
    with st.expander("Apercu des donnees", expanded=False):
        st.dataframe(st.session_state.df.head(10), use_container_width=True)

# --- Outils ---
tools = [
    {
        "name": "executer_pandas",
        "description": "Execute du code pandas sur le DataFrame 'df'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code pandas. Le DataFrame s'appelle 'df'."}
            },
            "required": ["code"]
        }
    }
]

def executer_outil(inputs):
    try:
        code = inputs["code"]
        if "\n" not in code and not code.startswith("print"):
            result = eval(code, {"df": st.session_state.df, "pd": pd, "__builtins__": __builtins__})
            return str(result)
        else:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            exec(code, {"df": st.session_state.df, "pd": pd, "__builtins__": __builtins__})
            sys.stdout = old_stdout
            output = buffer.getvalue()
            return output if output else "Code execute sans sortie"
    except Exception as e:
        return f"Erreur : {e}"

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Pose ta question sur les donnees..."):
    if "df" not in st.session_state:
        st.warning("Upload un fichier d'abord !")
    else:
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                outils_utilises = []

                while True:
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1024,
                        system=f"""Tu es un assistant comptable expert en analyse de donnees.
Utilise l'outil executer_pandas pour analyser les donnees.
Reponds en francais avec des chiffres precis.
Quand tu montres des resultats, formate-les clairement.

{st.session_state.info_fichier}""",
                        tools=tools,
                        messages=st.session_state.messages
                    )

                    if response.stop_reason == "end_turn":
                        reply = ""
                        for block in response.content:
                            if block.type == "text":
                                reply += block.text
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": response.content})
                        st.session_state.display_messages.append({"role": "assistant", "content": reply})

                        if outils_utilises:
                            with st.expander("Code pandas execute"):
                                for code in outils_utilises:
                                    st.code(code, language="python")
                        break

                    if response.stop_reason == "tool_use":
                        st.session_state.messages.append({"role": "assistant", "content": response.content})
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                outils_utilises.append(block.input["code"])
                                resultat = executer_outil(block.input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": resultat
                                })
                        st.session_state.messages.append({"role": "user", "content": tool_results})

# --- Reset ---
if st.sidebar.button("Nouveau fichier"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()