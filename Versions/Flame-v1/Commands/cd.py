import os
from pathlib import Path
PROTECTED=["/proc","/sys","/dev"]

def run(args):
    target = Path(args[0]).expanduser() if args else Path.home()
    real = target.resolve()
    if str(real) in PROTECTED:
        print(f"cd: refusing to enter protected: {real}")
        return
    try: os.chdir(real)
    except Exception as e: print(f"cd: {e}")
