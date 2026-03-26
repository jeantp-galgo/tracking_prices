# No parece usarse
import os
from pathlib import Path
import requests
from urllib.parse import urlparse
from typing import Any
import re

def get_urls_from_firecrawl_map(url_list: Any):
    """ Obtiene las URLs de un sitio web desde la respuesta de Firecrawl """
    links = getattr(url_list, "links", []) or []
    tuplas_urls = [(link.url, link.title, link.description) for link in links]
    return [tupla[0] for tupla in tuplas_urls]