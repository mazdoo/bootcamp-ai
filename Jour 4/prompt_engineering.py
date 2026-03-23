import anthropic
from dotenv import load_dotenv
import os
import json

load_dotenv(dotenv_path="C:/Users/kilia/Desktop/Bootcamp IA/Jour 4/.env")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def appeler_llm(system, user):
    reponse = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    texte = reponse.content[0].text
    # Nettoyer les backticks si le LLM en ajoute quand même
    texte = texte.strip()
    if texte.startswith("```"):
        texte = texte.split("\n", 1)[1]
    if texte.endswith("```"):
        texte = texte.rsplit("```", 1)[0]
    return texte.strip()
# TEST 1 - Zero-shot basique
resultat = appeler_llm(
    system="Tu es un assistant qui répond uniquement en JSON.",
    user="Donne moi les infos sur Paris : population, pays, continent."
)
print("ZERO-SHOT BASIQUE :")
print(resultat)

# TEST 2 - Zero-shot amélioré : JSON pur sans markdown
resultat2 = appeler_llm(
    system="Tu es un assistant qui répond UNIQUEMENT en JSON valide, sans backticks, sans markdown, sans texte avant ou après.",
    user="Donne moi les infos sur Paris : population, pays, continent."
)
print("\nZERO-SHOT AMÉLIORÉ :")
print(resultat2)
donnees = json.loads(resultat2)
print(f"\nPopulation extraite : {donnees['population']}")

# TEST 3 - Few-shot : donner des exemples au LLM
resultat3 = appeler_llm(
    system="""Tu extrais le sentiment d'un avis client.
Réponds uniquement avec : positif, négatif, ou neutre.

Exemples :
Avis: "Livraison rapide, très satisfait !" → positif
Avis: "Produit cassé à la réception." → négatif
Avis: "Conforme à la description." → neutre""",
    user='Avis: "Franchement déçu, ça ne correspond pas du tout à ce que j\'attendais."'
)
print("\nFEW-SHOT (sentiment) :")
print(resultat3)

# TEST 4 - Chain-of-thought
resultat4 = appeler_llm(
    system="Tu es un assistant logique. Raisonne étape par étape avant de donner ta réponse finale.",
    user="J'ai 3 boîtes. La rouge contient 2 balles. La bleue contient le double de la rouge. La verte contient autant que rouge et bleue réunies. Combien de balles au total ?"
)
print("\nCHAIN-OF-THOUGHT :")
print(resultat4)

# TEST 5 - Extracteur d'infos
texte_brut = """
Réunion du 21 mars 2026 avec le client Société Générale.
Participants : Marie Dupont (chef de projet), Jean Martin (développeur).
Décisions prises : migration vers Azure OpenAI en avril,
budget alloué 50 000 euros, livraison prévue le 15 juin 2026.
"""

resultat5 = appeler_llm(
    system="Tu extrais les informations clés d'un compte-rendu de réunion. Réponds UNIQUEMENT en JSON valide sans markdown avec ces champs : date, client, participants (liste), decisions (liste), budget, deadline",
    user=texte_brut
)
print("\nEXTRACTEUR D'INFOS :")
print(resultat5)
infos = json.loads(resultat5)
print(f"\nClient : {infos['client']}")
print(f"Budget : {infos['budget']}")
print(f"Deadline : {infos['deadline']}")