import anthropic
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(timeout=120.0)

# Charger les donnees
df = pd.read_csv("donnees_compta.csv")

# Preparer le contexte pour Claude
info_fichier = f"""Fichier CSV charge dans un DataFrame pandas nomme 'df'.

COLONNES :
{chr(10).join(f'- {col} ({df[col].dtype})' for col in df.columns)}

APERCU (5 premieres lignes) :
{df.head().to_string()}

STATISTIQUES :
- {len(df)} lignes au total
- Clients : {df['client'].unique().tolist()}
- Categories : {df['categorie'].unique().tolist()}
- Statuts : {df['statut'].unique().tolist()}
"""

tools = [
    {
        "name": "executer_pandas",
        "description": "Execute du code pandas sur le DataFrame 'df' et retourne le resultat. Utilise cet outil pour toute analyse de donnees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code pandas a executer. Le DataFrame s'appelle 'df'. Le code doit produire un resultat affichable."
                },
                "explication": {
                    "type": "string",
                    "description": "Breve explication de ce que fait le code."
                }
            },
            "required": ["code", "explication"]
        }
    }
]

def executer_outil(nom, inputs):
    if nom == "executer_pandas":
        try:
            code = inputs["code"]
            local_vars = {"df": df, "pd": pd}
            # Pour du code multi-lignes, on utilise exec puis on capture le dernier resultat
            if "\n" not in code and not code.startswith("print"):
                # Code sur une seule ligne = expression
                result = eval(code, {"df": df, "pd": pd, "__builtins__": __builtins__})
                return str(result)
            else:
                # Code multi-lignes = on execute et on capture les prints
                import io, sys
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                exec(code, {"df": df, "pd": pd, "__builtins__": __builtins__})
                sys.stdout = old_stdout
                output = buffer.getvalue()
                return output if output else "Code execute sans sortie"
        except Exception as e:
            return f"Erreur : {e}"
    return "Outil inconnu"

def agent(question):
    print(f"\nQ: {question}\n")
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=f"""Tu es un assistant comptable expert en analyse de donnees.
Tu as acces a un DataFrame pandas pour repondre aux questions.

{info_fichier}

Utilise l'outil executer_pandas pour analyser les donnees.
Reponds toujours en francais avec des chiffres precis.""",
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"R: {block.text}")
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [pandas] {block.input.get('explication', '')}")
                    print(f"  [code]   {block.input['code']}")
                    resultat = executer_outil(block.name, block.input)
                    print(f"  [result] {resultat[:200]}\n")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": resultat
                    })
            messages.append({"role": "user", "content": tool_results})

import time
agent("Quel est le total des impayes ?")
time.sleep(3)
agent("Quel client depense le plus ?")
time.sleep(3)
agent("Compare les depenses par categorie.")
time.sleep(3)
agent("Quelles factures sont en retard de paiement par rapport a aujourd'hui ?")