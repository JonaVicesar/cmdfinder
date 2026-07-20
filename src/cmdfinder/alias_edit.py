"""
Add custom aliases to existing actions, direct from the command line 
Designed to address the language barrier: the
action is searched for/added in English (it comes from the catalog), but you can
add "eliminar rama" as an alias without modifying the original
"""

from cmdfinder.colors import GREEN, RED, YELLOW, GRAY, RESET
from cmdfinder.core import search_program, search_actions
from cmdfinder.data_io import load_data, save_data

def print_alias_help():
    print(f"{YELLOW}Use: cf alias <program> <action or command> <new alias>{RESET}")
    print(f'{GRAY}Example: cf alias git "delete branch" "eliminar rama"{RESET}')
    print(f"{GRAY}(if the action or alias contain spaces, they must be enclosed in quotation marks){RESET}")

def add_alias(program_name, query, new_alias):
    data = load_data()

    program, score = search_program(program_name, data)
    if program is None or score < 40:
        print(f"{RED}Program not found: '{program_name}'{RESET}")
        return False

    actions = data[program].get("actions", {})
    results = search_actions(query, actions)
    if not results:
        print(f"{RED}No action matched '{query}' in {program}{RESET}")
        return False

    #we choose the best match, just like in normal search
    _, key, info = results[0]

    aliases = info.setdefault("aliases", [])
    if new_alias in aliases:
        print(f"{YELLOW}'{new_alias}' it was already used as an alias for '{key}'{RESET}")
        return True

    aliases.append(new_alias)
    save_data(data)

    print(f"{GREEN}\u2713 Alias added: '{new_alias}' -> {program} {key}{RESET}")
    if len(results) > 1:
        print(f"{GRAY}(note: '{query}' matched more than one action; the one with the highest score was used: '{key}'){RESET}")
    return True