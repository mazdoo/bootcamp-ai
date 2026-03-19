import os
from pathlib import Path

# Savoir où tu es
print(os.getcwd())          # affiche le dossier actuel

# Construire un chemin qui marche partout
dossier = Path("Jour 2")
fichier = dossier / "data.txt"   # le / est une vraie opération !
print(fichier)              # Jour 2\data.txt

# Vérifier si un fichier existe
if fichier.exists():
    print("Le fichier existe")
else:
    print("Fichier introuvable")

# Lister tous les fichiers d'un dossier
for f in Path(".").iterdir():
    print(f.name)

# Créer un dossier s'il n'existe pas
Path("outputs").mkdir(exist_ok=True)