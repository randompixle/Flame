#!/usr/bin/env python3
import os, subprocess, readline, importlib, importlib.util
from pathlib import Path

COMMAND_FOLDER = Path(__file__).parent / "Commands"
INSTALLED_FOLDER = Path(__file__).parent / "Installed"
COMMANDS = {}

def load_commands():
    for file in os.listdir(COMMAND_FOLDER):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            try:
                module = importlib.import_module(f"Commands.{name}")
                COMMANDS[name] = module
            except Exception as e:
                print(f"[ERROR] Failed loading {name}: {e}")

def load_installed():
    if not INSTALLED_FOLDER.exists():
        return
    for file in INSTALLED_FOLDER.rglob("*.py"):
        name = file.stem
        try:
            spec = importlib.util.spec_from_file_location(f"installed_{name}", file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            COMMANDS[name] = module
        except Exception as e:
            print(f"[INSTALLED ERROR] {name}: {e}")

def setup_autocomplete():
    def comp(text, state):
        opts = [c for c in COMMANDS.keys() if c.startswith(text)]
        if "pkm".startswith(text):
            opts.append("pkm")
        opts = sorted(set(opts))
        return opts[state] if state < len(opts) else None

    readline.set_completer(comp)
    readline.parse_and_bind("tab: complete")

def make_prompt():
    cwd = os.getcwd().replace(str(Path.home()), "~")
    return f"\033[38;5;208mflame\033[0m:\033[38;5;39m{cwd}\033[0m $ "

def main():
    load_commands()
    load_installed()
    setup_autocomplete()

    while True:
        try:
            line = input(make_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            continue

        if not line:
            continue

        parts = line.split()
        cmd, args = parts[0], parts[1:]

        if cmd in COMMANDS:
            try:
                COMMANDS[cmd].run(args)
            except Exception as e:
                print(f"[CMD ERROR] {cmd}: {e}")

            continue

        print(f"{cmd}: command not found (FlameShell only)")

if __name__ == "__main__":
    main()
