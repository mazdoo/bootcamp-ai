import streamlit as st
import anthropic
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

st.set_page_config(page_title="Agent AI", page_icon="🤖", layout="wide")
st.title("🤖 Agent AI Multi-Outils")

client = anthropic.Anthropic()

# --- Outils ---
tools = [
    {
        "name": "calculatrice",
        "description": "Effectue un calcul mathématique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression mathématique"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "date_heure",
        "description": "Retourne la date et l'heure actuelles.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "recherche_employes",
        "description": "Recherche un employé dans la base de données par nom.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nom": {"type": "string", "description": "Nom de l'employé"}
            },
            "required": ["nom"]
        }
    }
]

employes = {
    "dupont": {"nom": "Marie Dupont", "poste": "Comptable", "salaire": 42000},
    "martin": {"nom": "Jean Martin", "poste": "Développeur", "salaire": 48000},
    "bernard": {"nom": "Sophie Bernard", "poste": "Manager", "salaire": 55000},
}

def executer_outil(nom, inputs):
    if nom == "calculatrice":
        try:
            return str(eval(inputs["expression"]))
        except:
            return "Erreur de calcul"
    elif nom == "date_heure":
        return datetime.now().strftime("%d/%m/%Y %H:%M")
    elif nom == "recherche_employes":
        recherche = inputs["nom"].lower()
        for key, emp in employes.items():
            if recherche in key or recherche in emp["nom"].lower():
                return json.dumps(emp, ensure_ascii=False)
        return "Employé non trouvé"
    return "Outil inconnu"

# --- Interface ---
st.sidebar.header("🔧 Outils disponibles")
st.sidebar.write("- 🧮 Calculatrice")
st.sidebar.write("- 🕐 Date et heure")
st.sidebar.write("- 👤 Base employés")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Pose ta question..."):
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("L'agent réfléchit..."):
            messages = [{"role": "user", "content": prompt}]
            outils_utilises = []

            while True:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if block.type == "text":
                            st.write(block.text)
                            st.session_state.display_messages.append(
                                {"role": "assistant", "content": block.text}
                            )
                    break

                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            resultat = executer_outil(block.name, block.input)
                            outils_utilises.append(
                                f"🔧 {block.name}({json.dumps(block.input)}) → {resultat}"
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": resultat
                            })
                    messages.append({"role": "user", "content": tool_results})

            if outils_utilises:
                with st.expander("🔧 Outils utilisés par l'agent"):
                    for outil in outils_utilises:
                        st.code(outil)