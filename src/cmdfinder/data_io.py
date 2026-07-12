"""
Route Resolver for DATA_FILE, route to the .json file that contains the commands
"""
import json 
import shutil
from pathlib import Path
 
from cmdfinder.paths import USER_DATA_DIR
 
SEED_FILE = Path(__file__).parent / "data" / "commands.json"  # this will be default file "installed" when you use the 'cf' command for the first time

DATA_FILE = USER_DATA_DIR / "commands.json" # this will be the main file (user data) that the program will update, overwrite with the new commands that the user downloads
 
def _verify_seed_file():
    """The first time that 'cf' is used, the seed is copied to the user data file"""
    if not DATA_FILE.exists() and SEED_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SEED_FILE, DATA_FILE)
 
def load_data():
    _verify_seed_file()
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)
  
def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

