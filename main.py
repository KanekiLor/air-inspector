#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import csv
import glob
import datetime
import argparse
from pathlib import Path

from scapy.all import rdpcap, Dot11Elt, Dot11Beacon, Dot11ProbeResp, Dot11
from collections import defaultdict
from colorama import Fore, Style, init

init(autoreset=True)

def print_banner():
    banner = """ 
 █████╗ ██╗██████╗     ██╗███╗   ██╗███████╗██████╗ ███████╗ ██████╗ ████████╗ ██████╗ ██████╗ 
██╔══██╗██║██╔══██╗    ██║████╗  ██║██╔════╝██╔══██╗██╔════╝██╔════╝ ╚══██╔══╝██╔═══██╗██╔══██╗
███████║██║██████╔╝    ██║██╔██╗ ██║███████╗██████╔╝█████╗  ██║         ██║   ██║   ██║██████╔╝
██╔══██║██║██╔══██╗    ██║██║╚██╗██║╚════██║██╔═══╝ ██╔══╝  ██║         ██║   ██║   ██║██╔══██╗
██║  ██║██║██║  ██║    ██║██║ ╚████║███████║██║     ███████╗╚██████╗    ██║   ╚██████╔╝██║  ██║
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝
            Automated WPA2-WPA3 Pen-Testing Tool
                     Developed by: KanekiLor
                                                                                       
    """
    
    lights = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●"]

    os.system("clear" if os.name != "nt" else "cls")
    print(banner)

    for _ in range(10):
        for l in lights:
            sys.stdout.write("\r Initializing modules, checking tools   " + l)
            sys.stdout.flush()
            time.sleep(0.15)

    print("\n✔ AirInspector ready.\n")

def check_root():
    # Checks whether the script is executed with root privileges.
    if os.geteuid() != 0:
        print("[-] This script must be run with root privileges. Use sudo.")
        sys.exit(1)

def check_tools():
    # Checks required tools
    tools = [
        'ip',
        'iw',
        'iwconfig',
        'airodump-ng',
        'aircrack-ng',
        'airmon-ng',
        'hostapd-mana',
        'dnsmasq',
        'hydra',
        'hping3',
        'ettercap',
        'nmap',
        'macchanger',
        'rfkill',
        'systemctl',
        'tcpdump',
        'service',
    ]

    missing_tools = []

    for tool in tools:
        if not any(
            os.access(os.path.join(path, tool), os.X_OK) 
            for path in os.environ['PATH'].split(os.pathsep)
        ):
            missing_tools.append(tool)

    if missing_tools:
        print(f"[-] Missing required tools: {', '.join(missing_tools)}")
        sys.exit(1)
    else:
        print("[+] All required tools are present.")

def delete_old_scan_files(directory: Path = None):
    if directory is None:
        directory = Path(__file__).resolve().parent
    
    patterns = [
        "handshake*.cap",
        "handshake*.csv", 
        "scan_*.csv",
        "scan_*.cap",
        "extended_scan*.csv",
        "extended_scan*.cap",
        "rescan_*.csv",
        "rescan_*.cap",
    ]
    
    for pattern in patterns:
        for f in directory.glob(pattern):
            try:
                os.remove(f)
                print(f"Deleted old file: {f.name}")
            except Exception as e:
                print(f"Failed to delete {f.name}: {e}")


def print_menu():
    print("=" * 50)
    print("\n AirInspector Menu \n")
    print("=" * 50)
    print("WPA2 Attacks:")
    print("1. Password Cracker")
    print("2. DoS Attacks")
    print("3. MiTM Attacks")
    print("4. Launch Rogue AP")
    print("5. Sweep Network: Scan for Hosts")
    print("6. Triangulate AP Location")
    print("\n WPA3 Attacks:")
    print("7. DragonShift Attack")
    print("\n0. Exit")
    print("=" * 50)

def main():
    print_banner()
    check_root()
    check_tools()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    time.sleep(1)

    while True:
        os.system("clear")
        print_menu()
        choice = input("Select an option (0-8): ")
        if choice == "0":
            print("Exiting AirInspector. Goodbye!")
            break
        elif choice == "1":
            # WPA2 Password Cracker
            delete_old_scan_files() 
            os.system("clear")
            script_path = os.path.join(
            base_dir, "wpa2_crack", "main.py")
            subprocess.run(["python3", script_path])
            
        elif choice == "2":
            # DoS Attacks

            os.system("clear")
            script_path = os.path.join(base_dir, "DoS_Hping3", "main.py")
            subprocess.run(["python3", script_path])
        elif choice == "3":
            # MiTM Attacks

            os.system("clear")
            script_path = os.path.join(base_dir, "Nmap_scan", "main.py")
            subprocess.run(["python3", script_path])
        elif choice == "4":
            # Rogue AP

            os.system("clear")
            script_path = os.path.join(base_dir, "rogue_ap", "main.py")
            subprocess.run(["python3", script_path])
        elif choice == "5":
            # Sweep Network
            
            os.system("clear")
            script_path = os.path.join(base_dir, "Sweep", "main.py")
            subprocess.run(["python3", script_path])
        elif choice == "6":
            # Triangulate AP Location
            
            os.system("clear")
            script_path = os.path.join(base_dir, "Scapy_Scan", "scan.py")
            subprocess.run(["python3", script_path])
        elif choice == "7":
            # DragonShift Attack (WPA3)
            
            os.system("clear")
            script_path = os.path.join(base_dir, "Wpa3_DragonBLood", "dragonshift.py")
            subprocess.run(["python3", script_path])
        else:
            print("Invalid choice. Please select a valid option.")
    

    parser = argparse.ArgumentParser(
        description="Automated WPA2-WPA3 Pen-Testing tool."
    )
    # parser.add_argument(
    #     "-m", "--monitor",
    #     dest="monitor_interface",
    #     type=str,
    #     required=True,
    #     help="Interface to use in monitor mode."
    # )
    # parser.add_argument(
    #     "-r", "--rogue",
    #     dest="rogueAP_interface",
    #     type=str,
    #     required=False,
    #     help="Interface to use for Rogue AP during hostapd-mana launch."
    # )

    args = parser.parse_args()


if __name__ == "__main__":
    main()