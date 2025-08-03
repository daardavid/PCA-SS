# import requests, pandas as pd
# from datetime import date

# API_KEY = "fqWYWOIpesPKFNfhbXZqfy8qAp9kZGvZ"
# BASE    = "https://financialmodelingprep.com/api/v3/historical-market-capitalization/{sym}"

# TICKERS = {
#     "BMW Group": "BMWYY",         # o BMW.DE
#     "Continental": "CTTAY",       # o CON.DE
#     "Denso": "DNZOY",             # o 6902.T
#     "Ford Motor": "F",
#     "General Motors": "GM",
#     "Honeywell International": "HON",
#     "LG Electronics": "LGEIY",    # o 066570.KS
#     "Nissan Motor": "NSANY",
#     "Panasonic Holdings": "PCRFY",
#     "Samsung Electronics": "SSNLF",
#     "Sony": "SONY",
#     "BYD": "BYDDY",
#     "Tesla": "TSLA",
#     "Volkswagen": "VWAGY",
#     "Volvo": "VLVLY",
#     "Geely": "GELYY",
# }

# # Fechas de corte: necesitaremos tres bloques (12 años / 5 años ≈ 3)
# BLOCKS = [
#     ("2011-01-01", "2015-12-31"),
#     ("2016-01-01", "2020-12-31"),
#     ("2021-01-01", "2022-12-31"),
# ]

# rows = []
# for company, ticker in TICKERS.items():
#     for start, end in BLOCKS:
#         url = f"{BASE.format(sym=ticker)}?from={start}&to={end}&apikey={API_KEY}&limit=2000"
#         data = requests.get(url, timeout=30).json()
#         # Nos quedamos solo con el último día hábil de cada año
#         for d in data:
#             yr = d["date"][:4]
#             if d["date"].endswith("12-31"):           # fue día hábil
#                 rows.append([company, yr, d["marketCap"]])
#             # Si 31‑dic fue festivo, tomamos la última cotización de ese año
#         # deduplicar por año, escogiendo la fecha más alta (31‑dic o anterior)
#     # opcional: time.sleep(0.2) si ves errores de rate‑limit

# df = (pd.DataFrame(rows, columns=["company", "year", "marketCap_USD"])
#         .drop_duplicates(subset=["company", "year"])
#         .sort_values(["company", "year"]))

# df.to_excel("market_cap_2011_2022.xlsx", index=False)
# print("Archivo generado: market_cap_2011_2022.xlsx")



# import requests, pandas as pd
# from datetime import datetime
# import time

# API_KEY = "fqWYWOIpesPKFNfhbXZqfy8qAp9kZGvZ"
# BASE    = "https://financialmodelingprep.com/api/v3/historical-market-capitalization/{sym}"

# TICKERS = {
#     "BMW Group": "BMWYY",         # o BMW.DE
#     "Continental": "CTTAY",       # o CON.DE
#     "Denso": "DNZOY",             # o 6902.T
#     "Ford Motor": "F",
#     "General Motors": "GM",
#     "Honeywell International": "HON",
#     "LG Electronics": "LGEIY",    # o 066570.KS
#     "Nissan Motor": "NSANY",
#     "Panasonic Holdings": "PCRFY",
#     "Samsung Electronics": "SSNLF",
#     "Sony": "SONY",
#     "BYD": "BYDDY",
#     "Tesla": "TSLA",
#     "Volkswagen": "VWAGY",
#     "Volvo": "VLVLY",
#     "Geely": "GELYY",
# }

# # Solo queremos estos tres ejercicios
# TARGET_YEARS = {2011, 2016, 2022}

# # Tres bloques porque el endpoint acepta máx. 5 años por llamada
# BLOCKS = [
#     ("2011-01-01", "2015-12-31"),
#     ("2016-01-01", "2020-12-31"),
#     ("2021-01-01", "2022-12-31"),
# ]

# rows = []
# for company, ticker in TICKERS.items():
#     for start, end in BLOCKS:
#         url = (f"{BASE.format(sym=ticker)}?from={start}&to={end}"
#                f"&apikey={API_KEY}&limit=2000")
#         data = requests.get(url, timeout=30).json()

