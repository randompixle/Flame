import shutil
import sys


def run(args):
    size = shutil.get_terminal_size(fallback=(80, 24))
    blank = " " * size.columns
    for _ in range(size.lines):
        sys.stdout.write(f"\r{blank}\r\n")
    sys.stdout.write("\033[H")
    sys.stdout.flush()
