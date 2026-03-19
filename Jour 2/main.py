class Chatbot:
    def __init__(self, nom):
        self.nom = nom

    def repondre(self, message):
        print(f"{self.nom} : {message}")


# Créer un chatbot et lui faire dire quelque chose
bot = Chatbot("Alex")
bot.repondre("Bonjour, comment puis-je t'aider ?")
bot.repondre("Je suis un assistant IA.")

import requests
import json

try:
    reponse = requests.get("https://wttr.in/Paris?format=j1")
    donnees = reponse.json()
    
    temperature = donnees["current_condition"][0]["temp_C"]
    description = donnees["current_condition"][0]["weatherDesc"][0]["value"]
    
    print(f"Météo à Paris : {temperature}°C, {description}")
