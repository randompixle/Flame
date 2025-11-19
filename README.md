# Flame v2

Flame v2 is a fully Python-powered terminal that loads built-in commands from `Commands/` and optional packages from `Installed/`. It keeps Linux utilities from overriding Flame behavior, provides colorful prompts, and offers a package manager (`pkm`) for installing new commands on the fly.

## Features
- Dynamic loading of built-in and installed commands with automatic reloads.
- Tab-completion for every available command.
- Safe error handling: broken commands are skipped with helpful logs.
- A Python-native package manager capable of downloading single-file commands or zip bundles, validating their structure, installing dependencies, and restarting Flame after every change.
- Core utilities implemented in Python (no shell passthrough) such as `ls`, `rm`, `mkdir`, `cat`, `clear`, `ping`, `help`, `echo`, and `exit`.

## Running Flame
```
python Terminal.py
```
The prompt displays as `flame:<cwd> $` with an orange `flame` label and a blue working directory. Only Flame commands are executed; if you enter an unknown command you will receive a `not found` message instead of falling through to the system shell.

## Built-in Commands
| Command | Description |
| --- | --- |
| `help` | Lists all available commands (built-in + installed). |
| `exit` | Exits Flame safely. |
| `ping <host>` | Performs four TCP reachability checks using Python sockets. |
| `clear` | Clears the visible terminal area using terminal-width detection. |
| `echo <text>` | Prints the provided text. |
| `mkdir <path>` | Creates a directory (parents included). |
| `rm <path>` | Removes files or directories recursively. |
| `cat <path>` | Prints the contents of a file. |
| `ls [path]` | Lists directory contents (directories are suffixed with `/`). |
| `pkm ...` | Manages third-party Flame commands (see below). |

## Package Manager (`pkm`)
The package manager installs Python commands into `Installed/`. Each command file must define a `run(args)` function. The PKM also scans for `#require:` comments inside command files and installs the listed Python packages before activating the command.

### Usage
```
pkm install <url> [name]   # download a single-file command (.py)
pkm install <zip-url>      # download a zip command pack
pkm update <name|--all>    # refresh commands from their original source
pkm remove <name>          # remove an installed command
pkm list                   # list installed commands and their sources
```

### Command Validation
- Every file must include a `def run(args)` definition. Files without it are rejected.
- Zip archives can contain multiple commands; each `.py` file becomes its own command. Names that collide with built-ins are skipped automatically.
- When a command references dependencies via `#require: moduleA, moduleB==1.0`, `pkm` installs them using `pip`.
- After installs, updates, or removals, Flame reloads automatically so new commands become available immediately.

## Directory Layout
```
Flame/
 ├── Terminal.py
 ├── Commands/
 │     ├── help.py
 │     ├── exit.py
 │     ├── ping.py
 │     ├── clear.py
 │     ├── echo.py
 │     ├── mkdir.py
 │     ├── rm.py
 │     ├── cat.py
 │     ├── ls.py
 │     └── pkm.py
 ├── Installed/
 │     └── .gitkeep
```

Place any manually created commands inside `Installed/` (one `.py` file per command with a `run(args)` function). Flame will pick them up on the next reload.
