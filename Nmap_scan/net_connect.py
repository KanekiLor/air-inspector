import subprocess
import re
import shlex
import ipaddress
import datetime
from typing import Tuple, Optional
 
 
class NetConnectError(Exception):
    pass
 
 
def run_cmd(cmd: str, timeout: int = 10) -> str:
    try:
        completed = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        raise NetConnectError(f"Command execution failed: {e}")
    if completed.returncode != 0:
        raise NetConnectError(f"Command `{cmd}` failed: {completed.stderr.strip()}")
    return completed.stdout.strip()
 
 
# ------------------ NetworkManager / nmcli helpers ------------------
 
def nmcli_available() -> bool:
    try:
        subprocess.run(["nmcli", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False
 
 
def connect_wifi_nmcli(ssid: str, password: Optional[str] = None, timeout: int = 20) -> None:
    if not nmcli_available():
        raise NetConnectError("nmcli not found. Install NetworkManager or use another method.")
 
    if password:
        cmd = f"nmcli device wifi connect {shlex.quote(ssid)} password {shlex.quote(password)}"
    else:
        cmd = f"nmcli device wifi connect {shlex.quote(ssid)}"
 
    try:
        out = run_cmd(cmd, timeout=timeout)
    except NetConnectError as e:
        raise NetConnectError(f"Failed to connect to Wi-Fi '{ssid}': {e}")
 
    
    if "successfully activated" not in out.lower() and "successfully activated" not in out:       
        active = get_active_ssid()
        if active != ssid:
            raise NetConnectError(f"nmcli did not confirm activation; active SSID is: {active}")
 
 
def get_active_ssid() -> Optional[str]:
    try:
        out = run_cmd("nmcli -t -f ACTIVE,SSID dev wifi")
    except NetConnectError:
        return None
    for line in out.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2 and parts[0] == "yes":
            return parts[1]
    return None
 
 
# ------------------ IP / route helpers ------------------
 
def get_iface_and_src_via_ip_route() -> Tuple[str, str]:
    out = run_cmd("ip route get 8.8.8.8")
    m_dev = re.search(r"\bdev\s+(\S+)", out)
    m_src = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", out)
    if not m_dev or not m_src:
        raise NetConnectError(f"Could not parse `ip route get` output: {out}")
    iface = m_dev.group(1)
    src = m_src.group(1)
    return iface, src
 
 
def get_prefix_for_iface(iface: str) -> int:
    out = run_cmd(f"ip -4 addr show dev {shlex.quote(iface)}")
    m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", out)
    if not m:
        raise NetConnectError(f"Could not find inet line for interface {iface}: {out}")
    return int(m.group(2))
 
 
def build_network_cidr(src_ip: str, prefix: int) -> str:
    intf = ipaddress.IPv4Interface(f"{src_ip}/{prefix}")
    network = intf.network
    return str(network)
 
 
# ------------------ nmap wrapper ------------------
 
def scan_with_nmap(cidr: str, output_file: Optional[str] = None, timeout: int = 120) -> str:
    cmd = f"nmap -sn {shlex.quote(cidr)} -oG -"
    try:
        out = run_cmd(cmd, timeout=timeout)
    except NetConnectError as e:
        raise NetConnectError(f"nmap scan failed: {e}")

    return out

 
 
# ------------------ small parser for nmap -oG output ------------------
 
def parse_nmap_grepable(out: str) -> list:
    results = []
    for line in out.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith("Host:"):
            m = re.search(r"Host:\s+(\d+\.\d+\.\d+\.\d+).*Status:\s+(\S+)", line)
            if m:
                ip = m.group(1)
                status = m.group(2)
                results.append({"ip": ip, "status": status, "raw": line})
    return results
 
 
 
def connect_and_scan(ssid: Optional[str], password: Optional[str], output_prefix: Optional[str] = None) -> dict:
    if ssid:
        connect_wifi_nmcli(ssid, password)
 
    iface, src = get_iface_and_src_via_ip_route()
    prefix = get_prefix_for_iface(iface)
    cidr = build_network_cidr(src, prefix)
 
    scan_out = scan_with_nmap(cidr, output_prefix)
 
    if isinstance(scan_out, str) and scan_out.endswith('.txt') and output_prefix:
        with open(scan_out, 'r', encoding='utf-8') as f:
            scan_text = f.read()
    else:
        scan_text = scan_out
 
    parsed = parse_nmap_grepable(scan_text)
 
    return {
        "iface": iface,
        "src_ip": src,
        "cidr": cidr,
        "scan_raw": scan_text,
        "scan_parsed": parsed,
    }
 
