"""
Route Resolver for DATA_FILE, route to the .json file that contains the commands
"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "commands.json"

def load_data():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
