import anthropic
from dotenv import load_dotenv
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
                    "description": "Expression mathématique à calculer"
                }
            },
            "required": ["expression"]
        }
    }
]

def executer_outil(nom, inputs):
    """Exécute l'outil demandé par Claude"""
    if nom == "calculatrice":
        try:
            resultat = eval(inputs["expression"])
            return str(resultat)
        except Exception as e:
            return f"Erreur : {e}"
    return "Outil inconnu"

def agent(question):
    print(f"🧑 Question : {question}\n")
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        # Si Claude a fini (pas d'outil à appeler)
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"🤖 Réponse : {block.text}")
            break

        # Si Claude veut utiliser un outil
        if response.stop_reason == "tool_use":
            # Ajouter la réponse de Claude aux messages
            messages.append({"role": "assistant", "content": response.content})

            # Exécuter chaque outil demandé
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"🔧 Claude utilise : {block.name}({block.input})")
                    resultat = executer_outil(block.name, block.input)
                    print(f"📊 Résultat : {resultat}\n")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": resultat
                    })

            # Renvoyer les résultats à Claude
            messages.append({"role": "user", "content": tool_results})

# Test
agent("Si j'achète 47 articles à 23.50€ chacun, combien je paie au total ? Et avec 20% de TVA ?")