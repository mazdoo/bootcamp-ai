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
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&ids={ids_param}",
            timeout=10
        )
        data = response.json()
        results = []
        for crypto in data:
            results.append({
                "name":      crypto["name"],
                "ticker":    crypto["symbol"].upper(),
                "price":     crypto["current_price"],
                "high":      crypto["high_24h"],
                "low":       crypto["low_24h"],
                "change":    crypto["price_change_percentage_24h"],
                "type":      "crypto"
            })
        return results
    except Exception as e:
        print(f"Crypto error: {e}")
        return []


# --- Stocks via Yahoo Finance ---
def get_stock_price(name, ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        meta           = data["chart"]["result"][0]["meta"]
        price          = meta["regularMarketPrice"]
        high           = meta["regularMarketDayHigh"]
        low            = meta["regularMarketDayLow"]
        previous_close = meta["chartPreviousClose"]
        change         = ((price - previous_close) / previous_close) * 100

        return {
            "name":   name,
            "ticker": ticker,
            "price":  price,
            "high":   high,
            "low":    low,
            "change": change,
            "type":   "stock"
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


# --- Technical analysis: buy/sell signal ---
def analyze_signal(ticker, asset_type):
    try:
        symbol = ticker + "-USD" if asset_type == "crypto" else ticker
        history = yf.download(symbol, period="3mo", interval="1d", progress=False)

        if history.empty:
            return "⚪ Insufficient data", [], None, None, None, None

        closes = history["Close"].squeeze()

        # Moving averages
        ma20 = closes.rolling(window=20).mean().iloc[-1]
        ma50 = closes.rolling(window=50).mean().iloc[-1]
        current_price = closes.iloc[-1]

        # RSI (14 days)
        delta    = closes.diff()
        gains    = delta.where(delta > 0, 0)
        losses   = -delta.where(delta < 0, 0)
        avg_gain = gains.rolling(window=14).mean().iloc[-1]
        avg_loss = losses.rolling(window=14).mean().iloc[-1]
        rs       = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi      = 100 - (100 / (1 + rs))

        # Signal decision
        score = 0
        reasons = []

        if current_price > ma20:
            score += 1
            reasons.append("Price above MA20")
        else:
            score -= 1
            reasons.append("Price below MA20")

        if ma20 > ma50:
            score += 1
            reasons.append("MA20 > MA50 (uptrend)")
        else:
            score -= 1
            reasons.append("MA20 < MA50 (downtrend)")

        if rsi < 35:
            score += 2
            reasons.append(f"RSI {rsi:.0f} — oversold (opportunity)")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI {rsi:.0f} — overbought (risk)")
        else:
            reasons.append(f"RSI {rsi:.0f} — neutral")

        if score >= 2:
            signal = "🟢 BUY"
        elif score <= -1:
            signal = "🔴 SELL / AVOID"
        else:
            signal = "🟡 NEUTRAL"

        return signal, reasons, closes, ma20, ma50, rsi

    except Exception as e:
        return "⚪ Analysis error", [str(e)], None, None, None, None


# --- Chart for one asset ---
def plot_chart(ax_price, ax_rsi, closes, ma20, ma50, rsi, name, signal):
    if closes is None:
        return

    ax_price.plot(closes.index, closes.values, label="Price",  color="#1f77b4", linewidth=1.5)
    ax_price.plot(closes.index, closes.rolling(20).mean(), label="MA20", color="orange",  linewidth=1)
    ax_price.plot(closes.index, closes.rolling(50).mean(), label="MA50", color="red",     linewidth=1)
    ax_price.set_title(f"{name} — {signal}", fontsize=9, fontweight="bold")
    ax_price.legend(fontsize=7)
    ax_price.tick_params(axis='x', labelsize=6)
    ax_price.tick_params(axis='y', labelsize=6)

    # RSI line
    rsi_series = []
    delta  = closes.diff()
    gains  = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    for i in range(len(closes)):
        if i < 14:
            rsi_series.append(None)
        else:
            avg_g = gains.iloc[i-14:i].mean()
            avg_l = losses.iloc[i-14:i].mean()
            rs = avg_g / avg_l if avg_l != 0 else 100
            rsi_series.append(100 - (100 / (1 + rs)))

    ax_rsi.plot(closes.index, rsi_series, color="purple", linewidth=1)
    ax_rsi.axhline(70, color="red",   linestyle="--", linewidth=0.7)
    ax_rsi.axhline(30, color="green", linestyle="--", linewidth=0.7)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_ylabel("RSI", fontsize=7)
    ax_rsi.tick_params(axis='x', labelsize=6)
    ax_rsi.tick_params(axis='y', labelsize=6)


# --- Main program ---
cryptos = ["bitcoin", "ethereum"]
stocks = {
    "Apple":     "AAPL",
    "Microsoft": "MSFT",
    "Amazon":    "AMZN",
    "Nvidia":    "NVDA",
    "Tesla":     "TSLA",
    "Google":    "GOOGL",
    "Meta":      "META",
    "Netflix":   "NFLX"
}

all_assets = []

print("=" * 60)
print("       REAL-TIME PRICES + TECHNICAL ANALYSIS")
print("=" * 60)

print("\n📊 CRYPTOCURRENCIES\n")
for asset in get_crypto_prices(cryptos):
    all_assets.append(asset)

print("\n📊 STOCKS\n")
for name, ticker in stocks.items():
    asset = get_stock_price(name, ticker)
    if asset:
        all_assets.append(asset)

# Analysis + console output
text_results = []
analyses = {}

for asset in all_assets:
    arrow = "📈" if asset["change"] >= 0 else "📉"
    change_str = f"+{asset['change']:.2f}%" if asset["change"] >= 0 else f"{asset['change']:.2f}%"

    signal, reasons, closes, ma20, ma50, rsi = analyze_signal(asset["ticker"], asset["type"])
    analyses[asset["ticker"]] = (signal, reasons, closes, ma20, ma50, rsi)

    line = (
        f"{arrow} {asset['name']} ({asset['ticker']}) : ${asset['price']} | "
        f"{change_str} | High: ${asset['high']} | Low: ${asset['low']} | {signal}"
    )
    print(line)
    for reason in reasons:
        print(f"   └─ {reason}")
    text_results.append(line)

# Save to file
Path("outputs").mkdir(exist_ok=True)
Path("outputs/prices.txt").write_text("\n".join(text_results), encoding="utf-8")
print(f"\nSaved to outputs/prices.txt")

# --- Charts ---
n = len(all_assets)
fig = plt.figure(figsize=(20, n * 3))
fig.suptitle(f"Technical Analysis — {datetime.now().strftime('%m/%d/%Y %H:%M')}", fontsize=14, fontweight="bold")

gs = gridspec.GridSpec(n * 2, 1, hspace=0.6)

for i, asset in enumerate(all_assets):
    ax_price = fig.add_subplot(gs[i * 2])
    ax_rsi   = fig.add_subplot(gs[i * 2 + 1], sharex=ax_price)
    signal, reasons, closes, ma20, ma50, rsi = analyses[asset["ticker"]]
    plot_chart(ax_price, ax_rsi, closes, ma20, ma50, rsi, asset["name"], signal)

plt.savefig("outputs/charts.png", dpi=120, bbox_inches="tight")
print("Charts saved to outputs/charts.png")
plt.show()