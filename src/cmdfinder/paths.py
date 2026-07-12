"""
Paths XDG of the Project (XDG for linux conventions)
"""
import os
from pathlib import Path

def _xdg_dir(env_var, default_relative):
    base = os.environ.get(env_var)
    if base:
        return Path(base) / "cmdfinder"
    return Path.home() / default_relative / "cmdfinder"

USER_DATA_DIR = _xdg_dir("XDG_DATA_HOME", ".local/share") #saves commands
CACHE_DIR = _xdg_dir("XDG_CACHE_HOME", ".cache") #saves the index of the catalog
# CONFIG_DIR = _xdg_dir("XDG_CONFIG_HOME", ".config")  # we don't use it, if we will need config files we're gonna use it