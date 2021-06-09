package test

import (
	"fmt"
	"testing"
	"trafficGenerator/src/generator"
)

func TestGenerator(t *testing.T) {
	gen := generator.NewMsgIdGenerator("test gen")

	msg := gen.NextMsg()
	fmt.Printf("msg: %+v\n", msg)
	//encode
	msgByte := msg.EncodeMsg()
	//decode
	msg2, err := generator.DecodeMsg(msgByte)
	if err != nil {
		t.Fatal("decode msg error")
	}
	fmt.Printf("decoded: %+v\n", msg2)

	if msg.Id != msg2.Id {
		t.Fatal("id wrong: {} != {}", msg.Id, msg2.Id)
	}

	if msg.SendTime != msg.SendTime {
		t.Fatal("send time wrong: {} != {}", msg.SendTime, msg2.SendTime)
	}
}
