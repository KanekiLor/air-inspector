import argparse
import json
import sys
import time
import net_connect
import mitm_ettercap 


def main():
    parser = argparse.ArgumentParser(description="Connect to Wi-Fi (optional) and run an nmap ping-sweep on the active network.")
    parser.add_argument("--ssid", help="SSID to connect to (optional)")
    parser.add_argument("--password", help="Wi-Fi password (optional)")
    parser.add_argument("--no-connect", action="store_true", help="Do not attempt to connect; just use the currently active interface")
    parser.add_argument("--outprefix", default="nmap_ping", help="Prefix for saved nmap output files (if used)")
    args = parser.parse_args()

    dots = ['.  ', '.. ', '...']
    for _ in range(10):
        for l in dots:
            sys.stdout.write("\r Scanning for victims " + l)
            sys.stdout.flush()
            time.sleep(0.15)
            
    try:
        ssid = None if args.no_connect else args.ssid
        result = net_connect.connect_and_scan(ssid, args.password, args.outprefix)
    except net_connect.NetConnectError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
 
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
    
