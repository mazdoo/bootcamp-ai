import anthropic
from dotenv import load_dotenv
import json

load_dotenv()
client = anthropic.Anthropic()

# On définit un outil que Claude PEUT utiliser
tools = [
    {
        "name": "calculatrice",
        "description": "Effectue un calcul mathématique. Utilise cet outil pour toute opération arithmétique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "L'expression mathématique à calculer, ex: '245 * 18'"
                }
            },
            "required": ["expression"]
        }
    }
]

question = "Combien font 1547 * 38 + 294 ?"

print(f"Question : {question}\n")

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": question}]
)

# Regardons ce que Claude répond
for block in response.content:
    print(f"Type : {block.type}")
    if block.type == "tool_use":
        print(f"Outil : {block.name}")
        print(f"Input : {block.input}")
        print(f"ID : {block.id}")
    elif block.type == "text":
        print(f"Texte : {block.text}")