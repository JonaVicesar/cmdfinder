"""
To add a new command, create a new Program if it does not exists,
create a new command if it does not exists
"""

"""for now i create it just to add commands from the terminal
i can update the "new_program.py" to not repeat code 
 """

from cmdfinder.colors import GREEN, YELLOW, GRAY, RESET
from cmdfinder.core import search_program, normalize_key
from cmdfinder.data_io import load_data, save_data

def print_add_help():
    print(f"{YELLOW}Use: cf -a <program> <command> [alias] [description]{RESET}")
    print(f'{GRAY}Example: cf -a gh "gh auth login" "github login" "add a new account of github"{RESET}')
    print(f"{GRAY}The alias defines the name under which the search is performed. Without an alias, the command itself is used{RESET}")

def add_command(program_name, command, alias=None, description=None):
    data = load_data()

    program, score = search_program(program_name, data)
    if program is None or score < 40:
        program = program_name
        data[program] = {"program_description": "", "actions": {}}

    key_source = alias if alias else command
    key = normalize_key(key_source)

    actions = data[program].setdefault("actions", {})
    exist = actions.get(key, {"aliases": [], "description": "", "commands": []})

    aliases = list(exist.get("aliases", []))
    if alias and alias not in aliases:
        aliases.append(alias)

    commands = list(exist.get("commands", []))
    command_exists = command in commands
    if not command_exists:
        commands.append(command)

    actions[key] = {
        "aliases": aliases,
        "description": description or exist.get("description", ""),
        "commands": commands,
    }

    save_data(data)

    print(f"{GREEN}\u2713 {program} {key}{RESET}")
    if command_exists:
        print(f"{YELLOW}  (the command already exist, it wasn't duplicated){RESET}")
    else:
        print(f"{GREEN}  the command was added: {command}{RESET}")
    if alias:
        print(f"{GREEN}  alias: {alias}{RESET}")
    if description:
        print(f"{GREEN}  description: {description}{RESET}")
    return True