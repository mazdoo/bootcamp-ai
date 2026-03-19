import requests
from pathlib import Path

# --- Crypto via CoinGecko (endpoint markets) ---
def get_crypto_prices(crypto_ids):
    try:
        ids_param = ",".join(crypto_ids)
        reponse = requests.get(
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&ids={ids_param}",
            timeout=10
        )
        donnees = reponse.json()
        resultats = []

        for crypto in donnees:
            prix      = crypto["current_price"]
            haut      = crypto["high_24h"]
            bas       = crypto["low_24h"]
            variation = crypto["price_change_percentage_24h"]

            fleche = "📈" if variation >= 0 else "📉"
            variation_str = f"+{variation:.2f}%" if variation >= 0 else f"{variation:.2f}%"

            resultats.append(
                f"{fleche} {crypto['name']} : ${prix} | {variation_str} | "
                f"Haut 24h : ${haut} | Bas 24h : ${bas}"
            )
        return resultats

    except requests.exceptions.ConnectionError:
        return ["Erreur : pas de connexion réseau."]
    except Exception as e:
        return [f"Erreur inattendue (crypto) : {e}"]


# --- Actions boursières via Yahoo Finance ---
def get_stock_price(nom, ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        reponse = requests.get(url, headers=headers, timeout=10)
        donnees = reponse.json()

        meta        = donnees["chart"]["result"][0]["meta"]
        prix        = meta["regularMarketPrice"]
        haut        = meta["regularMarketDayHigh"]
        bas         = meta["regularMarketDayLow"]
        prix_veille = meta["chartPreviousClose"]

        variation = ((prix - prix_veille) / prix_veille) * 100
        fleche = "📈" if variation >= 0 else "📉"
        variation_str = f"+{variation:.2f}%" if variation >= 0 else f"{variation:.2f}%"

        return (
            f"{fleche} {nom} ({ticker}) : ${prix} | {variation_str} | "
            f"Haut du jour : ${haut} | Bas du jour : ${bas}"
        )

    except requests.exceptions.ConnectionError:
        return f"Erreur : pas de connexion réseau."
    except Exception as e:
        return f"Erreur inattendue pour {ticker} : {e}"


# --- Sauvegarde ---
def sauvegarder(texte, nom_fichier):
    Path("outputs").mkdir(exist_ok=True)
    fichier = Path("outputs") / nom_fichier
    fichier.write_text(texte, encoding="utf-8")
    print(f"\nSauvegardé dans {fichier}")


# --- Programme principal ---
cryptos = ["bitcoin", "ethereum"]

actions = {
    "Apple":     "AAPL",
    "Microsoft": "MSFT",
    "Amazon":    "AMZN",
    "Nvidia":    "NVDA",
    "Tesla":     "TSLA",
    "Google":    "GOOGL",
    "Meta":      "META",
    "Netflix":   "NFLX"
}

resultats = []

print("=" * 60)
print("         COURS EN TEMPS RÉEL")
print("=" * 60)

# Crypto
print("\n📊 CRYPTOMONNAIES\n")
lignes_crypto = get_crypto_prices(cryptos)
for ligne in lignes_crypto:
    print(ligne)
    resultats.append(ligne)

# Actions
print("\n📊 ACTIONS BOURSIÈRES\n")
for nom, ticker in actions.items():
    ligne = get_stock_price(nom, ticker)
    print(ligne)
    resultats.append(ligne)

# Sauvegarde
sauvegarder("\n".join(resultats), "prix.txt")