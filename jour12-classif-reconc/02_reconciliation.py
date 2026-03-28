import pandas as pd
import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(timeout=120.0)

# Charger les deux fichiers
journal = pd.read_csv("journal_comptable.csv")
releve = pd.read_csv("releve_banque.csv")

# Preparer le releve : creer une colonne montant unique
releve["debit"] = releve["debit"].fillna(0)
releve["credit"] = releve["credit"].fillna(0)
releve["montant"] = releve.apply(
    lambda r: r["credit"] if r["credit"] > 0 else -r["debit"], axis=1
)

print("=== JOURNAL COMPTABLE ===")
print(journal.to_string(index=False))
print(f"\n{len(journal)} ecritures")

print("\n=== RELEVE BANCAIRE ===")
print(releve.to_string(index=False))
print(f"\n{len(releve)} operations")

# --- Reconciliation automatique par date + montant ---
print("\n=== RECONCILIATION ===\n")

matches = []
journal_non_rapproche = journal.copy()
releve_non_rapproche = releve.copy()

for idx_j, row_j in journal.iterrows():
    montant_j = row_j["montant"] if row_j["type"] == "credit" else -row_j["montant"]
    date_j = row_j["date"]

    for idx_r, row_r in releve.iterrows():
        if idx_r not in releve_non_rapproche.index:
            continue
        if row_r["date"] == date_j and abs(row_r["montant"] - montant_j) < 0.01:
            matches.append({
                "date": date_j,
                "journal_ref": row_j["reference"],
                "journal_desc": row_j["description"],
                "releve_libelle": row_r["libelle"],
                "montant": row_j["montant"],
                "statut": "rapproche"
            })
            journal_non_rapproche = journal_non_rapproche.drop(idx_j)
            releve_non_rapproche = releve_non_rapproche.drop(idx_r)
            break

print(f"Ecritures rapprochees : {len(matches)}")
for m in matches:
    print(f"  {m['date']} | {m['journal_ref']} <-> {m['releve_libelle']} | {m['montant']} EUR")

print(f"\nJournal non rapproche : {len(journal_non_rapproche)} ecritures")
if len(journal_non_rapproche) > 0:
    print(journal_non_rapproche[["date", "reference", "description", "montant"]].to_string(index=False))

print(f"\nReleve non rapproche : {len(releve_non_rapproche)} operations")
if len(releve_non_rapproche) > 0:
    print(releve_non_rapproche[["date", "libelle", "montant"]].to_string(index=False))

# --- Analyse par Claude ---
print("\n=== ANALYSE CLAUDE ===\n")

resume = f"""Resultat de la reconciliation :
- {len(matches)} ecritures rapprochees sur {len(journal)} dans le journal et {len(releve)} dans le releve
- {len(journal_non_rapproche)} ecritures du journal non rapprochees
- {len(releve_non_rapproche)} operations du releve non rapprochees

Operations du releve non rapprochees :
{releve_non_rapproche[['date', 'libelle', 'montant']].to_string(index=False) if len(releve_non_rapproche) > 0 else 'Aucune'}

Ecritures du journal non rapprochees :
{journal_non_rapproche[['date', 'reference', 'description', 'montant']].to_string(index=False) if len(journal_non_rapproche) > 0 else 'Aucune'}
"""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    system="""Tu es un assistant comptable expert en reconciliation bancaire.
Analyse le resultat de la reconciliation et donne :
1. Un resume clair de la situation
2. L'explication probable des ecarts
3. Les actions a entreprendre
Reponds en francais.""",
    messages=[{"role": "user", "content": resume}]
)

print(response.content[0].text)