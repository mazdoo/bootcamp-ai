import fitz

factures = [
    {
        "filename": "facture_001.pdf",
        "text": """
FACTURE N° 2026-001

Émetteur : CloudTech Solutions SAS
SIRET : 123 456 789 00012
Date : 05/01/2026

Client : Dupont SARL
Adresse : 12 rue de la Paix, 75002 Paris

Description                     Qté    Prix unit.    Total
------------------------------------------------------------
Hébergement cloud annuel          1    2 400,00 €   2 400,00 €
Support premium (mois)           12      150,00 €   1 800,00 €
Migration données                 1      800,00 €     800,00 €

------------------------------------------------------------
Total HT :                                         5 000,00 €
TVA (20%) :                                         1 000,00 €
Total TTC :                                         6 000,00 €

Paiement : virement sous 30 jours
IBAN : FR76 1234 5678 9012 3456 7890 123
"""
    },
    {
        "filename": "facture_002.pdf",
        "text": """
FACTURE N° F-2026-042

De : Martin & Associés
N° SIRET : 987 654 321 00034
En date du : 18/02/2026

Destinataire : Tech Solutions SAS
5 avenue des Champs, 69001 Lyon

Désignation                     Qté    PU HT         Montant
------------------------------------------------------------
Audit cybersécurité               1    3 500,00 €   3 500,00 €
Rapport de conformité RGPD        1    1 200,00 €   1 200,00 €
Formation sécurité (jours)        3      600,00 €   1 800,00 €

------------------------------------------------------------
Sous-total HT :                                     6 500,00 €
TVA 20% :                                           1 300,00 €
TOTAL TTC :                                         7 800,00 €

Échéance : 20/03/2026
"""
    },
    {
        "filename": "facture_003.pdf",
        "text": """
Facture #INV-2026-103

Fournisseur : Bureau Express SARL
SIRET : 456 789 123 00056
Date d'émission : 10/03/2026

Facturé à : Bernard SAS
28 boulevard Haussmann, 75009 Paris

Article                          Qté    Prix         Total HT
------------------------------------------------------------
Ramettes papier A4 (carton)       20       45,00 €     900,00 €
Cartouches imprimante             8       35,00 €     280,00 €
Stylos (boîte de 50)              5       12,00 €      60,00 €
Classeurs (lot de 10)             3       25,00 €      75,00 €

------------------------------------------------------------
Total HT :                                          1 315,00 €
TVA (20%) :                                           263,00 €
Total TTC :                                         1 578,00 €

Règlement attendu sous 45 jours
"""
    }
]

for f in factures:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), f["text"], fontsize=11)
    doc.save(f["filename"])
    doc.close()
    print(f"✅ {f['filename']} créé")

print(f"\n{len(factures)} factures de test générées !")