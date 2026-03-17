import subprocess
import re
import os
import sys

def run_dragonshift(iface_deauth, iface_rogue_ap):
    subprocess.run(["python3", "dragonshift.py", "-m", iface_deauth, "-r", iface_rogue_ap])


def get_wireless_interfaces():
    out = subprocess.run(["iw", "dev"], capture_output=True, text=True, check=False).stdout
    return re.findall(r"Interface\s+(\S+)", out)

def enable_monitor(iface: str) -> str | None:
    cmd = ["airmon-ng", "check", "kill"]
    subprocess.run(cmd)

    cmd = ["airmon-ng", "start", iface]
    subprocess.run(cmd)

    print(f"Monitor mode enabled on interface {iface}")

def main():
    if os.geteuid() != 0:
        print("[-] This script must be run with root privileges. Use sudo.")
        sys.exit(1)

    ifaces = get_wireless_interfaces()
    if not ifaces:
        print("[-] No wireless interfaces.")
        sys.exit(1)
    print("\nChoose which interface you want the rogue ap hosted on:")
    
    for i, ifc in enumerate(ifaces, 1):
        print(f"  {i}) {ifc}")
    while True:
        try:
            idx = int(input(f"Select [1-{len(ifaces)}]: "))
            if 1 <= idx <= len(ifaces):
                iface_rogue_ap = ifaces[idx-1]
                ifaces.remove(iface_rogue_ap)
                break
        except (ValueError, EOFError):
            pass
    

    print("\nChoose which interface you want in monitor mode:")
    for i, ifc in enumerate(ifaces ,1):
        print(f" {i}) {ifc}")
    while True:
        try:
            idx = int(input(f"Select [1-{len(ifaces)}]: "))
            if 1 <= idx <= len(ifaces):
                iface_deauth = ifaces[idx-1]
                break
        except (ValueError, EOFError):
            pass
    enable_monitor(iface_deauth)
    run_dragonshift(iface_deauth, iface_rogue_ap)

if __name__ == "__main__":
    main()