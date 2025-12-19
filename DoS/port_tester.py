from scapy.all import * 

def test_syn(target_ip, target_port):
    conf.verb = 0
    ip = IP(dst=target_ip)
    syn = TCP(dport=target_port, flags="S")
    syn_ack = sr1(ip/syn, timeout=2)
    if syn_ack.haslayer(TCP) and syn_ack[TCP].flags == "SA":
    	print(f"Portul {target_port} este deschis.")

if __name__ == "__main__":
    target_ip = "10.99.99.1"
    for  i in range (1,1000):
    	test_syn(target_ip, i)
