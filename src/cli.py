"""
Entrypoint of 'cf', decides what to do based on the arguments and
prints it
"""
import sys

from colors import (
    GREEN, BLUE, SKY_BLUE, RED, YELLOW, WHITE, GRAY, RESET,
)
from core import search_program, search_actions
from data_io import load_data, DATA_FILE
from tui.app import run_tui


def _print_result(key, info, score):
    print("key de mierda", info)
    print("find commands", info.get("commands"))
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
    print(f"{GRAY}Example: cf git delete branch  |   cf nmap{RESET}")

def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        _print_help()
        return

    data = load_data()

    if args and args[0] in ("add", "-a"):
        run_tui()

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
