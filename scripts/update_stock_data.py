#!/usr/bin/env python3
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

# C25 stocks with Stooq tickers (.DK suffix for Copenhagen) and display symbols
# Stooq uses .DK for Copenhagen; some base symbols differ from Yahoo Finance
C25 = [
    {"stooq": "NOVO-B.DK",   "symbol": "NOVO-B.CO",      "name": "Novo Nordisk B"},
    {"stooq": "CARL-B.DK",   "symbol": "CARL-B.CO",      "name": "Carlsberg B"},
    {"stooq": "DANSKE.DK",   "symbol": "DANSKE.CO",      "name": "Danske Bank"},
    {"stooq": "MAERSK-B.DK", "symbol": "MAERSK-B.CO",    "name": "A.P. Møller-Mærsk B"},
    {"stooq": "MAERSK-A.DK", "symbol": "MAERSK-A.CO",    "name": "A.P. Møller-Cárgo A"},
    {"stooq": "ORSTED.DK",   "symbol": "ORSTED.CO",      "name": "Ørsted"},
    {"stooq": "DSV.DK",      "symbol": "DSV.CO",         "name": "DSV"},
    {"stooq": "COLOB.DK",    "symbol": "COLOPLAST-B.CO", "name": "Coloplast B"},
    {"stooq": "GMAB.DK",     "symbol": "GENMAB.CO",      "name": "Genmab"},
    {"stooq": "VWS.DK",      "symbol": "VESTAS.CO",      "name": "Vestas Wind Systems"},
    {"stooq": "ROCK-B.DK",   "symbol": "ROCKWOOL-B.CO",  "name": "Rockwool B"},
    {"stooq": "DEMANT.DK",   "symbol": "DEMANT.CO",      "name": "Demant"},
    {"stooq": "AMBU-B.DK",   "symbol": "AMBU-B.CO",      "name": "Ambu B"},
    {"stooq": "FLS.DK",      "symbol": "FLS.CO",         "name": "FLSmidth"},
    {"stooq": "GN.DK",       "symbol": "GN.CO",          "name": "GN Store Nord"},
    {"stooq": "ISS.DK",      "symbol": "ISS.CO",         "name": "ISS"},
    {"stooq": "JYSB.DK",     "symbol": "JYSK.CO",        "name": "Jyske Bank"},
    {"stooq": "NETC.DK",     "symbol": "NETC.CO",        "name": "Netcompany"},
    {"stooq": "NKT.DK",      "symbol": "NKT.CO",         "name": "NKT"},
    {"stooq": "PNDORA.DK",   "symbol": "PNDORA.CO",      "name": "Pandora"},
    {"stooq": "RBREW.DK",    "symbol": "RBREW.CO",       "name": "Royal Unibrew"},
    {"stooq": "SYDB.DK",     "symbol": "SYDB.CO",        "name": "Sydbank"},
    {"stooq": "TOP.DK",      "symbol": "TOPDK.CO",       "name": "Topdanmark"},
    {"stooq": "TDC.DK",      "symbol": "TDC.CO",         "name": "TDC Net"},
    {"stooq": "TRYG.DK",     "symbol": "TRYG.CO",        "name": "Tryg"},
]

STOOQ_URL = "https://stooq.com/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"


def fetch_quote(stock):
    url = STOOQ_URL.format(ticker=stock["stooq"])
    with urlopen(url, timeout=30) as response:
        content = response.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return None

    row = rows[0]
    try:
        close = float(row["Close"]) if row.get("Close") not in (None, "", "N/D") else None
        open_ = float(row["Open"]) if row.get("Open") not in (None, "", "N/D") else None
        prev_close = open_  # Stooq does not provide previous close directly; use open as proxy
        change = (close - prev_close) if (close is not None and prev_close is not None) else None
        change_pct = (change / prev_close * 100) if (change is not None and prev_close) else None
    except (ValueError, TypeError):
        return None

    return {
        "symbol": stock["symbol"],
        "shortName": stock["name"],
        "regularMarketPrice": close,
        "regularMarketChange": round(change, 4) if change is not None else None,
        "regularMarketChangePercent": round(change_pct, 4) if change_pct is not None else None,
        "regularMarketPreviousClose": prev_close,
        "currency": "DKK",
    }


def fetch_quotes():
    results = []
    for stock in C25:
        quote = fetch_quote(stock)
        if quote is None:
            quote = {
                "symbol": stock["symbol"],
                "shortName": stock["name"],
                "regularMarketPrice": None,
                "regularMarketChange": None,
                "regularMarketChangePercent": None,
                "regularMarketPreviousClose": None,
                "currency": "DKK",
            }
        results.append(quote)
    return results


def main():
    data = {
        "quoteResponse": {"result": fetch_quotes()},
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "Stooq",
    }
    Path("data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
