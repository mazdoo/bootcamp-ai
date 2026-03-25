import fitz  # PyMuPDF

doc = fitz.open("facture_test.pdf")

print(f"Nombre de pages : {len(doc)}\n")

for i, page in enumerate(doc):
    texte = page.get_text()
    print(f"=== PAGE {i+1} ===")
    print(texte)

doc.close()