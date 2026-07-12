"""
Communicates with the remote catalog

We make GET requests to .json files, stored in Github Raw
"""
import json
import time
import urllib.error
import urllib.request

from cmdfinder.data_io import load_data, save_data
from cmdfinder.paths import CACHE_DIR

# catalog repo
CATALOG_BASE_URL = "https://raw.githubusercontent.com/JonaVicesar/cmdfinder_catalog/refs/heads/main"
INDEX_URL = f"{CATALOG_BASE_URL}/index.json"
PROGRAM_URL_TEMPLATE = CATALOG_BASE_URL + "/catalog/{name}.json"

INDEX_CACHE_FILE = CACHE_DIR / "remote_index.json"
TTL_SECONDS = 60*5  # 5 minutes for now
TIMEOUT_SECONDS = 5

class CatalogError(Exception):
    """Any failure to communicate with the catalog (network, HTTP, invalid JSON)"""

def _download_json(url):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise CatalogError(f"The catalog answered {e.code} to {url}") from e
    except urllib.error.URLError as e:
        raise CatalogError(f"We couldn't connect to the catalog: {e.reason}") from e

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise CatalogError(f"The catalog returned an invalid JSON: {e}") from e

def get_index(force_updates=False):
    """
    {program_name: description} of everything available in the catalog,
    uses a locally cached copy if it's less than the ttl, to avoid
    calling the network on every search within the tui
    """
    if not force_updates and INDEX_CACHE_FILE.exists():
        ttl_now = time.time() - INDEX_CACHE_FILE.stat().st_mtime
        if ttl_now < TTL_SECONDS:
            with open(INDEX_CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)

    index = _download_json(INDEX_URL)

    INDEX_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return index

def download_program(name):
    url = PROGRAM_URL_TEMPLATE.format(name=name)
    data = _download_json(url)

    if isinstance(data, dict) and set(data.keys()) == {name}: #just to verify if is there's another {} wrapping the keys
        data = data[name]

    return data

def install_program(name):
    """
    Download a program from the catalog and link it to the local data (DATA_FILE) 
    If it already exists locally it is overwritten with the version from the catalog.
    """
    program_data = download_program(name)
    local_data = load_data()
    local_data[name] = program_data
    save_data(local_data)
    return program_data