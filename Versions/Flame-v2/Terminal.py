import os
import sys
import readline
import importlib.util
import traceback
from typing import Dict, Callable, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDS_DIR = os.path.join(BASE_DIR, "Commands")
INSTALLED_DIR = os.path.join(BASE_DIR, "Installed")
os.environ.setdefault("FLAME_V2_HOME", BASE_DIR)

for required_dir in (COMMANDS_DIR, INSTALLED_DIR):
    if not os.path.isdir(required_dir):
        os.makedirs(required_dir, exist_ok=True)

COLOR_RESET = "\033[0m"
COLOR_FLAME = "\033[38;5;208m"
COLOR_CWD = "\033[34m"


class CommandError(Exception):
    """Raised when a command fails to execute."""


class CommandRegistry:
    def __init__(self) -> None:
        self._paths: Dict[str, str] = {}
        self.refresh()

    def refresh(self) -> None:
        self._paths.clear()
        for directory in (COMMANDS_DIR, INSTALLED_DIR):
            if not os.path.isdir(directory):
                continue
            for entry in os.listdir(directory):
                if entry.startswith("_") or not entry.endswith(".py"):
                    continue
                name = entry[:-3]
                path = os.path.join(directory, entry)
                self._paths[name] = path

    def available(self):
        return sorted(self._paths.keys())

    def load(self, name: str) -> Callable[[list], None]:
        path = self._paths.get(name)
        if not path:
            raise CommandError(f"Command '{name}' not found")
        spec_name = f"flame_v2_{name}_{abs(hash(path))}"
        spec = importlib.util.spec_from_file_location(spec_name, path)
        if spec is None or spec.loader is None:
            raise CommandError(f"Unable to load command '{name}'")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - diagnostic output is needed
            raise CommandError(f"Error loading command '{name}': {exc}") from exc
        if not hasattr(module, "run"):
            raise CommandError(f"Command '{name}' is missing a run() function")
        run_callable = getattr(module, "run")
        if not callable(run_callable):
            raise CommandError(f"Command '{name}' run attribute is not callable")
        return run_callable


class FlameTerminal:
    def __init__(self) -> None:
        self.registry = CommandRegistry()
        self.current_dir = BASE_DIR
        os.chdir(self.current_dir)
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer)

    def _completer(self, text: str, state: int) -> Optional[str]:
        options = [cmd for cmd in self.registry.available() if cmd.startswith(text)]
        if state < len(options):
            return options[state] + " "
        return None

    def format_prompt(self) -> str:
        cwd_display = os.path.relpath(os.getcwd(), BASE_DIR)
        if cwd_display == ".":
            cwd_display = "/"
        prompt = f"{COLOR_FLAME}flame{COLOR_RESET}:{COLOR_CWD}{cwd_display}{COLOR_RESET} $ "
        return prompt

    def execute_line(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        parts = line.split()
        command_name, args = parts[0], parts[1:]
        try:
            runner = self.registry.load(command_name)
            runner(args)
        except CommandError as err:
            print(f"Error: {err}")
        except SystemExit:
            raise
        except Exception:
            traceback.print_exc()
        finally:
            self.registry.refresh()

    def loop(self) -> None:
        while True:
            try:
                line = input(self.format_prompt())
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
            try:
                self.execute_line(line)
            except SystemExit:
                break


def main() -> None:
    terminal = FlameTerminal()
    terminal.loop()


if __name__ == "__main__":
    main()
