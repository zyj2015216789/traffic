package generator

import (
	"bytes"
	"encoding/gob"
	"log"
	"time"
)

type Msg struct {
	From     string
	FlowId   uint64
	Id       uint64    //数据流的第几个包
	SendTime time.Time //发包的时间戳
	Rate     int
	Total	 int
}

func NewMsg(from string, flowId, msgId uint64) Msg {
	return Msg{
		From:     from,
		FlowId:   flowId,
		Id:       msgId,
		SendTime: time.Now(),
	}
}

func DecodeMsg(buffer []byte) (Msg, error) {
	dec := gob.NewDecoder(bytes.NewBuffer(buffer))
	var msg Msg
	err := dec.Decode(&msg)
	if err != nil {
		log.Println("msg decode error: ", err)
	}

	return msg, err
}

func (msg *Msg) EncodeMsg() []byte {
	var msgBuffer bytes.Buffer
	enc := gob.NewEncoder(&msgBuffer)

	err := enc.Encode(msg)
	if err != nil {
		log.Fatal("msg encode error: ", err)
	}

	return msgBuffer.Bytes()
}
