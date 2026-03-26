import fitz
import anthropic
import json
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(timeout=120.0)

PROMPT_EXTRACTION = """Tu es un assistant spécialisé dans l'extraction de données de factures.

Extrais les informations et retourne UNIQUEMENT un objet JSON valide :

{
    "numero_facture": "string",
    "date": "JJ/MM/AAAA",
    "fournisseur": "string",
    "siret_fournisseur": "string ou null",
    "client": "string",
    "lignes": [{"description": "string", "quantite": 0, "prix_unitaire": 0.00, "total_ligne": 0.00}],
    "total_ht": 0.00,
    "tva": 0.00,
    "total_ttc": 0.00,
    "echeance": "string ou null"
}

Montants en nombres, dates en JJ/MM/AAAA. Retourne UNIQUEMENT le JSON."""

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
        messages=[{"role": "user", "content": f"Facture :\n\n{texte}"}]
    )
    reponse_texte = response.content[0].text.strip()
    if reponse_texte.startswith("```"):
        reponse_texte = reponse_texte.split("\n", 1)[1]
    if reponse_texte.endswith("```"):
        reponse_texte = reponse_texte[:-3]
    reponse_texte = reponse_texte.strip()
    try:
        return json.loads(reponse_texte)
    except json.JSONDecodeError:
        print(f"Erreur JSON: {reponse_texte[:100]}")
        return None

# --- Traitement en lot ---
fichiers = ["facture_001.pdf", "facture_002.pdf", "facture_003.pdf"]
resultats = []

print("Extraction en cours...\n")

for fichier in fichiers:
    print(f"  {fichier}...", end=" ")
    donnees = extraire_facture(fichier)
    if donnees:
        donnees["fichier_source"] = fichier
        resultats.append(donnees)
        print(f"OK - {donnees['fournisseur']} - {donnees['total_ttc']} euros")
    else:
        print("ECHEC")
    time.sleep(3)

# --- Creer le recapitulatif ---
recap = []
for r in resultats:
    recap.append({
        "N Facture": r["numero_facture"],
        "Date": r["date"],
        "Fournisseur": r["fournisseur"],
        "Client": r["client"],
        "Total HT": r["total_ht"],
        "TVA": r["tva"],
        "Total TTC": r["total_ttc"],
        "Echeance": r["echeance"],
        "Fichier": r["fichier_source"]
    })

df = pd.DataFrame(recap)

# --- Creer le detail des lignes ---
detail = []
for r in resultats:
    for ligne in r["lignes"]:
        detail.append({
            "N Facture": r["numero_facture"],
            "Fournisseur": r["fournisseur"],
            "Description": ligne["description"],
            "Quantite": ligne["quantite"],
            "Prix unitaire": ligne["prix_unitaire"],
            "Total ligne": ligne["total_ligne"]
        })

df_detail = pd.DataFrame(detail)

# --- Export Excel ---
with pd.ExcelWriter("factures_extraites.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Recapitulatif", index=False)
    df_detail.to_excel(writer, sheet_name="Detail lignes", index=False)

print(f"\nfactures_extraites.xlsx cree !")
print(f"   Recapitulatif : {len(df)} factures")
print(f"   Detail : {len(df_detail)} lignes")

if len(df) > 0:
    print(f"\n   Total general : {df['Total TTC'].sum():.2f} euros")