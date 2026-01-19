from scapy.all import *
from threading import Thread, Event
from multiprocessing import Process, Manager
import subprocess
import shutil
import re
import pandas
import time
import os
from triangulate import triangulate


def list_wireless_interfaces():
    try:
        ifaces = get_if_list()
    except Exception:
        ifaces = []

    wireless = [i for i in ifaces if i.startswith(("wlan", "wlp", "wl", "mon"))]
    return wireless


def enable_monitor_mode(iface, run_check_kill=True):
    print(f"Attempting to enable monitor mode on {iface}...")

    try:
        before = set(get_if_list())
    except Exception:
        before = set()

    airmon = shutil.which("airmon-ng")
    global did_kill_processes, monitor_iface_created
    if airmon:
        if run_check_kill:
            try:
                print("Running: airmon-ng check kill (may stop network managers)")
                subprocess.run([airmon, "check", "kill"], check=False)
                did_kill_processes = True
            except Exception as e:
                print(f"Warning: failed to run airmon-ng check kill: {e}")

        try:
            print(f"Running: airmon-ng start {iface}")
            proc = subprocess.run([airmon, "start", iface], capture_output=True, text=True, check=False)
            out = proc.stdout + proc.stderr
            cand = None
            after = set(get_if_list())
            new = after - before
            if new:
                for n in new:
                    if n.endswith("mon") or n.startswith(iface):
                        cand = n
                        break
                if not cand:
                    cand = new.pop()
            else:
                m = re.search(r"(\w+mon)", out)
                if m:
                    cand = m.group(1)

            if cand:
                print(f"Monitor-mode interface looks like: {cand}")
                monitor_iface_created = cand
                return cand
            else:
                print("airmon-ng did not report a new interface; will try to use the original iface.")
        except Exception as e:
            print(f"Warning: failed to run airmon-ng start: {e}")

    try:
        print(f"Falling back to ip/iwconfig method for {iface}")
        subprocess.run(["ip", "link", "set", iface, "down"], check=False)
        subprocess.run(["iwconfig", iface, "mode", "monitor"], check=False)
        subprocess.run(["ip", "link", "set", iface, "up"], check=False)
        time.sleep(0.3)
        try:
            after = set(get_if_list())
            if iface in after:
                return iface
        except Exception:
            pass
    except Exception as e:
        print(f"Fallback failed: {e}")

    print("Monitor mode enabling did not change interface name; continuing with given iface.")
    return iface


def restore_services():
    airmon = shutil.which("airmon-ng")
    if airmon and did_kill_processes:
        try:
            print("Restoring services with: airmon-ng check restore")
            subprocess.run([airmon, "check", "restore"], check=False)
        except Exception as e:
            print(f"Warning: failed to run airmon-ng check restore: {e}")

    if airmon and monitor_iface_created:
        try:
            print(f"Stopping monitor interface {monitor_iface_created} with airmon-ng stop")
            subprocess.run([airmon, "stop", monitor_iface_created], check=False)
        except Exception as e:
            print(f"Warning: failed to stop monitor iface: {e}")

    systemctl = shutil.which("systemctl")
    if systemctl:
        for svc in ("NetworkManager", "wpa_supplicant"):
            try:
                subprocess.run([systemctl, "start", svc], check=False)
            except Exception:
                pass

networks = pandas.DataFrame(columns=["BSSID", "SSID", "dBm_Signal", "Channel", "Crypto"])
networks.set_index("BSSID", inplace=True)

interface = None
selected_bssid = None
scanning_active = False
did_kill_processes = False
monitor_iface_created = None


def _sniff_worker(iface, results_dict):
    def _callback(packet):
        if packet.haslayer(Dot11Beacon):
            bssid = packet[Dot11].addr2
            try:
                ssid = packet[Dot11Elt].info.decode()
            except:
                ssid = ""
            try:
                dbm_signal = packet.dBm_AntSignal
            except:
                dbm_signal = "N/A"
            stats = packet[Dot11Beacon].network_stats()
            channel = stats.get("channel")
            crypto = str(stats.get("crypto"))
            results_dict[bssid] = (ssid, dbm_signal, channel, crypto)

    sniff(prn=_callback, iface=iface)

def callback(packet):
    if not scanning_active:
        return

    if packet.haslayer(Dot11Beacon):
        bssid = packet[Dot11].addr2
        ssid = packet[Dot11Elt].info.decode()
        try:
            dbm_signal = packet.dBm_AntSignal
        except:
            dbm_signal = "N/A"
        stats = packet[Dot11Beacon].network_stats()
        channel = stats.get("channel")
        crypto = stats.get("crypto")
        networks.loc[bssid] = (ssid, dbm_signal, channel, crypto)


