package generator

import (
	"fmt"
	"log"
	"net"
	"os"
)

type Receiver struct {
	c          *net.UDPConn
	pktReceive uint64
}

func NewReceiver(host string, port int) Receiver {
	addr, err := net.ResolveUDPAddr("udp", fmt.Sprintf("%s:%d", host, port))
	if err != nil {
		fmt.Println("Can't resolve address: ", err)
		os.Exit(1)
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		fmt.Println("Error listening:", err)
		os.Exit(1)
	}

	return Receiver{c: conn}
}

func (recv *Receiver) ReceiveMsg() (Msg, error) {
	var data [2048]byte
	n, _, err := recv.c.ReadFromUDP(data[0:])
	if err != nil {
		log.Println("read UDP data error: ", err)
	}

	return DecodeMsg(data[:n])
}

func (recv *Receiver) Close() {
	err := recv.c.Close()
	if err != nil {
		log.Fatal("UDP connection close error: ", err)
	}
}
