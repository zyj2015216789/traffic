package test

import (
	"fmt"
	"testing"
	"trafficGenerator/src/generator"
)

func TestReceiver(t *testing.T) {
	//sender := generator.NewRawSender("ip4:udp", "0.0.0.0")
	sender := generator.NewUdpSender("127.0.0.1:3333")
	defer sender.Close()

	receiver := generator.NewReceiver("0.0.0.0", 3333)
	defer receiver.Close()

	//srcIP := net.ParseIP("192.168.200.128")
	//dstIP := net.ParseIP("192.168.200.1")

	gen := generator.NewMsgIdGenerator("recv test")

	msg := gen.NextMsg()
	fmt.Printf("msg: %+v\n", msg)

	latch := make(chan struct{})

	go func() {
		msg2, err := receiver.ReceiveMsg()
		if err != nil {
			t.Fatal("receive msg error")
		}
		fmt.Printf("receive msg: %+v\n", msg2)
		if msg.Id != msg2.Id {
			t.Fatal("id wrong: {} != {}", msg.Id, msg2.Id)
		}

		if msg.SendTime != msg.SendTime {
			t.Fatal("send time wrong: {} != {}", msg.SendTime, msg2.SendTime)
		}

		latch <- struct{}{}
	}()

	//encode
	msgByte := msg.EncodeMsg()
	//msgByte := []byte{0, 0, 0, 1, 1, 1, 1, 1}
	//
	//iph := generator.GenerateIP(srcIP, dstIP, len(msgByte))
	//udp := generator.GenerateUdp(msgByte, srcIP, dstIP, 4444, 3333)

	sender.Send(msgByte)
	fmt.Printf("package sent!\n")

	<-latch
}
