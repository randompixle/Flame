# FlameShell help command
# Shows built-in + installed commands with descriptions

from pathlib import Path

YELLOW = "\033[33m"
BLUE   = "\033[36m"
RESET  = "\033[0m"

def run(args):
    print(f"{BLUE}FlameShell Help — Available Commands{RESET}\n")

    root = Path(__file__).resolve().parents[1]
    commands_folder = root / "Commands"
    installed_folder = root / "Installed"

    def get_description(path: Path):
        """Read first comment line as description."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        return line.lstrip("# ").strip()
                    if line:
                        break
        except:
            pass
        return ""

    def list_cmds(folder: Path, title: str):
        if not folder.exists():
            return
        print(f"{BLUE}{title}:{RESET}")
        for f in sorted(folder.glob("*.py")):
            if f.name == "__init__.py":
                continue
            name = f.stem
            desc = get_description(f)
            print(f"  {YELLOW}{name:<14}{RESET} {desc}")
        print()

    # Show built-in commands
    list_cmds(commands_folder, "Built-in Commands")

    # Show installed commands
    list_cmds(installed_folder, "Installed Commands")

    print(f"{BLUE}Usage:{RESET}")
    print("  help                Show this help menu")
    print("  <command> [args]    Run command")
    print()
