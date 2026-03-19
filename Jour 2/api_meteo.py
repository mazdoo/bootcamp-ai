import requests
from pathlib import Path

def get_meteo(ville):
    try:
        reponse = requests.get(f"https://wttr.in/{ville}?format=j1", timeout=10)
        donnees = reponse.json()
        
        temperature = donnees["data"]["current_condition"][0]["temp_C"]
        ressenti = donnees["data"]["current_condition"][0]["FeelsLikeC"]
        description = donnees["data"]["current_condition"][0]["weatherDesc"][0]["value"]
        
        resultat = f"{ville} : {temperature}°C (ressenti {ressenti}°C) — {description}"
        return resultat

    except requests.exceptions.ConnectionError:
        return "Erreur : pas de connexion réseau."
    
    except Exception as e:
        return f"Erreur inattendue : {e}"


def sauvegarder(texte, nom_fichier):
    Path("outputs").mkdir(exist_ok=True)
    fichier = Path("outputs") / nom_fichier
    fichier.write_text(texte, encoding="utf-8")
    print(f"Sauvegardé dans {fichier}")


# Programme principal
villes = ["Paris", "Lyon", "Marseille"]

resultats = []
for ville in villes:
    meteo = get_meteo(ville)
    print(meteo)
    resultats.append(meteo)

sauvegarder("\n".join(resultats), "meteo.txt")