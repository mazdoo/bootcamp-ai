import requests
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from datetime import datetime

# --- Crypto via CoinGecko ---
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
            resultats.append({
                "nom":       crypto["name"],
                "ticker":    crypto["symbol"].upper(),
                "prix":      crypto["current_price"],
                "haut":      crypto["high_24h"],
                "bas":       crypto["low_24h"],
                "variation": crypto["price_change_percentage_24h"],
                "type":      "crypto"
            })
        return resultats
    except Exception as e:
        print(f"Erreur crypto : {e}")
        return []


# --- Actions via Yahoo Finance ---
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
        variation   = ((prix - prix_veille) / prix_veille) * 100

        return {
            "nom":       nom,
            "ticker":    ticker,
            "prix":      prix,
            "haut":      haut,
            "bas":       bas,
            "variation": variation,
            "type":      "action"
        }
    except Exception as e:
        print(f"Erreur {ticker} : {e}")
        return None


# --- Analyse technique : signal achat/vente ---
def analyser_signal(ticker, type_actif):
    try:
        # Récupère 3 mois d'historique
        if type_actif == "crypto":
            symbole = ticker + "-USD"
        else:
            symbole = ticker

        historique = yf.download(symbole, period="3mo", interval="1d", progress=False)

        if historique.empty:
            return "⚪ Données insuffisantes"

        closes = historique["Close"].squeeze()

        # --- Indicateurs ---
        # Moyenne mobile 20 jours et 50 jours
        mm20 = closes.rolling(window=20).mean().iloc[-1]
        mm50 = closes.rolling(window=50).mean().iloc[-1]
        prix_actuel = closes.iloc[-1]

        # RSI (Relative Strength Index) sur 14 jours
        delta    = closes.diff()
        gains    = delta.where(delta > 0, 0)
        pertes   = -delta.where(delta < 0, 0)
        avg_gain = gains.rolling(window=14).mean().iloc[-1]
        avg_loss = pertes.rolling(window=14).mean().iloc[-1]
        rs       = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi      = 100 - (100 / (1 + rs))

        # --- Décision ---
        points = 0
        raisons = []

        if prix_actuel > mm20:
            points += 1
            raisons.append("Prix > MM20")
        else:
            points -= 1
            raisons.append("Prix < MM20")

        if mm20 > mm50:
            points += 1
            raisons.append("MM20 > MM50 (tendance haussière)")
        else:
            points -= 1
            raisons.append("MM20 < MM50 (tendance baissière)")

        if rsi < 35:
            points += 2
            raisons.append(f"RSI {rsi:.0f} — survendu (opportunité)")
        elif rsi > 70:
            points -= 2
            raisons.append(f"RSI {rsi:.0f} — suracheté (risque)")
        else:
            raisons.append(f"RSI {rsi:.0f} — neutre")

        if points >= 2:
            signal = "🟢 ACHAT"
        elif points <= -1:
            signal = "🔴 VENTE / ÉVITER"
        else:
            signal = "🟡 NEUTRE"

        return signal, raisons, closes, mm20, mm50, rsi

    except Exception as e:
        return "⚪ Erreur analyse", [str(e)], None, None, None, None


# --- Graphique pour un actif ---
def tracer_graphique(ax_prix, ax_rsi, closes, mm20, mm50, rsi, nom, signal):
    if closes is None:
        return

    ax_prix.plot(closes.index, closes.values, label="Prix", color="#1f77b4", linewidth=1.5)
    ax_prix.plot(closes.index, closes.rolling(20).mean(), label="MM20", color="orange", linewidth=1)
    ax_prix.plot(closes.index, closes.rolling(50).mean(), label="MM50", color="red", linewidth=1)
    ax_prix.set_title(f"{nom} — {signal}", fontsize=9, fontweight="bold")
    ax_prix.legend(fontsize=7)
    ax_prix.tick_params(axis='x', labelsize=6)
    ax_prix.tick_params(axis='y', labelsize=6)

    # RSI
    rsi_series = []
    delta = closes.diff()
    gains = delta.where(delta > 0, 0)
    pertes = -delta.where(delta < 0, 0)
    for i in range(len(closes)):
        if i < 14:
            rsi_series.append(None)
        else:
            avg_g = gains.iloc[i-14:i].mean()
            avg_l = pertes.iloc[i-14:i].mean()
            rs = avg_g / avg_l if avg_l != 0 else 100
            rsi_series.append(100 - (100 / (1 + rs)))

    ax_rsi.plot(closes.index, rsi_series, color="purple", linewidth=1)
    ax_rsi.axhline(70, color="red",   linestyle="--", linewidth=0.7)
    ax_rsi.axhline(30, color="green", linestyle="--", linewidth=0.7)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_ylabel("RSI", fontsize=7)
    ax_rsi.tick_params(axis='x', labelsize=6)
    ax_rsi.tick_params(axis='y', labelsize=6)


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

tous_les_actifs = []

# Récupération des prix
print("=" * 60)
print("         COURS EN TEMPS RÉEL + ANALYSE")
print("=" * 60)

print("\n📊 CRYPTOMONNAIES\n")
for actif in get_crypto_prices(cryptos):
    tous_les_actifs.append(actif)

print("\n📊 ACTIONS BOURSIÈRES\n")
for nom, ticker in actions.items():
    actif = get_stock_price(nom, ticker)
    if actif:
        tous_les_actifs.append(actif)

# Analyse et affichage console
resultats_texte = []
analyses = {}

for actif in tous_les_actifs:
    fleche = "📈" if actif["variation"] >= 0 else "📉"
    variation_str = f"+{actif['variation']:.2f}%" if actif["variation"] >= 0 else f"{actif['variation']:.2f}%"

    signal, raisons, closes, mm20, mm50, rsi = analyser_signal(actif["ticker"], actif["type"])
    analyses[actif["ticker"]] = (signal, raisons, closes, mm20, mm50, rsi)

    ligne = (
        f"{fleche} {actif['nom']} ({actif['ticker']}) : ${actif['prix']} | "
        f"{variation_str} | Haut : ${actif['haut']} | Bas : ${actif['bas']} | {signal}"
    )
    print(ligne)
    for r in raisons:
        print(f"   └─ {r}")
    resultats_texte.append(ligne)

# Sauvegarde texte
Path("outputs").mkdir(exist_ok=True)
Path("outputs/prix.txt").write_text("\n".join(resultats_texte), encoding="utf-8")
print(f"\nSauvegardé dans outputs/prix.txt")

# --- Graphiques ---
n = len(tous_les_actifs)
fig = plt.figure(figsize=(20, n * 3))
fig.suptitle(f"Analyse technique — {datetime.now().strftime('%d/%m/%Y %H:%M')}", fontsize=14, fontweight="bold")

gs = gridspec.GridSpec(n * 2, 1, hspace=0.6)

for i, actif in enumerate(tous_les_actifs):
    ax_prix = fig.add_subplot(gs[i * 2])
    ax_rsi  = fig.add_subplot(gs[i * 2 + 1], sharex=ax_prix)
    signal, raisons, closes, mm20, mm50, rsi = analyses[actif["ticker"]]
    tracer_graphique(ax_prix, ax_rsi, closes, mm20, mm50, rsi, actif["nom"], signal)

plt.savefig("outputs/graphiques.png", dpi=120, bbox_inches="tight")
print("Graphiques sauvegardés dans outputs/graphiques.png")
plt.show()