import pandas as pd

df = pd.read_csv("donnees.csv")

# Créer un fichier Excel avec plusieurs onglets
with pd.ExcelWriter("rapport.xlsx", engine="openpyxl") as writer:
    # Onglet 1 : toutes les données
    df.to_excel(writer, sheet_name="Toutes les factures", index=False)

    # Onglet 2 : factures impayées
    impayes = df[df["statut"] == "impayé"]
    impayes.to_excel(writer, sheet_name="Impayés", index=False)

    # Onglet 3 : résumé par client
    par_client = df.groupby("client")["montant"].agg(["sum", "count"]).reset_index()
    par_client.columns = ["client", "total", "nb_factures"]
    par_client = par_client.sort_values("total", ascending=False)
    par_client.to_excel(writer, sheet_name="Par client", index=False)

print("✅ rapport.xlsx créé avec 3 onglets !")
print(f"   - Toutes les factures : {len(df)} lignes")
print(f"   - Impayés : {len(impayes)} lignes")
print(f"   - Par client : {len(par_client)} clients")