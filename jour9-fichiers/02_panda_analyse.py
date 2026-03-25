import pandas as pd

df = pd.read_csv("donnees.csv")

# --- FILTRER ---
print("=== FACTURES IMPAYÉES ===")
impayes = df[df["statut"] == "impayé"]
print(impayes)
print(f"\nTotal impayés : {impayes['montant'].sum():.2f} €")

# --- TRIER ---
print("\n=== TRIÉES PAR MONTANT (décroissant) ===")
print(df.sort_values("montant", ascending=False))

# --- GROUPER PAR CLIENT ---
print("\n=== TOTAL PAR CLIENT ===")
par_client = df.groupby("client")["montant"].sum().sort_values(ascending=False)
print(par_client)

# --- GROUPER PAR STATUT ---
print("\n=== TOTAL PAR STATUT ===")
par_statut = df.groupby("statut")["montant"].agg(["sum", "count"])
par_statut.columns = ["total", "nb_factures"]
print(par_statut)

# --- GROUPER PAR MOIS ---
print("\n=== TOTAL PAR MOIS ===")
df["date"] = pd.to_datetime(df["date"])
df["mois"] = df["date"].dt.strftime("%Y-%m")
par_mois = df.groupby("mois")["montant"].sum()
print(par_mois)

# --- FILTRE COMBINÉ ---
print("\n=== IMPAYÉS > 3000€ ===")
gros_impayes = df[(df["statut"] == "impayé") & (df["montant"] > 3000)]
print(gros_impayes)