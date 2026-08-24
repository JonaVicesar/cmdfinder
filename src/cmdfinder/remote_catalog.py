"""
Communicates with the remote catalog

We make GET requests to .json files, stored in Github Raw
"""
import datetime
import json
import time
import urllib.error
import urllib.request

from cmdfinder.data_io import load_data, save_data
from cmdfinder.paths import CACHE_DIR, USER_DATA_DIR

# catalog repo
CATALOG_BASE_URL = "https://raw.githubusercontent.com/JonaVicesar/cmdfinder_catalog/refs/heads/main"
INDEX_URL = f"{CATALOG_BASE_URL}/index.json"
PROGRAM_URL_TEMPLATE = CATALOG_BASE_URL + "/catalog/{name}.json"

INDEX_CACHE_FILE = CACHE_DIR / "remote_index.json"
INSTALLED_PROGRAMS = USER_DATA_DIR / "installed_programs.json" 
TTL_SECONDS = 60*5  # 5 minutes for now
TIMEOUT_SECONDS = 5

_today = datetime.date.today().strftime("%d-%m-%y")

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

def _parse_date(value):
    """
    Parse an update field into a comparable (year, month, day) tuple.

    Accepts every format the catalog or old registries have used:
    'DD-MM-YY' (current), 'DD:MM:YYYY' (legacy), 'YYYY-MM-DD'.
Conversations
Conversations
Conversations
    Returns None if value is missing or unparseable.
    """
    if not isinstance(value, str):
        return None
    value = value.strip()
    for fmt in ("%d-%m-%y", "%d:%m:%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d/%m/%Y"):
        try:
            d = datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
        return (d.year, d.month, d.day)
    return None

def _load_installed():
    """Read INSTALLED_PROGRAMS, returns {} if it doesn't exist or is corrupt"""
    if not INSTALLED_PROGRAMS.exists():
        return {}
    try:
        with open(INSTALLED_PROGRAMS, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}

def _save_installed(registry):
    """
    Write INSTALLED_PROGRAMS

    Every entry is normalized before saving legacy dates ('22:08:2026')
    are rewritten as 'DD-MM-YY' so the file converges to a single format.
    """
    normalized = {}
    for name, info in sorted(registry.items()):
        if not isinstance(info, dict):
            continue
        parsed = _parse_date(info.get("update"))
        update = datetime.date(*parsed).strftime("%d-%m-%y") if parsed else _today
        normalized[name] = {
            "description": info.get("description", ""),
            "update": update,
        }

    INSTALLED_PROGRAMS.parent.mkdir(parents=True, exist_ok=True)
    with open(INSTALLED_PROGRAMS, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
        f.write("\n")

def _stamp_installed(name, program_data):
    """
    Register a program in INSTALLED_PROGRAMS with the version it has in the index_catalog
    """
    try:
        entry = get_index().get(name) or {}
        update, description = entry.get("update"), entry.get("description")
    except CatalogError:
        update, description = None, None

    if not _parse_date(update):
        update = _today

    registry = _load_installed()
    registry[name] = {
        "description": description or program_data.get("program_description", ""),
        "update": update,
    }
    _save_installed(registry)

def install_program(name):
    """
    Download a program from the catalog and link it to the local data (DATA_FILE) 
    If it already exists locally it is overwritten with the version from the catalog.
    Now very install is registered in INSTALLED_PROGRAMS with its catalog version  
    """
    program_data = download_program(name)
    local_data = load_data()
    local_data[name] = program_data
    save_data(local_data)
    _stamp_installed(name, program_data)
    return program_data

def check_updates():
    """
    Compare the version registered at INSTALLED_PROGRAMS against
    the catalog index cache, returning the names of programs with a newer
    version in the catalog
    """
    installed_programs = _load_installed()
    updatable = []

    if not installed_programs or not INDEX_CACHE_FILE.exists():
        return updatable

    try:
        with open(INDEX_CACHE_FILE, encoding="utf-8") as f:
            cached_index = json.load(f)
    except (json.JSONDecodeError, OSError):
        return updatable

    if not isinstance(cached_index, dict):
        return updatable

    for key, installed_info in installed_programs.items():
        catalog_entry = cached_index.get(key)
        if not isinstance(catalog_entry, dict):
            continue

        installed_version = _parse_date(installed_info.get("update"))
        catalog_version = _parse_date(catalog_entry.get("update"))

        if installed_version is None or catalog_version is None:
            continue

        if catalog_version > installed_version:
            updatable.append(key)

    return sorted(updatable)
