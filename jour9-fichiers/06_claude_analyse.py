import pandas as pd
import anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

client = anthropic.Anthropic()

# Chemin du fichier CSV dans le même dossier que ce script
csv_path = Path(__file__).parent / "donnees.csv"

# Lire les données
df = pd.read_csv(csv_path)

# Vérifier que la colonne 'montant' existe
if "montant" not in df.columns:
    raise ValueError(f"La colonne 'montant' est introuvable. Colonnes disponibles : {df.columns.tolist()}")

# Convertir la colonne montant en numérique si besoin
df["montant"] = pd.to_numeric(df["montant"], errors="coerce")

# Supprimer les lignes où montant est vide ou invalide
df = df.dropna(subset=["montant"])

# Préparer un résumé pour Claude
resume = f"""Voici les données d'un fichier comptable :

COLONNES : {df.columns.tolist()}
NOMBRE DE LIGNES : {len(df)}
APERÇU :
{df.to_string(index=False)}

STATISTIQUES :
- Total montants : {df['montant'].sum():.2f} €
- Moyenne : {df['montant'].mean():.2f} €
- Min : {df['montant'].min():.2f} €
- Max : {df['montant'].max():.2f} €
"""

print(resume)