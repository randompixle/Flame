# FlameShell package manager (PKM)
# Allows installing commands from GitHub to Installed/
import os, sys, subprocess
import os
import re
import sys
import time
import zipfile
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
INSTALL_DIR = ROOT / "Installed"

# CHANGE THIS TO YOUR GITHUB PATH
GITHUB_BASE = "https://raw.githubusercontent.com/randompixle/Flame/main/FlameCommands/"

import shutil

def clear_line():
    width = shutil.get_terminal_size((80, 20)).columns
    sys.stdout.write("\r" + " " * width + "\r")
    sys.stdout.flush()


def print_error(msg, code=None):
    if code is not None:
        print(f"{msg} (error: {code})")
    else:
        print(f"{msg}")

def spinner(msg, duration=0.8):
    frames = ["-", "\\", "|", "/"]
    t_end = time.time() + duration
    i = 0

    while time.time() < t_end:
        clear_line()
        sys.stdout.write(f"{msg} {frames[i % len(frames)]}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1

    clear_line()



# ⭐ FIXED VERSION — NO MORE 147%
def download_with_progress(url, dest_path):
    print(f"getting... {dest_path.name}")
    r = requests.get(url, stream=True)

    if r.status_code == 404:
        print("github Error!: The file doesn't exist!")
        print_error("Error! the requested command doesn't exist!", 404)
        return False

    if r.status_code != 200:
        print(f"GitHub Error!: HTTP {r.status_code}")
        print_error("Error downloading from GitHub!", 2)
        return False

    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    chunk = 8192
    spinner("starting download...")

    with open(dest_path, "wb") as f:
        for c in r.iter_content(chunk_size=chunk):
            if not c:
                continue
            f.write(c)
            downloaded += len(c)

            if total > 0:
                bar_len = 22

                # ⭐ Clamp values so they never exceed max
                pct = min(int(downloaded * 100 / total), 100)
                filled = min(int(bar_len * downloaded / total), bar_len)

                bar = "#" * filled + "-" * (bar_len - filled)
                sys.stdout.write(f"\rflame: [{bar}] {pct}%")
                sys.stdout.flush()

    if total > 0:
        sys.stdout.write("\n")
    else:
        print("download complete (no size info)")

    return True


def validate_py_command(path: Path):
    try:
        code = path.read_text(errors="ignore")
    except:
        print_error("could not read downloaded file", 1)
        return False

    if "def run(" not in code:
        print_error("command isn't a proper Flame command!", 1)
        path.unlink(missing_ok=True)
        return False

    reqs = re.findall(r"#require:(.+)", code)
    if reqs:
        print("this command has requirements…")
        for req in reqs:
            req = req.strip()
            print(f"installing... {req}")
            os.system(f"pip install {req}")

    return True

def install_single_py(name: str):
    INSTALL_DIR.mkdir(exist_ok=True)

    url = GITHUB_BASE + name + ".py"
    dest = INSTALL_DIR / (name + ".py")

    if not download_with_progress(url, dest):
        return False

    if not validate_py_command(dest):
        return False

    print("Command installed! (code: 0)")
    return True

def install_zip_pack(name: str):
    INSTALL_DIR.mkdir(exist_ok=True)

    url = GITHUB_BASE + name + ".zip"
    dest = INSTALL_DIR / (name + ".zip")

    if not download_with_progress(url, dest):
        return False

    print("zip pack downloaded, extracting…")

    try:
        with zipfile.ZipFile(dest, "r") as z:
            z.extractall(INSTALL_DIR / name)
        dest.unlink()
        print("zip pack installed (code: 0)")
        return True
    except Exception as e:
        print_error(f"zip extraction failed: {e}", 3)
        return False

def install_command(name: str):
    py_path = INSTALL_DIR / (name + ".py")
    zip_path = INSTALL_DIR / name

    if py_path.exists() or zip_path.exists():
        print("command already installed, use: pkm update <name>")
        return

    if install_single_py(name):
        return

    print("trying .zip instead")
    install_zip_pack(name)

def update_command(name: str):
    py_path = INSTALL_DIR / (name + ".py")
    zip_folder = INSTALL_DIR / name
    zip_file = INSTALL_DIR / (name + ".zip")

    if py_path.exists():
        py_path.unlink()
        install_single_py(name)
        return

    if zip_folder.exists() or zip_file.exists():
        if zip_folder.exists():
            for root, dirs, files in os.walk(zip_folder, topdown=False):
                for f in files:
                    Path(root, f).unlink()
                for d in dirs:
                    Path(root, d).rmdir()
            zip_folder.rmdir()
        if zip_file.exists():
            zip_file.unlink()
        install_zip_pack(name)
        return

    print_error("command not installed, cannot update", 1)

def remove_command(name: str):
    py_path = INSTALL_DIR / (name + ".py")
    zip_folder = INSTALL_DIR / name
    zip_file = INSTALL_DIR / (name + ".zip")

    removed = False

    if py_path.exists():
        py_path.unlink()
        removed = True

    if zip_folder.exists():
        for root, dirs, files in os.walk(zip_folder, topdown=False):
            for f in files:
                Path(root, f).unlink()
            for d in dirs:
                Path(root, d).rmdir()
        zip_folder.rmdir()
        removed = True

    if zip_file.exists():
        zip_file.unlink()
        removed = True

    if removed:
        print("Command removed (code: 0)")
    else:
        print_error("command not found", 404)

def list_commands():
    print("Installed Commands:")
    if not INSTALL_DIR.exists():
        print(" (none)")
        return
    for f in sorted(INSTALL_DIR.glob("*.py")):
        print(" -", f.stem)
    for d in sorted(INSTALL_DIR.iterdir()):
        if d.is_dir():
            print(" -", d.name, "(pack)")

def help_text():
    print("pkm usage:")
    print("  pkm install <name>")
    print("  pkm update <name>")
    print("  pkm remove <name>")
    print("  pkm list")

def run(args):
    if not args:
        help_text()
        return

    sub = args[0]
    changed = False

    if sub == "install" and len(args) >= 2:
        install_command(args[1])
        changed = True
    elif sub == "update" and len(args) >= 2:
        update_command(args[1])
        changed = True
    elif sub == "remove" and len(args) >= 2:
        remove_command(args[1])
        changed = True
    elif sub == "list":
        list_commands()
        return
    else:
        help_text()
        return

    if not changed:
        return

    # ⭐ ENSURE CLEAN OUTPUT BEFORE RESTART ⭐
    sys.stdout.write("\r" + " " * 200 + "\r")
    sys.stdout.flush()

    # Finish progress bar output
    sys.stdout.write("\n")
    sys.stdout.flush()

    # Let terminal finish its redraw before restarting
    time.sleep(0.05)

    print("restarting Flame…")
    sys.stdout.flush()

    time.sleep(0.05)  # << absolutely required to avoid overlap

    term = Path(__file__).resolve().parents[1] / "Terminal.py"

    # ⭐ FULL REAL RESTART ⭐
    os.execv(sys.executable, ["python3", str(term)])

