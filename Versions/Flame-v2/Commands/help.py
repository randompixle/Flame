import os
from textwrap import dedent


def _discover_commands():
    base = os.environ.get("FLAME_V2_HOME", os.getcwd())
    paths = []
    for folder in ("Commands", "Installed"):
        directory = os.path.join(base, folder)
        if not os.path.isdir(directory):
            continue
        for entry in sorted(os.listdir(directory)):
            if entry.startswith("_") or not entry.endswith(".py"):
                continue
            paths.append(entry[:-3])
    return paths


def run(args):
    commands = _discover_commands()
    print("Flame v2 built-in commands:")
    for name in commands:
        print(f"  - {name}")
    print()
    message = dedent(
        """
        Use `help <command>` for per-command details when available.
        Commands live inside Versions/Flame-v2 and run entirely within Flame.
        """
    ).strip()
    print(message)
