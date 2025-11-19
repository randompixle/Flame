# FlameShell package: ping
#require: subprocess
#require: platform

import subprocess
import platform

def run(args):
    if len(args) == 0:
        print("Usage: ping <host>")
        return

    host = args[0]

    # Windows uses different flags
    is_windows = platform.system().lower().startswith("win")

    count_flag = "-n" if is_windows else "-c"

    try:
        # Call real system ping
        subprocess.run(["ping", count_flag, "4", host])
    except Exception as e:
        print("ping error:", e)
