import fitz
import anthropic
import json
import time
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(timeout=120.0)

PROMPT_CLASSIF = """Tu es un assistant specialise dans la classification de documents comptables.

Analyse le document et retourne UNIQUEMENT un objet JSON valide :

{
    "type_document": "facture | devis | bon_de_commande | releve_bancaire | contrat | note_de_frais | autre",
    "confiance": 0.95,
    "fournisseur_ou_emetteur": "nom si identifiable, sinon null",
    "date": "date si identifiable, sinon null",
    "montant_principal": 0.00,
    "resume": "resume en une phrase du contenu",
    "mots_cles": ["mot1", "mot2", "mot3"]
}

Retourne UNIQUEMENT le JSON."""

def lire_document(chemin):
    if chemin.endswith(".pdf"):
        doc = fitz.open(chemin)
        texte = ""
        for page in doc:
            texte += page.get_text()
        doc.close()
        return texte
    else:
        with open(chemin, "r", encoding="utf-8") as f:
            return f.read()

def classifier(chemin):
    texte = lire_document(chemin)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=PROMPT_CLASSIF,
        messages=[{"role": "user", "content": f"Document a classifier :\n\n{texte[:3000]}"}]
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
        return None

# --- Creer des documents de test ---
def creer_documents_test():
    # Devis
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), """
DEVIS N° D-2026-015

De : WebDesign Pro SARL
Date : 20/03/2026

Pour : Dupont SARL

Objet : Refonte site internet

Description                          Prix
-------------------------------------------------
Maquette graphique                  2 500,00 EUR
Developpement front-end             4 000,00 EUR
Integration CMS                     1 500,00 EUR
Formation utilisateur                 800,00 EUR

-------------------------------------------------
Total HT :                          8 800,00 EUR
TVA (20%) :                         1 760,00 EUR
Total TTC :                        10 560,00 EUR

Validite : 30 jours
""", fontsize=11)
    doc.save("devis_web.pdf")
    doc.close()

    # Note de frais
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), """
NOTE DE FRAIS

Employe : Jean Martin
Service : Commercial
Periode : Mars 2026

Date        Description              Montant
-------------------------------------------------
05/03/2026  Taxi client Lyon          45,00 EUR
12/03/2026  Dejeuner client           62,50 EUR
15/03/2026  Train Paris-Lyon         89,00 EUR
18/03/2026  Hotel 1 nuit Lyon       120,00 EUR
22/03/2026  Fournitures bureau        35,80 EUR

-------------------------------------------------
Total :                             352,30 EUR

Signature employe : J. Martin
Approbation manager : En attente
""", fontsize=11)
    doc.save("note_frais.pdf")
    doc.close()

    # Releve bancaire
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), """
RELEVE DE COMPTE

Banque Nationale - Agence Paris Centre
Compte : FR76 1234 5678 9012 3456 7890
Titulaire : Dupont SARL
Periode : 01/03/2026 au 31/03/2026

Date        Libelle                    Debit      Credit
-----------------------------------------------------------
01/03  Solde precedent                            15 230,00
03/03  Virement client Martin                      4 080,00
05/03  Paiement fournisseur         1 578,00
10/03  Prelevement loyer            2 500,00
15/03  Virement client Tech Sol.                   3 840,00
18/03  Achat fournitures              336,00
22/03  Paiement salaires            8 500,00
25/03  Virement client Global                     10 200,00
28/03  Charges sociales             3 200,00

-----------------------------------------------------------
Solde au 31/03/2026 :                            17 236,00
""", fontsize=11)
    doc.save("releve_bancaire.pdf")
    doc.close()

    print("3 documents de test crees !")

# Creer les documents
creer_documents_test()

# Classifier chaque document
fichiers = ["devis_web.pdf", "note_frais.pdf", "releve_bancaire.pdf"]

# Ajouter les factures du jour 10 si elles existent
import os
for f in ["../jour10-factures/facture_001.pdf", "../jour10-factures/facture_002.pdf"]:
    if os.path.exists(f):
        fichiers.append(f)

print("\nClassification en cours...\n")

for fichier in fichiers:
    nom = os.path.basename(fichier)
    print(f"  {nom}...", end=" ")
    resultat = classifier(fichier)
    if resultat:
        print(f"-> {resultat['type_document']} (confiance: {resultat['confiance']})")
        print(f"     Resume: {resultat['resume']}")
        print(f"     Mots-cles: {', '.join(resultat['mots_cles'])}\n")
    else:
        print("ECHEC\n")
    time.sleep(3)