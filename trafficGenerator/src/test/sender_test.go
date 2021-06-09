package test

import (
	"fmt"
	"net"
	"testing"
	"trafficGenerator/src/generator"
)

func TestRawSender(t *testing.T) {
	sender := generator.NewRawSender("ip4:udp", "0.0.0.0")
	defer sender.Close()

	send(&sender, t)
}

func TestRawSenderNIC(t *testing.T) {
	sender := generator.NewRawSenderNIC("ip4:udp", "ens33")
	defer sender.Close()

	send(&sender, t)
}

func send(sender *generator.RawSender, t *testing.T) {
	srcIP := net.ParseIP("192.168.200.128")
	dstIP := net.ParseIP("192.168.200.1")

	gen := generator.NewMsgIdGenerator("raw")

	msg := gen.NextMsg()
	fmt.Printf("msg: %+v\n", msg)
	//encode
	msgByte := msg.EncodeMsg()

	iph := generator.GenerateIP(srcIP, dstIP, len(msgByte))
	udp := generator.GenerateUdp(msgByte, srcIP, dstIP, 3333, 6668)

	sender.Send(iph, udp)
	fmt.Printf("package sent!\n")
}

func TestUdpSender(t *testing.T) {
	sender := generator.NewUdpSender("192.168.200.1:3333")
	defer sender.Close()

	gen := generator.NewMsgIdGenerator("udp")
	msg := gen.NextMsg()
	fmt.Printf("msg: %+v\n", msg)
	//encode
	msgByte := msg.EncodeMsg()

	sender.Send(msgByte)
	fmt.Printf("package sent!\n")
}
