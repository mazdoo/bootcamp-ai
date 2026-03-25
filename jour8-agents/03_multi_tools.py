import anthropic
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()
client = anthropic.Anthropic()

tools = [
    {
        "name": "calculatrice",
        "description": "Effectue un calcul mathématique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Expression mathématique"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "date_heure",
        "description": "Retourne la date et l'heure actuelles.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "recherche_employes",
        "description": "Recherche un employé dans la base de données par nom.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nom": {
                    "type": "string",
                    "description": "Nom de l'employé à rechercher"
                }
            },
            "required": ["nom"]
        }
    }
]

# Fake base de données
employes = {
    "dupont": {"nom": "Marie Dupont", "poste": "Comptable", "salaire": 42000},
    "martin": {"nom": "Jean Martin", "poste": "Développeur", "salaire": 48000},
    "bernard": {"nom": "Sophie Bernard", "poste": "Manager", "salaire": 55000},
}

def executer_outil(nom, inputs):
    if nom == "calculatrice":
        try:
            return str(eval(inputs["expression"]))
        except Exception as e:
            return f"Erreur : {e}"
    elif nom == "date_heure":
        return datetime.now().strftime("%d/%m/%Y %H:%M")
    elif nom == "recherche_employes":
        recherche = inputs["nom"].lower()
        for key, emp in employes.items():
            if recherche in key or recherche in emp["nom"].lower():
                return json.dumps(emp, ensure_ascii=False)
        return "Employé non trouvé"
    return "Outil inconnu"

def agent(question):
    print(f"\n🧑 Question : {question}\n")
    messages = [{"role": "user", "content": question}]

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
                    print(f"🤖 Réponse : {block.text}")
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"🔧 Outil : {block.name}({block.input})")
                    resultat = executer_outil(block.name, block.input)
                    print(f"📊 Résultat : {resultat}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": resultat
                    })
            messages.append({"role": "user", "content": tool_results})

# Tests — Claude choisit le bon outil à chaque fois
import time

agent("Quelle heure est-il ?")
time.sleep(5)
agent("Quel est le salaire de Sophie Bernard ?")
time.sleep(5)
agent("Si Dupont a une augmentation de 15%, quel sera son nouveau salaire ?")