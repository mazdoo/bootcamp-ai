from pathlib import Path

# Afficher le dossier actuel
print(Path.cwd())

# Lister les fichiers du dossier Jour 2
for f in Path(".").iterdir():
    print(f.name)

# Créer un dossier outputs
Path("outputs").mkdir(exist_ok=True)
print("Dossier outputs créé !")