BRAND_FEES: dict[str, float] = {
    "italika": 1000,
    "bajaj": 0,
}

BRANDS: dict[str, dict] = {
    "Bajaj": {
        "base_url": "https://www.motosbajaj.com.mx/",
        "filter": "bajaj",
        "galgo_fee": BRAND_FEES["bajaj"],
    },
    "Italika": {
        "base_url": "https://www.italika.mx/",
        "filter": "italika",
        "galgo_fee": BRAND_FEES["italika"],
    },
}

GSHEETS_INVENTORY = {
    "sheet_name": "[MKP] Precios",
    "worksheet": "price_data_mx",
}

GSHEETS_OUTPUT_SHEET = "[MKP - MX - Resultados] Monitoreo de precios"

LOG_PATH = "data/logs/price_diff_log.csv"