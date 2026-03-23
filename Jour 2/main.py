import requests
import json

try:
    reponse = requests.get("https://wttr.in/Paris?format=j1")
    donnees = reponse.json()
    
    temperature = donnees["current_condition"][0]["temp_C"]
    description = donnees["current_condition"][0]["weatherDesc"][0]["value"]
    
    print(f"Météo à Paris : {temperature}°C, {description}")

except requests.exceptions.ConnectionError:
    print("Erreur : pas de connexion réseau.")

except Exception as e:
    print(f"Erreur inattendue : {e}")