import pandas as pd

# Lire le CSV
df = pd.read_csv("donnees.csv")

# Explorer les données
print("=== APERÇU ===")
print(df.head())  # 5 premières lignes

print("\n=== INFOS ===")
print(df.info())  # Types de colonnes, valeurs manquantes

print("\n=== STATISTIQUES ===")
print(df.describe())  # Stats sur les colonnes numériques

print("\n=== COLONNES ===")
print(df.columns.tolist())

print("\n=== DIMENSIONS ===")
print(f"{len(df)} lignes, {len(df.columns)} colonnes")

print("\n=== VALEURS UNIQUES (clients) ===")
print(df["client"].unique())

print("\n=== TOTAL DES MONTANTS ===")
print(f"{df['montant'].sum():.2f} €")