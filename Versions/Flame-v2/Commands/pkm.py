import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from io import BytesIO
from typing import Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

HOME = os.environ.get("FLAME_V2_HOME", os.path.dirname(os.path.abspath(__file__)))
INSTALLED_DIR = os.path.join(HOME, "Installed")
REGISTRY_FILE = os.path.join(INSTALLED_DIR, "pkm_registry.json")
DEFAULT_BRANCH = "main"


def _load_registry() -> Dict[str, Dict]:
    if not os.path.isfile(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return {}


def _save_registry(data: Dict[str, Dict]) -> None:
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def _terminal_width() -> int:
    try:
        import shutil as pyshutil
        return pyshutil.get_terminal_size(fallback=(80, 20)).columns
    except Exception:
        return 80


def _print_progress(progress: float, prefix: str = "Downloading") -> None:
    width = _terminal_width() - 12
    width = max(10, width)
    filled = int(width * progress)
    bar = "#" * filled + "-" * (width - filled)
    percent = int(progress * 100)
    print(f"\r{prefix} [{bar}] {percent}%", end="", flush=True)


def _clear_progress_line() -> None:
    width = _terminal_width()
    print("\r" + " " * width + "\r", end="", flush=True)


def _download(repo: str, item: str, branch: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/FlameCommands/{item}"
    try:
        with urlopen(url) as response:
            total = response.length or 0
            chunks: List[bytes] = []
            downloaded = 0
            while True:
                data = response.read(8192)
                if not data:
                    break
                chunks.append(data)
                downloaded += len(data)
                progress = (downloaded / total) if total else 0.0
                _print_progress(progress if total else 0.0)
            _clear_progress_line()
            return b"".join(chunks)
    except HTTPError as exc:
        _clear_progress_line()
        raise RuntimeError(f"HTTP error: {exc.code} {exc.reason}") from exc
    except URLError as exc:
        _clear_progress_line()
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def _write_file(target_path: str, content: bytes) -> None:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as handle:
        handle.write(content)


def _validate_command(path: str) -> None:
    spec = importlib.util.spec_from_file_location(f"pkm_validate_{abs(hash(path))}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load command for validation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    run_fn = getattr(module, "run", None)
    if run_fn is None or not callable(run_fn):
        raise RuntimeError(f"Command at {path} is missing run()")


def _requirements_from_text(text: str) -> List[str]:
    requirements = []
    for line in text.splitlines():
        if line.strip().startswith("#require:"):
            requirement = line.split(":", 1)[1].strip()
            if requirement:
                requirements.append(requirement)
    return requirements


def _install_requirements(reqs: List[str]) -> None:
    if not reqs:
        return
    cmd = [sys.executable, "-m", "pip", "install", *reqs]
    subprocess.run(cmd, check=False)


def _install_py(repo: str, item: str, branch: str, name_override: str = None) -> str:
    content = _download(repo, item, branch)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Downloaded file is not valid UTF-8") from exc
    requirements = _requirements_from_text(text)
    if requirements:
        _install_requirements(requirements)
    name = name_override or os.path.splitext(os.path.basename(item))[0]
    target_path = os.path.join(INSTALLED_DIR, f"{name}.py")
    _write_file(target_path, content)
    _validate_command(target_path)
    return name


def _install_zip(repo: str, item: str, branch: str) -> List[str]:
    content = _download(repo, item, branch)
    installed_names: List[str] = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive.extractall(temp_dir)
            for root, _dirs, files in os.walk(temp_dir):
                for entry in files:
                    if not entry.endswith(".py"):
                        continue
                    src_path = os.path.join(root, entry)
                    name = os.path.splitext(entry)[0]
                    dst_path = os.path.join(INSTALLED_DIR, entry)
                    shutil.copyfile(src_path, dst_path)
                    with open(src_path, "r", encoding="utf-8") as handle:
                        requirements = _requirements_from_text(handle.read())
                    if requirements:
                        _install_requirements(requirements)
                    _validate_command(dst_path)
                    installed_names.append(name)
    return installed_names


def _remove_installed(name: str) -> None:
    path = os.path.join(INSTALLED_DIR, f"{name}.py")
    if os.path.exists(path):
        os.remove(path)


def _restart_terminal() -> None:
    terminal_path = os.path.join(HOME, "Terminal.py")
    print("Restarting Flame v2...")
    os.execl(sys.executable, sys.executable, terminal_path)


def _print_usage() -> None:
    print("pkm usage:")
    print("  pkm install <owner/repo> <file.py|pack.zip> [--branch <branch>] [--name <alias>]")
    print("  pkm update <name>")
    print("  pkm remove <name>")
    print("  pkm list")
    print("  pkm restart")


def _install_command(args: List[str]) -> None:
    if len(args) < 2:
        _print_usage()
        return
    repo, item = args[0], args[1]
    branch = DEFAULT_BRANCH
    name_override = None
    idx = 2
    while idx < len(args):
        if args[idx] == "--branch" and idx + 1 < len(args):
            branch = args[idx + 1]
            idx += 2
        elif args[idx] == "--name" and idx + 1 < len(args):
            name_override = args[idx + 1]
            idx += 2
        else:
            print(f"Unknown option: {args[idx]}")
            return
    registry = _load_registry()
    try:
        if item.endswith(".zip"):
            installed_names = _install_zip(repo, item, branch)
            for name in installed_names:
                registry[name] = {
                    "repo": repo,
                    "item": f"{item}:{name}",
                    "branch": branch,
                    "type": "zip",
                }
                print(f"Installed {name} from pack {item}")
        else:
            name = _install_py(repo, item, branch, name_override=name_override)
            registry[name] = {
                "repo": repo,
                "item": item,
                "branch": branch,
                "type": "file",
            }
            print(f"Installed {name} from {repo}:{branch}")
    except RuntimeError as exc:
        print(f"pkm install error: {exc}")
        return
    _save_registry(registry)


def _update_command(args: List[str]) -> None:
    if len(args) != 1:
        _print_usage()
        return
    name = args[0]
    registry = _load_registry()
    record = registry.get(name)
    if not record:
        print(f"pkm: no record for {name}")
        return
    repo = record["repo"]
    branch = record.get("branch", DEFAULT_BRANCH)
    if record.get("type") == "zip":
        pack_name = record["item"].split(":", 1)[0]
        installed_names = _install_zip(repo, pack_name, branch)
        for installed in installed_names:
            registry[installed] = {
                "repo": repo,
                "item": f"{pack_name}:{installed}",
                "branch": branch,
                "type": "zip",
            }
        print(f"Updated pack {pack_name}")
    else:
        item = record["item"]
        _install_py(repo, item, branch, name_override=name)
        print(f"Updated {name}")
    _save_registry(registry)


def _remove_command(args: List[str]) -> None:
    if len(args) != 1:
        _print_usage()
        return
    name = args[0]
    registry = _load_registry()
    if name not in registry:
        print(f"pkm: {name} is not installed via pkm")
        return
    _remove_installed(name)
    del registry[name]
    _save_registry(registry)
    print(f"Removed {name}")


def _list_commands() -> None:
    registry = _load_registry()
    if not registry:
        print("No commands installed via pkm.")
        return
    for name, info in registry.items():
        branch = info.get("branch", DEFAULT_BRANCH)
        print(f"{name} -> {info['repo']} ({branch}) [{info.get('type')}] {info['item']}")


def run(args):
    if not args:
        _print_usage()
        return
    action = args[0]
    rest = args[1:]
    if action == "install":
        _install_command(rest)
    elif action == "update":
        _update_command(rest)
    elif action == "remove":
        _remove_command(rest)
    elif action == "list":
        _list_commands()
    elif action == "restart":
        _restart_terminal()
    else:
        _print_usage()