#         # Guarda todas las fechas porque luego nos quedamos con la última de diciembre
#         for item in data:
#             y = int(item["date"][:4])
#             if y in TARGET_YEARS:
#                 rows.append([company, item["date"], item["marketCap"]])

#         time.sleep(0.3)   # margen para no sobrepasar 5 llamadas/min

# # ---- PULIDO FINAL ----------------------------------------------------------
# df = (pd.DataFrame(rows, columns=["company", "date", "marketCap_USD"])
#         .assign(date=lambda d: pd.to_datetime(d["date"]),
#                 year=lambda d: d["date"].dt.year)
#         .sort_values("date"))

# # Quedarnos con la **última** fecha disponible de cada año (31‑dic o día hábil previo)
# df_final = (df.groupby(["company", "year"], as_index=False)
#               .tail(1)                              # ya está ordenado; tail(1) ⇒ la fecha más tardía
#               .sort_values(["company", "year"]))

# df_final.to_excel("market_cap_2011_2016_2022.xlsx", index=False)

# print("Archivo generado: market_cap_2011_2016_2022.xlsx")
# print(df_final.head(20))   # muestra una vista rápida en consola


import requests, pandas as pd, time, sys

API_KEY  = "fqWYWOIpesPKFNfhbXZqfy8qAp9kZGvZ"          # ← tu key de FMP
BASE_URL = ("https://financialmodelingprep.com/"
            "api/v3/historical-market-capitalization/{sym}")

TICKERS = {
    "Hitachi":        "6501.T",       # mercado primario Tokio
    "Kia":            "000270.KS",    # Korea Exchange
    "LG Electronics": "066570.KS",    # Korea Exchange
    "Volvo":          "VOLV-B.ST",    # Nasdaq Stockholm
}

YEARS = {
    "Hitachi":        list(range(2011, 2023)),          # 2011‑2022
    "Kia":            list(range(2011, 2023)),
    "LG Electronics": list(range(2011, 2023)),
    "Volvo":          list(range(2011, 2016)),          # 2011‑2015
}

# ────────────────────────────────────────────────────────────────────────────
def fetch_cap(ticker: str, year: int) -> dict | None:
    """Devuelve {'date', 'marketCap_USD'} para el último día hábil de dic‑<year>."""
    url = (f"{BASE_URL.format(sym=ticker)}"
           f"?from={year}-12-01&to={year}-12-31"
           f"&apikey={API_KEY}")

    try:
        js = requests.get(url, timeout=30).json()
    except ValueError as exc:                  # respuesta no‑JSON
        print(f"⚠️  {ticker} {year}: respuesta no JSON → {exc}")
        return None
    except requests.exceptions.RequestException as exc:
        print(f"⚠️  {ticker} {year}: error de conexión → {exc}")
        return None

    if not isinstance(js, list):
        print(f"⚠️  {ticker} {year}: {js}")     # p. ej. {"Error":"..."} o str
        return None
    if not js:                                 # lista vacía
        return None

    latest = max(js, key=lambda x: x["date"])  # fecha más tardía de diciembre
    return {"date": latest["date"], "marketCap_USD": latest["marketCap"]}

# ────────────────────────────────────────────────────────────────────────────
rows = []
for company, ticker in TICKERS.items():
    for yr in YEARS[company]:
        cap = fetch_cap(ticker, yr)
        if cap:
            rows.append({
                "company":        company,
                "year":           yr,
                "date":           cap["date"],
                "marketCap_USD":  cap["marketCap_USD"],
            })
        else:
            print(f"⚠️  Sin datos para {company} {yr}")

        time.sleep(0.35)                       # ≤ 5 llamadas por minuto (plan free)

# ────────────────────────────────────────────────────────────────────────────
if not rows:
    sys.exit("⛔  No se recuperó ningún dato. Revisa API_KEY o tickers.")

df = pd.DataFrame(rows).sort_values(["company", "year"])
df.to_excel("market_cap_faltantes.xlsx", index=False)

print("\n✔️  Archivo generado: market_cap_faltantes.xlsx")
print(df.head(20))
