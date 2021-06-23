from scapy.all import *
from scapy.layers.inet import *
from scapy.layers.dhcp import *
from scapy.layers.dns import *

def send_tcp(dst_ip, dst_port, pkt_size=100, inter=0.05):
	src_port = RandShort()
	tcp_pkt = IP(dst=dst_ip) / TCP(sport=src_port,dport=dst_port, flags='S')
	if len(tcp_pkt)<pkt_size:
		tcp_pkt=tcp_pkt/Raw(RandString(size=pkt_size-8))
	send(tcp_pkt)

def send_udp(dst_ip,dst_port,pkt_size=100,inter=0.05):
	src_port=RandShort()
	udp_pkt=IP(dst=dst_ip) / UDP(sport=src_port, dport=dst_port)
	if len(udp_pkt) < pkt_size:
		udp_pkt = udp_pkt / Raw(RandString(size=pkt_size-20))
        send(udp_pkt)

def main(num, size, inter):

	send_tcp(dst_ip=RandIP(), dst_port=(10,9 + int(num)), pkt_size=int(size),inter=float(inter))
	send_udp(dst_ip=RandIP(), dst_port=(10,9 + int(num)), pkt_size=int(size),inter=float(inter))
if __name__=='__main__':
	#main(sys.argv[1], sys.argv[2], sys.argv[3])
        for i in range(10):
            main(1, 120, 1)
	#main(1,120,1)
