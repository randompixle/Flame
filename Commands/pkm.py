import ast
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

from builtins import FLAME_CONTEXT


class PackageManager:
    def __init__(self) -> None:
        self.context = FLAME_CONTEXT
        self.installed_dir = self.context.installed_dir
        self.manifest_path = self.context.manifest_path
        self.manifest: Dict[str, Dict[str, Dict[str, str]]] = {"commands": {}}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self.manifest_path.exists():
            try:
                self.manifest = json.loads(self.manifest_path.read_text())
            except json.JSONDecodeError:
                self.manifest = {"commands": {}}
        else:
            self.manifest_path.write_text(json.dumps({"commands": {}}, indent=2))
            self.manifest = {"commands": {}}

    def _save_manifest(self) -> None:
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2))

    def handle(self, args: List[str]) -> None:
        if not args:
            self._print_usage()
            return
        command = args[0]
        try:
            if command == "install" and len(args) >= 2:
                url = args[1]
                name = args[2] if len(args) >= 3 else None
                self.install(url, name)
            elif command == "remove" and len(args) == 2:
                self.remove(args[1])
            elif command == "list":
                self.list_commands()
            elif command == "update" and len(args) >= 2:
                target = args[1]
                if target == "--all":
                    for cmd in list(self.manifest["commands"].keys()):
                        self.update(cmd)
                else:
                    self.update(target)
            else:
                self._print_usage()
        except Exception as exc:
            print(f"pkm error: {exc}")

    def _print_usage(self) -> None:
        print("pkm usage:")
        print("  pkm install <url> [name]")
        print("  pkm update <name|--all>")
        print("  pkm remove <name>")
        print("  pkm list")

    def install(self, url: str, name: Optional[str]) -> None:
        if url.lower().endswith(".zip"):
            self._install_zip(url)
        else:
            self._install_single(url, name)
        self.context.request_restart("packages updated")

    def update(self, name: str) -> None:
        meta = self.manifest["commands"].get(name)
        if not meta:
            print(f"pkm: {name} is not installed")
            return
        source = meta.get("source")
        ctype = meta.get("type")
        if not source or not ctype:
            print(f"pkm: {name} has invalid metadata")
            return
        if ctype == "single":
            self._install_single(source, name, overwrite=True)
        elif ctype == "zip":
            member = meta.get("member")
            self._install_from_zip_member(source, member, name)
        else:
            print(f"pkm: unknown type for {name}")
            return
        self.context.request_restart("packages updated")

    def remove(self, name: str) -> None:
        target = self.installed_dir / f"{name}.py"
        if not target.exists():
            print(f"pkm: {name} is not installed")
            return
        try:
            target.unlink()
        except OSError as exc:
            print(f"pkm: failed to remove {name}: {exc}")
            return
        self.manifest["commands"].pop(name, None)
        self._save_manifest()
        print(f"removed {name}")
        self.context.request_restart("package removed")

    def list_commands(self) -> None:
        commands = self.manifest.get("commands", {})
        if not commands:
            print("no installed packages")
            return
        for name, meta in sorted(commands.items()):
            source = meta.get('source', 'unknown')
            print(f"{name} -> {source}")

    def _install_single(self, url: str, name: Optional[str], overwrite: bool = False) -> None:
        data = self._download(url)
        text = data.decode("utf-8")
        if not self._has_run(text):
            raise ValueError("downloaded command missing run()")
        command_name = name or Path(urlparse(url).path).stem
        if not command_name:
            raise ValueError("unable to determine command name")
        if self._is_reserved(command_name) and not overwrite:
            raise ValueError(f"{command_name} is reserved")
        destination = self.installed_dir / f"{command_name}.py"
        if destination.exists() and not overwrite:
            raise FileExistsError(f"{command_name} already exists")
        requirements = self._extract_requirements(text)
        destination.write_text(text)
        self._install_requirements(requirements)
        self.manifest["commands"][command_name] = {
            "source": url,
            "type": "single"
        }
        self._save_manifest()
        print(f"installed {command_name}")

    def _install_zip(self, url: str) -> None:
        data = self._download(url)
        buffer = io.BytesIO(data)
        installed_any = False
        with zipfile.ZipFile(buffer) as zf:
            members = [m for m in zf.namelist() if m.endswith('.py') and not m.endswith('/')]
            if not members:
                raise ValueError("zip archive contains no python commands")
            for member in members:
                text = zf.read(member).decode('utf-8')
                if not self._has_run(text):
                    print(f"skipping {member}: missing run()")
                    continue
                name = Path(member).stem
                if self._is_reserved(name):
                    print(f"skipping {name}: reserved")
                    continue
                destination = self.installed_dir / f"{name}.py"
                if destination.exists():
                    print(f"skipping {name}: already exists")
                    continue
                requirements = self._extract_requirements(text)
                destination.write_text(text)
                self._install_requirements(requirements)
                self.manifest["commands"][name] = {
                    "source": url,
                    "type": "zip",
                    "member": member
                }
                print(f"installed {name}")
                installed_any = True
        if installed_any:
            self._save_manifest()
        else:
            print("pkm: nothing installed from archive")

    def _install_from_zip_member(self, url: str, member: Optional[str], name: str) -> None:
        if not member:
            print(f"pkm: missing member path for {name}")
            return
        data = self._download(url)
        buffer = io.BytesIO(data)
        with zipfile.ZipFile(buffer) as zf:
            if member not in zf.namelist():
                print(f"pkm: {member} not found in archive")
                return
            text = zf.read(member).decode('utf-8')
            if not self._has_run(text):
                print(f"pkm: {name} missing run() in archive")
                return
            destination = self.installed_dir / f"{name}.py"
            destination.write_text(text)
            requirements = self._extract_requirements(text)
            self._install_requirements(requirements)
            print(f"updated {name}")
        self._save_manifest()

    def _download(self, url: str) -> bytes:
        with urlopen(url) as response:
            total = response.length or 0
            chunk = 64 * 1024
            received = 0
            buffer = io.BytesIO()
            while True:
                data = response.read(chunk)
                if not data:
                    break
                buffer.write(data)
                received += len(data)
                self._render_progress(received, total)
        if total:
            self._render_progress(total, total)
        print()
        return buffer.getvalue()

    def _render_progress(self, current: int, total: int) -> None:
        columns = shutil.get_terminal_size(fallback=(80, 20)).columns
        bar_width = max(10, min(40, columns - 20))
        if total:
            ratio = min(1, current / total)
            filled = int(bar_width * ratio)
            bar = '#' * filled + '-' * (bar_width - filled)
            label = f"{ratio * 100:5.1f}%"
        else:
            filled = 0
            bar = '-' * bar_width
            label = f"{current // 1024}KB"
        sys.stdout.write(f"\r[{bar}] {label}")
        sys.stdout.flush()

    def _has_run(self, text: str) -> bool:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return False
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'run':
                return True
        return False

    def _extract_requirements(self, text: str) -> List[str]:
        reqs: List[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith('#require:'):
                items = stripped.split(':', 1)[1]
                reqs.extend([item.strip() for item in items.split(',') if item.strip()])
        return reqs

    def _install_requirements(self, requirements: Iterable[str]) -> None:
        req_list = list(requirements)
        if not req_list:
            return
        cmd = [sys.executable, '-m', 'pip', 'install', *req_list]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"pkm: requirement install failed: {exc}")

    def _is_reserved(self, name: str) -> bool:
        existing = self.installed_dir / f"{name}.py"
        if existing.exists():
            return False
        return name in self.context.list_commands()


def run(args):
    manager = PackageManager()
    manager.handle(args)
