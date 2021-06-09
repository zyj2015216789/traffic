package generator

import (
	"golang.org/x/net/ipv4"
	"log"
	"net"
	"time"
	"trafficGenerator/src/utils"
)

type RawSender struct {
	conn     *ipv4.RawConn
	MsgSent  uint64
	LastTime time.Time
}

func NewRawSenderNIC(network, nic string) RawSender {

	ipAddr, err := utils.GetIPv4Addr(nic)
	//fmt.Printf("ip addr %s", ipAddr.String())
	if err != nil {
		log.Fatalf("can not get ip from interface %s: %+v\n", nic, err)
	}
	return NewRawSender(network, ipAddr.String())
}

func NewRawSender(network, address string) RawSender {
	//fmt.Printf(">>>>> addr: %s, network %s\n", address, network)
	listener, err := net.ListenPacket(network, address)
	if err != nil {
		log.Fatal("can not create packet listener: ", err)
	}

	rawConn, err := ipv4.NewRawConn(listener)
	if err != nil {
		log.Fatal("can not create raw connection: ", err)
	}

	return RawSender{
		conn:     rawConn,
		MsgSent:  0,
		LastTime: time.Time{},
	}
}

func (sender *RawSender) Send(ipHeader *ipv4.Header, data []byte) uint64 {
	if err := sender.conn.WriteTo(ipHeader, data, nil); err != nil {
		log.Fatal("packet send error: ", err)
	} else {
		sender.MsgSent += 1
	}
	return uint64(20 + len(data))
}

func (sender *RawSender) Close() {
	err := sender.conn.Close()
	if err != nil {
		log.Fatal("connection close error: ", err)
	}
}

type UdpSender struct {
	conn     *net.UDPConn
	MsgSent  uint64
	LastTime time.Time
}

func NewUdpSender(address string) UdpSender {
	addr, err := net.ResolveUDPAddr("udp", address)
	if err != nil {
		log.Fatal("can not resolve UDP address: ", err)
	}

	conn, err := net.DialUDP("udp", nil, addr)
	if err != nil {
		log.Fatal("can not open connection: ", err)
	}

	return UdpSender{
		conn:     conn,
		MsgSent:  0,
		LastTime: time.Time{},
	}
}

func (sender *UdpSender) Send(data []byte) int {
	n, err := sender.conn.Write(data)
	if err != nil {
		log.Fatal("UDP send error: ", err)
	} else {
		sender.MsgSent += 1
	}
	return n
}

func (sender *UdpSender) Close() {
	err := sender.conn.Close()
	if err != nil {
		log.Fatal("connection close error: ", err)
	}
}

func (sender *UdpSender) RemoteAddr() string {
	return sender.conn.RemoteAddr().String()
}
