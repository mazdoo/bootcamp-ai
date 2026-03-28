import anthropic
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(timeout=120.0)

df = pd.read_csv("donnees_compta.csv")

info_fichier = f"""DataFrame 'df' charge.

COLONNES : {df.columns.tolist()}
TYPES : {df.dtypes.to_dict()}
LIGNES : {len(df)}
CLIENTS : {df['client'].unique().tolist()}
CATEGORIES : {df['categorie'].unique().tolist()}
STATUTS : {df['statut'].unique().tolist()}

APERCU :
{df.head(3).to_string()}
"""

tools = [
    {
        "name": "executer_pandas",
        "description": "Execute du code pandas sur le DataFrame 'df'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code pandas. Le DataFrame s'appelle 'df'."
                }
            },
            "required": ["code"]
        }
    }
]

def executer_outil(inputs):
    try:
        code = inputs["code"]
        if "\n" not in code and not code.startswith("print"):
            result = eval(code, {"df": df, "pd": pd, "__builtins__": __builtins__})
            return str(result)
        else:
            import io, sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            exec(code, {"df": df, "pd": pd, "__builtins__": __builtins__})
            sys.stdout = old_stdout
            output = buffer.getvalue()
            return output if output else "Code execute sans sortie"
    except Exception as e:
        return f"Erreur : {e}"

SYSTEM = f"""Tu es un assistant comptable expert.
Tu analyses les donnees avec l'outil executer_pandas.
Reponds en francais avec des chiffres precis.

{info_fichier}"""

print("--- CHAT COMPTABLE ---")
print("Tape 'quit' pour quitter.\n")

messages = []

while True:
    question = input("Q: ")
    if question.lower() in ["quit", "exit", "q"]:
        break

    messages.append({"role": "user", "content": question})

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"\nR: {block.text}\n")
                    messages.append({"role": "assistant", "content": response.content})
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [analyse en cours...]")
                    resultat = executer_outil(block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": resultat
                    })
            messages.append({"role": "user", "content": tool_results})