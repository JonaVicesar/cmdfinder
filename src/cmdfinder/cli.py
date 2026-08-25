"""
Entrypoint of 'cf', decides what to do based on the arguments and
prints it
"""
import sys

from cmdfinder.colors import (
    GREEN, BLUE, SKY_BLUE, RED, YELLOW, WHITE, GRAY, RESET,
)
from cmdfinder.core import search_program, search_actions
from cmdfinder.data_io import load_data, DATA_FILE

def _print_result(key, info, score):
    if score is None:
        print(f"\n{BLUE}\u25b8 {key}{RESET}")
    else:
        print(f"\n{BLUE}\u25b8 {key}{RESET} {GRAY}({score:.0f}%){RESET}")
    if info.get("description"): #i have the json in spanish xd, so most of the keys in the .json file are in spanish
        print(f"  {GRAY}{info['description']}{RESET}")
    for cmd in info.get("commands", []):
        print(f"  {GREEN}$ {cmd}{RESET}")

def _list_programs(data):
    print(f"{WHITE}Available programs:{RESET}")
    for name, info in sorted(data.items()):
        desc = info.get("descripcion_programa", "")
        print(f"  {SKY_BLUE}{name}{RESET}  {GRAY}{desc}{RESET}")

def _list_all_actions(program, data):
    actions = data[program].get("actions", {})
    print(f"{WHITE}All the commands of {program}:{RESET}")
    for key in sorted(actions.keys()):
        _print_result(key, actions[key], None)
    print()

def _print_help():
    print(f"{YELLOW}Use:{RESET}")
    print("  cf                        list all available programs")
    print("  cf <program>             list all the commands of this program")
    print("  cf <program> <action>    search specific action")
    print("  cf add or cf -a                  add a new command")
    print("  cf update [--all | <program>]    sync installed programs with the catalog")
    print("  cf rm <program> [-y]             remove an installed program")
    print(f"{GRAY}Example: cf git delete branch  |   cf nmap{RESET}")

def _cmd_update(args):
    from cmdfinder.remote_catalog import check_updates, install_program, CatalogError

    data = load_data()

    #cf update --all : sync everything flagged as updatable
    if args and args[0] in ("--all", "-A"):
        targets = sorted(check_updates())
        if not targets:
            print(f"{GREEN}Everything is up to date{RESET}")
            return
        failed = 0
        for name in targets:
            print(f"{SKY_BLUE}syncing {name}...{RESET}", end=" ", flush=True)
            try:
                program_data = install_program(name)
            except CatalogError as e:
                failed += 1
                print(f"{RED}failed: {e}{RESET}")
                continue
            n_actions = len(program_data.get("actions", {}))
            print(f"{GREEN}\u2713 ({n_actions} actions, your aliases kept){RESET}")
        if failed:
            sys.exit(1)
        return

    #cf update <program> : sync one program
    if args:
        target = " ".join(args)
        program, score = search_program(target, data)
        if program is None or score < 40:
            print(f"{RED}Program not found: '{target}'{RESET}")
            sys.exit(1)
        if target != program:
            print(f"{SKY_BLUE}(interpreting '{target}' as '{program}'){RESET}")
        if program not in check_updates():
            print(f"{GREEN}'{program}' is already up to date{RESET}")
            return
        try:
            install_program(program)
        except CatalogError as e:
            print(f"{RED}Could not update '{program}': {e}{RESET}")
            sys.exit(1)
        print(f"{GREEN}\u2713 '{program}' updated (your aliases kept){RESET}")
        return

    #bare cf update : list what can be updated
    updatable = check_updates()
    if not updatable:
        print(f"{GREEN}Everything is up to date{RESET}")
        return
    print(f"{WHITE}{len(updatable)} program(s) can be updated:{RESET}")
    for name in updatable:
        print(f"  {YELLOW}\u2191 {name}{RESET}")
    print(f"{GRAY}run 'cf update --all' or 'cf update <program>'{RESET}")

def _cmd_rm(args):
    from cmdfinder.remote_catalog import load_installed, uninstall_program

    data = load_data()
    yes = any(a in ("-y", "--yes") for a in args[1:])
    positional = [a for a in args[1:] if a not in ("-y", "--yes")]
    if not positional:
        print(f"{YELLOW}Use: cf rm <program> [-y]{RESET}")
        return

    target = " ".join(positional)
    program, score = search_program(target, data)
    if program is None or score < 40:
        print(f"{RED}'{target}' is not installed{RESET}")
        sys.exit(1)

    info = data[program]
    n_actions = len(info.get("actions", {}))
    installed = load_installed().get(program, {})
    print(f"'{program}': {n_actions} actions, installed version {installed.get('update', '?')}")

    if not yes:
        answer = input("remove it? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print(f"{YELLOW}aborted{RESET}")
            return

    uninstall_program(program)
    print(f"{GREEN}\u2713 '{program}' removed{RESET}")

def main():
    args = sys.argv[1:]

    #print help
    if args and args[0] in ("-h", "--help"):
        _print_help()
        return

    data = load_data()

    #add new commands, if the user just use -a or add open the tui
    if args and args[0] in ("add", "-a"):
        if len(args) == 1:
            from cmdfinder.tui.app import run_tui
            run_tui()
            return 

        # I WILL DISABLE THIS, IT DON'T WORKS THE WAY THAT I WANT :w
        """    
        from cmdfinder.add_command import add_command, print_add_help
        if len(args) not in (3, 4, 5):
            print_add_help()
            return
        program_name = args[1]
        command = args[2]
        alias = args[3] if len(args) >= 4 else None
        description = args[4] if len(args) == 5 else None
        add_command(program_name, command, alias, description)
        return """


    #sync installed programs with the catalog
    if args and args[0] == "update":
        _cmd_update(args[1:])
        return

    #remove an installed program
    if args and args[0] in ("rm", "uninstall"):
        _cmd_rm(args)
        return
    
    #FOR NOW I WILL NOT USE IT, THE BODY OF THE COMMAND MAY BE TOO LONG
    #and the matcheo could be confusing

    # add new aliases with just one command 
    """if args and args[0] in ("-e", "-edit"):
        from cmdfinder.alias_edit import add_alias, print_alias_help
        
        if len(args) != 4:
            print_alias_help()
            return
    
        _, program_name, query, new_alias = args
        add_alias(program_name, query, new_alias)
        return """

    #list available programs/comands
    if not args or args[0] == "--list":
        if not data:
            print(f"{RED}There's no data in {DATA_FILE}{RESET}")
            sys.exit(1)
        _list_programs(data)
        return
    
    if not data:
        print(f"{RED}There's no data in {DATA_FILE}{RESET}")
        sys.exit(1)

    program_name = args[0]
    program, score_prog = search_program(program_name, data)

    if program is None or score_prog < 40:
        print(f"{RED}Program not found: '{program_name}'{RESET}")
        _list_programs(data)
        sys.exit(1)

    if program != program_name:
        print(f"{SKY_BLUE}(interpreting '{program_name}' as '{program}'){RESET}")

    if len(args) == 1:
        _list_all_actions(program, data)
        return

    query = " ".join(args[1:])
    actions = data[program].get("actions", {})
    results = search_actions(query, actions)

    if not results:
        print(f"{RED}Didn't find any coincidences '{query}' in {program}{RESET}")
        sys.exit(1)

    print(f"{WHITE}results for {program} -> \"{query}\"{RESET}")
    for score, key, info in results[:5]:
        _print_result(key, info, score)
    print()

if __name__ == "__main__":
    main()