def print_all():
    while True:
        os.system("clear")
        header = f"Monitoring interface: {interface}"
        if selected_bssid:
            header += f"  (focused BSSID: {selected_bssid})"
        print(header + "\n")

        if selected_bssid and selected_bssid in networks.index:
            print(networks.loc[[selected_bssid]])
        else:
            print(networks)
        time.sleep(0.5)


def change_channel(iface, stop_event: Event):
    ch = 1
    while not stop_event.is_set():
        os.system(f"iwconfig {iface} channel {ch}")
        # switch channel from 1 to 14 each 0.5s
        ch = ch % 14 + 1
        for _ in range(5):
            if stop_event.is_set():
                break
            time.sleep(0.1)


def sniffing(selected_iface):
    global interface, selected_bssid, networks
    interface = selected_iface
    selected_bssid = None

    print(f"Starting initial scan for 14 seconds on {interface} (hopping channels)...")

    stop_event = Event()
    channel_changer = Thread(target=change_channel, args=(interface, stop_event))
    channel_changer.daemon = True
    channel_changer.start()

    manager = Manager()
    results_dict = manager.dict()

    sniff_proc = Process(target=_sniff_worker, args=(interface, results_dict))
    sniff_proc.start()

    time.sleep(14)

    sniff_proc.terminate()
    sniff_proc.join(timeout=2)
    if sniff_proc.is_alive():
        sniff_proc.kill()
        sniff_proc.join()

    stop_event.set()
    time.sleep(0.2)

    for bssid, (ssid, dbm, ch, crypto) in results_dict.items():
        networks.loc[bssid] = (ssid, dbm, ch, crypto)

    print(f"\nInitial scan complete. Found {len(networks)} networks.\n")

    snapshot = networks.copy()
    if snapshot.empty:
        print("No networks detected during the initial scan.")
        print("Continuing live scan without focus. Press Ctrl-C to stop.")
        try:
            sniff(prn=callback, iface=interface)
        except KeyboardInterrupt:
            print("Exiting.")
        return

    rows = []
    for bssid, row in snapshot.iterrows():
        rows.append((bssid, row.get('SSID', ''), row.get('Channel', ''), row.get('dBm_Signal', '')))

    print("\nDetected networks:")
    for idx, (bssid, ssid, ch, dbm) in enumerate(rows, start=1):
        print(f"  {idx}) SSID: '{ssid}'  BSSID: {bssid}  Channel: {ch}  Signal: {dbm}")

    choice = input(f"Choose a network to focus on [1-{len(rows)}] (default 1, 0=none): ")
    try:
        idx = int(choice) if choice.strip() else 1
    except ValueError:
        idx = 1

    if idx == 0:
        print("No focus selected. Continuing live scan without channel locking.")
        try:
            sniff(prn=callback, iface=interface)
        except KeyboardInterrupt:
            print("Exiting.")
        return

    if idx < 1 or idx > len(rows):
        idx = 1

    chosen_bssid, chosen_ssid, chosen_channel, _ = rows[idx - 1]

    print(f"\nFocusing on SSID '{chosen_ssid}' BSSID {chosen_bssid} on channel {chosen_channel}.")

    if chosen_channel:
        try:
            os.system(f"iwconfig {interface} channel {chosen_channel}")
            print(f"Set {interface} to channel {chosen_channel}\n")
        except Exception:
            print("Failed to set interface channel; continuing without locking.\n")

    results = triangulate(interface, chosen_bssid, chosen_ssid, chosen_channel)
    
    print("Triangulation complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    wireless_ifaces = list_wireless_interfaces()
    if not wireless_ifaces:
        print("No wireless interfaces detected by scapy.get_if_list() with common prefixes.")
        print("Please ensure you have at least one wireless interface (e.g. wlan0) and run as root.")
        exit(1)

    print("Available wireless interfaces:")
    for idx, iface in enumerate(wireless_ifaces, start=1):
        print(f"  {idx}) {iface}")

    choice = input(f"Choose an interface to focus on [1-{len(wireless_ifaces)}] (default 1): ")
    try:
        idx = int(choice) if choice.strip() else 1
    except ValueError:
        idx = 1

    if idx < 1 or idx > len(wireless_ifaces):
        idx = 1

    selected = wireless_ifaces[idx - 1]
    print(f"Selected interface: {selected}")
    
    enable_mon = input("Enable monitor mode? (required for scanning) [Y/n]: ")
    if enable_mon.strip().lower() not in ("n", "no"):
        selected = enable_monitor_mode(selected, run_check_kill=True)
        print(f"Using interface: {selected}")
    else:
        print("Proceeding without enabling monitor mode (scanning may fail).")
    
    try:
        sniffing(selected)
    finally:
        restore_services()
