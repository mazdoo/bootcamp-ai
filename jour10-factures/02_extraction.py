import fitz
import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

PROMPT_EXTRACTION = """Tu es un assistant spécialisé dans l'extraction de données de factures.

Extrais les informations suivantes de la facture et retourne UNIQUEMENT un objet JSON valide, sans texte avant ni après :

{
    "numero_facture": "numéro de la facture",
    "date": "date d'émission au format JJ/MM/AAAA",
    "fournisseur": "nom de l'entreprise émettrice",
    "siret_fournisseur": "numéro SIRET si présent, sinon null",
    "client": "nom du client destinataire",
    "lignes": [
        {
            "description": "description de l'article/service",
            "quantite": 0,
            "prix_unitaire": 0.00,
            "total_ligne": 0.00
        }
    ],
    "total_ht": 0.00,
    "tva": 0.00,
    "total_ttc": 0.00,
    "echeance": "conditions de paiement si mentionnées, sinon null"
}

Règles :
- Les montants sont en nombres (pas de symbole €)
- Les dates en format JJ/MM/AAAA
- Si une info est absente, mettre null
- Retourne UNIQUEMENT le JSON, rien d'autre"""

def lire_pdf(chemin):
    doc = fitz.open(chemin)
    texte = ""
    for page in doc:
        texte += page.get_text()
    doc.close()
    return texte

def extraire_facture(chemin_pdf):
    texte = lire_pdf(chemin_pdf)
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=PROMPT_EXTRACTION,
        messages=[{"role": "user", "content": f"Voici la facture à analyser :\n\n{texte}"}]
    )
    
    reponse_texte = response.content[0].text
    
    # Nettoyer les balises markdown
    reponse_texte = reponse_texte.strip()
    if reponse_texte.startswith("```"):
        reponse_texte = reponse_texte.split("\n", 1)[1]
    if reponse_texte.endswith("```"):
        reponse_texte = reponse_texte[:-3]
    reponse_texte = reponse_texte.strip()
    
    try:
        donnees = json.loads(reponse_texte)
        return donnees
    except json.JSONDecodeError:
        print(f"⚠️ Erreur de parsing JSON")
        print(f"Réponse brute : {reponse_texte[:200]}")
        return None

# Test sur une facture
print("=== EXTRACTION FACTURE 001 ===\n")
resultat = extraire_facture("facture_001.pdf")

if resultat:
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    print(f"\n📊 Résumé :")
    print(f"   Fournisseur : {resultat['fournisseur']}")
    print(f"   Client : {resultat['client']}")
    print(f"   Total TTC : {resultat['total_ttc']} €")