#!/usr/bin/env python3
import json
import re
import unicodedata
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

# C25 stocks with site symbol, display name, and Nordnet match candidates
C25 = [
    {"symbol": "NOVO-B.CO",      "name": "Novo Nordisk B",      "matches": ["NOVO B", "NOVO-B", "NOVO NORDISK B"]},
    {"symbol": "CARL-B.CO",      "name": "Carlsberg B",         "matches": ["CARL B", "CARL-B", "CARLSBERG B"]},
    {"symbol": "DANSKE.CO",      "name": "Danske Bank",         "matches": ["DANSKE", "DANSKE BANK"]},
    {"symbol": "MAERSK-B.CO",    "name": "A.P. Møller-Mærsk B", "matches": ["MAERSK B", "MAERSK-B", "A P MOLLER MAERSK B"]},
    {"symbol": "MAERSK-A.CO",    "name": "A.P. Møller-Mærsk A", "matches": ["MAERSK A", "MAERSK-A", "A P MOLLER MAERSK A"]},
    {"symbol": "ORSTED.CO",      "name": "Ørsted",              "matches": ["ORSTED", "ØRSTED"]},
    {"symbol": "DSV.CO",         "name": "DSV",                 "matches": ["DSV", "DSV A/S"]},
    {"symbol": "COLOPLAST-B.CO", "name": "Coloplast B",         "matches": ["COLO B", "COLO-B", "COLOPLAST B"]},
    {"symbol": "GENMAB.CO",      "name": "Genmab",              "matches": ["GMAB", "GENMAB"]},
    {"symbol": "VESTAS.CO",      "name": "Vestas Wind Systems", "matches": ["VWS", "VESTAS", "VESTAS WIND SYSTEMS"]},
    {"symbol": "ROCKWOOL-B.CO",  "name": "Rockwool B",          "matches": ["ROCK B", "ROCK-B", "ROCKWOOL B"]},
    {"symbol": "DEMANT.CO",      "name": "Demant",              "matches": ["DEMANT"]},
    {"symbol": "AMBU-B.CO",      "name": "Ambu B",              "matches": ["AMBU B", "AMBU-B", "AMBU B A/S"]},
    {"symbol": "FLS.CO",         "name": "FLSmidth",            "matches": ["FLS", "FLSMIDTH"]},
    {"symbol": "GN.CO",          "name": "GN Store Nord",       "matches": ["GN", "GN STORE NORD"]},
    {"symbol": "ISS.CO",         "name": "ISS",                 "matches": ["ISS", "ISS A/S"]},
    {"symbol": "JYSK.CO",        "name": "Jyske Bank",          "matches": ["JYSK", "JYSKE BANK"]},
    {"symbol": "NETC.CO",        "name": "Netcompany",          "matches": ["NETC", "NETCOMPANY"]},
    {"symbol": "NKT.CO",         "name": "NKT",                 "matches": ["NKT", "NKT A/S"]},
    {"symbol": "PNDORA.CO",      "name": "Pandora",             "matches": ["PNDORA", "PANDORA"]},
    {"symbol": "RBREW.CO",       "name": "Royal Unibrew",       "matches": ["RBREW", "ROYAL UNIBREW"]},
    {"symbol": "SYDB.CO",        "name": "Sydbank",             "matches": ["SYDB", "SYDBANK"]},
    {"symbol": "TOPDK.CO",       "name": "Topdanmark",          "matches": ["TOP", "TOPDANMARK"]},
    {"symbol": "TDC.CO",         "name": "TDC Net",             "matches": ["TDC", "TDC NET"]},
    {"symbol": "TRYG.CO",        "name": "Tryg",                "matches": ["TRYG"]},
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
LANDING_URL = "https://www.nordnet.dk/markedet"
API_URL = "https://www.nordnet.dk/api/2/instrument_search/query/stocklist"


def normalize_text(value):
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().replace("&", " AND ")
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def build_empty_quote(stock):
    return {
        "symbol": stock["symbol"],
        "shortName": stock["name"],
        "regularMarketPrice": None,
        "regularMarketChange": None,
        "regularMarketChangePercent": None,
        "regularMarketPreviousClose": None,
        "currency": "DKK",
    }


def make_opener():
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def fetch_nordnet_results():
    opener = make_opener()
    with opener.open(LANDING_URL, timeout=30):
        pass

    params = {
        "apply_filters": "exchange_country=DK",
        "sort_order": "desc",
        "sort_attribute": "dividend_yield",
        "limit": "200",
        "offset": "0",
    }
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"client-id": "NEXT", "User-Agent": USER_AGENT},
    )

    with opener.open(request, timeout=30) as response:
        payload = json.load(response)

    return payload.get("results", [])


def build_lookup(results):
    lookup = {}
    for item in results:
        info = item.get("instrument_info", {})
        for candidate in (info.get("symbol"), info.get("name")):
            key = normalize_text(candidate)
            if key and key not in lookup:
                lookup[key] = item
    return lookup


def find_match(stock, lookup):
    exact_candidates = [stock["symbol"].replace(".CO", ""), stock["name"], *stock.get("matches", [])]
    for candidate in exact_candidates:
        item = lookup.get(normalize_text(candidate))
        if item:
            return item

    name_key = normalize_text(stock["name"])
    for key, item in lookup.items():
        if name_key and (name_key in key or key in name_key):
            return item

    return None


def build_quote(stock, item):
    if not item:
        return build_empty_quote(stock)

    info = item.get("instrument_info", {})
    price_info = item.get("price_info", {})
    diff = price_info.get("diff", {}) or {}
    last = price_info.get("last", {}) or {}
    close = price_info.get("close", {}) or {}

    price = last.get("price")
    previous_close = close.get("price")
    change = diff.get("diff")
    change_pct = price_info.get("diff_pct")

    return {
        "symbol": stock["symbol"],
        "shortName": info.get("name") or stock["name"],
        "regularMarketPrice": price,
        "regularMarketChange": round(change, 4) if isinstance(change, (int, float)) else None,
        "regularMarketChangePercent": round(change_pct, 4) if isinstance(change_pct, (int, float)) else None,
        "regularMarketPreviousClose": previous_close,
        "currency": info.get("currency") or "DKK",
    }


def fetch_quotes():
    results = fetch_nordnet_results()
    lookup = build_lookup(results)
    return [build_quote(stock, find_match(stock, lookup)) for stock in C25]


def main():
    data = {
        "quoteResponse": {"result": fetch_quotes()},
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "Nordnet",
    }
    Path("data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
