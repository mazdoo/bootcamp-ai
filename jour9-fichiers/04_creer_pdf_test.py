import fitz  # PyMuPDF

doc = fitz.open()
page = doc.new_page()

# Simuler une facture
texte = """
FACTURE N° 2026-0042

Émetteur : Tech Solutions SAS
Date : 15/03/2026

Client : Dupont SARL
Adresse : 12 rue de la Paix, 75002 Paris

Description                    Quantité    Prix unitaire    Total
---------------------------------------------------------------
Licence logiciel annuelle         1          3 400,00 €    3 400,00 €
Support technique (heures)       10            95,00 €      950,00 €
Formation utilisateurs            2           750,00 €    1 500,00 €

---------------------------------------------------------------
Total HT :                                              5 850,00 €
TVA (20%) :                                             1 170,00 €
Total TTC :                                             7 020,00 €

Conditions : paiement à 30 jours
"""

page.insert_text(fitz.Point(50, 50), texte, fontsize=11)
doc.save("facture_test.pdf")
doc.close()
print("✅ facture_test.pdf créé !")