import json
import logging
from src.config.settings import SRC_DIR

log = logging.getLogger(__name__)

def bajaj_filter(urls_scraped: list[str]) -> list[str]:
    urls = []
    for url in urls_scraped:
        if "product-page" in url and not any(x in url for x in ["balatas", "juego", "valvula", "balero", "biela"]):
            urls.append(url)
    return urls

def italika_filter(urls_scraped: list[str]) -> list[str]:
    urls = []
    for url in urls_scraped:
        if any(x in url for x in ["motocicleta", "motoneta", "cuatrimoto"]) and not any(x in url for x in ["motos", "refacciones", "accesorios", "morbidelli"]):
            urls.append(url)
    return urls

def compare_urls(urls_new: list[str], urls_old: list[str], brand_name: str) -> list[str]:
    # Comparar urls nuevas y agregarlas si no existen
    new_urls = [url for url in urls_new if url not in urls_old]
    if new_urls:
        urls_old.extend(new_urls)
        # Guardar el JSON actualizado en brand_urls/ para que step2 lo pueda leer
        with open(f"{SRC_DIR}/data/json/brand_urls/{brand_name.lower()}.json", "w") as f:
            json.dump({"urls": urls_old}, f, indent=4)
        log.info(f"Se agregaron {len(new_urls)} nuevas URLs y se guardaron en el JSON.")
        for url in new_urls:
            log.info(f"  Nueva URL: {url}")
    else:
        log.info("No se encontraron nuevas URLs para agregar.")