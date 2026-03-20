from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="C:/Users/kilia/Desktop/Bootcamp IA/Jour 3/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

historique = [
    {"role": "system", "content": "Tu es un assistant utile et concis."}
]

print("Chatbot prêt ! Tape 'quitter' pour arrêter.\n")

while True:
    message = input("Toi : ")
    
    if message.lower() == "quitter":
        print("Au revoir !")
        break
    
    historique.append({"role": "user", "content": message})
    
    reponse = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historique
    )
    
    réponse_texte = reponse.choices[0].message.content
    historique.append({"role": "assistant", "content": réponse_texte})
    
    print(f"GPT : {réponse_texte}\n")