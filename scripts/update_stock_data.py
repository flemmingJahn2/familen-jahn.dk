#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

C25 = [
    {"ticker": "NOVO-B.CO", "name": "Novo Nordisk B"},
    {"ticker": "CARL-B.CO", "name": "Carlsberg B"},
    {"ticker": "DANSKE.CO", "name": "Danske Bank"},
    {"ticker": "MAERSK-B.CO", "name": "A.P. Møller-Mærsk B"},
    {"ticker": "MAERSK-A.CO", "name": "A.P. Møller-Cárgo A"},
    {"ticker": "ORSTED.CO", "name": "Ørsted"},
    {"ticker": "DSV.CO", "name": "DSV"},
    {"ticker": "COLOPLAST-B.CO", "name": "Coloplast B"},
    {"ticker": "GENMAB.CO", "name": "Genmab"},
    {"ticker": "VESTAS.CO", "name": "Vestas Wind Systems"},
    {"ticker": "ROCKWOOL-B.CO", "name": "Rockwool B"},
    {"ticker": "DEMANT.CO", "name": "Demant"},
    {"ticker": "AMBU-B.CO", "name": "Ambu B"},
    {"ticker": "FLS.CO", "name": "FLSmidth"},
    {"ticker": "GN.CO", "name": "GN Store Nord"},
    {"ticker": "ISS.CO", "name": "ISS"},
    {"ticker": "JYSK.CO", "name": "Jyske Bank"},
    {"ticker": "NETC.CO", "name": "Netcompany"},
    {"ticker": "NKT.CO", "name": "NKT"},
    {"ticker": "PNDORA.CO", "name": "Pandora"},
    {"ticker": "RBREW.CO", "name": "Royal Unibrew"},
    {"ticker": "SYDB.CO", "name": "Sydbank"},
    {"ticker": "TOPDK.CO", "name": "Topdanmark"},
    {"ticker": "TDC.CO", "name": "TDC Net"},
    {"ticker": "TRYG.CO", "name": "Tryg"},
]

FIELDS = ",".join(
    [
        "regularMarketPrice",
        "regularMarketChange",
        "regularMarketChangePercent",
        "regularMarketPreviousClose",
        "currency",
    ]
)


def fetch_quotes():
    params = urlencode(
        {
            "symbols": ",".join(stock["ticker"] for stock in C25),
            "fields": FIELDS,
        }
    )
    with urlopen(f"https://query1.finance.yahoo.com/v7/finance/quote?{params}", timeout=30) as response:
        payload = json.load(response)

    quotes = payload.get("quoteResponse", {}).get("result", [])
    if not quotes:
        raise RuntimeError("Ingen data modtaget fra Yahoo Finance")
    return quotes


def main():
    data = {
        "quoteResponse": {"result": fetch_quotes()},
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "Yahoo Finance",
    }
    Path("data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
