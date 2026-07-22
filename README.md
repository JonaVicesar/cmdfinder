# cmdfinder

cmdfinder is a program that helps you find commands quickly and easily. Its main purpose is to be useful when you're in a hurry and can't remember a command. 

Its syntax allows you to use everyday words or simple definitions to find any command. The program uses aliases for each command, and you can also add your own aliases and commands. It's not meant to complicate things; it simply lets you stay in the terminal without having to go to Google to search for a command or spend tokens on it. 

It has TUI that allows you to install new commands or programs, we use Github to store programs, so you just download those that use.

It is still in development, so I'm working in some features or could be some bugs. 

## Install

```bash
git clone https://github.com/JonaVicesar/cmdfinder.git
cd cmdfinder
pip install .
```

## Usage

```
cf                          # list all available programs
cf git                      # list all git actions
cf git eliminar              # fuzzy search: "eliminar" in git actions
cf add                      # open TUI to add commands
cf -a gh "gh auth login" "github login"  # add from CLI
```

### Example

```
$ cf git remov branch
results for git -> "remov branch"

▸ delete-branch (87%)
  Deletes a local or remote branch
  $ git branch -d <branch>
  $ git branch -D <branch>  # force delete even if not merged
  $ git push origin --delete <branch>  # delete remote branch
```

## How it works

Each program has **actions** with **aliases** natural language synonyms for what you want to do. When you search, `cf` scores every alias against your query using fuzzy matching (0-100%) and shows the best matches.

Aliases can be anything: `"eliminar rama"`, `"delete branch"`, `"kill branch"`, `"get rid of branch"`, `"la cague"`. The more synonyms, the easier it is to find what you need.

## Adding commands

**Interactive TUI:**
```bash
cf add
```

Programs and commands are stored in `~/.local/share/cmdfinder/commands.json`. 

You can also install programs from the [remote catalog](https://github.com/JonaVicesar/cmdfinder_catalog) via `cf add`.

## License

[MIT](LICENSE)
