import builtins
import importlib.util
import shlex
import subprocess
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional


class FlameContext:
    """Runtime helpers exposed to commands via builtins.FLAME_CONTEXT."""

    def __init__(self, terminal: "FlameTerminal") -> None:
        self._terminal = terminal

    @property
    def root_dir(self) -> Path:
        return self._terminal.root_path

    @property
    def commands_dir(self) -> Path:
        return self._terminal.commands_path

    @property
    def installed_dir(self) -> Path:
        return self._terminal.installed_path

    @property
    def manifest_path(self) -> Path:
        return self._terminal.manifest_path

    def list_commands(self) -> List[str]:
        return sorted(self._terminal.commands.keys())

    def request_restart(self, reason: str = "") -> None:
        self._terminal.request_restart(reason)


class FlameTerminal:
    def __init__(self) -> None:
        self.root_path = Path(__file__).resolve().parent
        self.commands_path = self.root_path / "Commands"
        self.installed_path = self.root_path / "Installed"
        self.manifest_path = self.installed_path / "manifest.json"
        self.commands_path.mkdir(parents=True, exist_ok=True)
        self.installed_path.mkdir(parents=True, exist_ok=True)
        self.commands: Dict[str, Callable[[List[str]], None]] = {}
        self._restart_requested = False
        self._restart_reason: Optional[str] = None
        self.context = FlameContext(self)
        builtins.FLAME_CONTEXT = self.context
        self._readline = None
        self._load_commands()
        self._setup_readline()

    def _setup_readline(self) -> None:
        try:
            import readline
        except ImportError:
            self._readline = None
            return
        self._readline = readline
        readline.set_completer(self._complete)
        readline.parse_and_bind("tab: complete")

    def _complete(self, text: str, state: int) -> Optional[str]:
        options = [name for name in self.commands if name.startswith(text)]
        options.sort()
        if state < len(options):
            return options[state]
        return None

    def _load_commands_from(self, directory: Path, allow_override: bool) -> None:
        for path in sorted(directory.glob("*.py")):
            name = path.stem
            if not allow_override and name in self.commands:
                continue
            module_name = f"flame_cmd_{name}_{hash(path)}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if not spec or not spec.loader:
                print(f"[warn] unable to create spec for {path}")
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)  # type: ignore[union-attr]
            except Exception as exc:
                print(f"[warn] failed to load {name}: {exc}")
                traceback.print_exc()
                continue
            run_callable = getattr(module, "run", None)
            if not callable(run_callable):
                print(f"[warn] command '{name}' missing run()")
                continue
            self.commands[name] = run_callable  # type: ignore[assignment]

    def _load_commands(self) -> None:
        self.commands.clear()
        self._load_commands_from(self.commands_path, allow_override=False)
        self._load_commands_from(self.installed_path, allow_override=True)

    def request_restart(self, reason: str = "") -> None:
        self._restart_requested = True
        self._restart_reason = reason or "changes detected"

    def _apply_restart(self) -> None:
        self._load_commands()
        if self._readline:
            self._readline.set_completer(self._complete)
        if self._restart_reason:
            print(f"[flame] reloaded commands ({self._restart_reason})")
        self._restart_requested = False
        self._restart_reason = None

    def _prompt(self) -> str:
        cwd = Path.cwd()
        orange = "\033[38;5;208m"
        blue = "\033[34m"
        reset = "\033[0m"
        return f"{orange}flame{reset}:{blue}{cwd}{reset} $ "

    def run(self) -> None:
        while True:
            try:
                line = input(self._prompt())
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
            command_line = line.strip()
            if not command_line:
                continue
            should_exit = self._execute_line(command_line)
            if should_exit:
                break
            if self._restart_requested:
                self._apply_restart()

    def _execute_line(self, line: str) -> bool:
        try:
            args = shlex.split(line)
        except ValueError as exc:
            print(f"[flame] parse error: {exc}")
            return False
        if not args:
            return False
        cmd_name, cmd_args = args[0], args[1:]
        handler = self.commands.get(cmd_name)
        if handler:
            try:
                handler(cmd_args)
            except SystemExit:
                return True
            except Exception as exc:
                print(f"[flame] {cmd_name} failed: {exc}")
                traceback.print_exc()
            return False
        return self._run_system_command(args)

    def _run_system_command(self, args: List[str]) -> bool:
        try:
            completed = subprocess.run(args)
            if completed.returncode != 0:
                print(f"[flame] system command exited with {completed.returncode}")
            return False
        except FileNotFoundError:
            print(f"flame: command '{args[0]}' not found")
            return False
        except Exception as exc:
            print(f"[flame] system command failed: {exc}")
            return False


def main() -> None:
    terminal = FlameTerminal()
    try:
        terminal.run()
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
