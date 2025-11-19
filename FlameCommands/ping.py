import subprocess, platform
GREEN="\033[32m"; RESET="\033[0m"

def run(args):
    if not args:
        print("Usage: ping <host>")
        return
    host=args[0]
    flag = "-n" if "win" in platform.system().lower() else "-c"
    print(f"{GREEN}Pinging {host} with 4 packets...{RESET}")
    try:
        subprocess.run(["ping",flag,"4",host])
    except Exception as e:
        print("ping error:", e)
