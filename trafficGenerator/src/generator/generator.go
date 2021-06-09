package generator

import (
	"golang.org/x/net/ipv4"
	"math/rand"
	"net"
	"time"

	//"unsafe"
)

var Random = rand.New(rand.NewSource(time.Now().UnixNano()))


type Generator interface {
}

type MsgIdGenerator struct {
	NodeName string
	FLowId   uint64
	nextId   uint64
}

func NewMsgIdGenerator(name string) MsgIdGenerator {
	return MsgIdGenerator{
		NodeName: name,
		FLowId:   Random.Uint64(),
		nextId:   1,
	}
}

func (gen *MsgIdGenerator) NextMsg() Msg {
	msg := NewMsg(
		gen.NodeName,
		gen.FLowId,
		gen.nextId,
	)
	gen.nextId++
	return msg
}

func GenerateUdpFullHeader(srcIP, dstIP net.IP, srcPort, dstPort uint16) []byte {
	length := 8
	udpHeader := make([]byte, 20)
	/*
		UDP 伪首部
	*/
	udpHeader[0], udpHeader[1], udpHeader[2], udpHeader[3] = srcIP[12], srcIP[13], srcIP[14], srcIP[15]
	udpHeader[4], udpHeader[5], udpHeader[6], udpHeader[7] = dstIP[12], dstIP[13], dstIP[14], srcIP[15]

	udpHeader[8], udpHeader[9] = 0x00, 0x11

	udpHeader[10], udpHeader[11] = byte((length>>8)&0xff), byte(length&0xff)
	/*
		UDP 头部
	*/
	// 源端口
	udpHeader[12], udpHeader[13] = byte((srcPort>>8)&0xff), byte(srcPort&0xff)
	// 目的端口
	udpHeader[14], udpHeader[15] = byte((dstPort>>8)&0xff), byte(dstPort&0xff)
	// UDP 头长度
	udpHeader[16], udpHeader[17] = byte((length>>8)&0xff), byte(length&0xff)
	// 效验和
	udpHeader[18], udpHeader[19] = 0x00, 0x00

	return udpHeader
}

func AppendUdpData(udpHeader, data []byte) []byte {
	length := 8 + len(data)

	udpHeader[10], udpHeader[11] = byte((length>>8)&0xff), byte(length&0xff)
	udpHeader[16], udpHeader[17] = byte((length>>8)&0xff), byte(length&0xff)

	pktData := append(udpHeader, data...)
	return pktData[12:]
}

func GenerateUdp(msgByte []byte, srcIP, dstIP net.IP, srcPort, dstPort uint16) []byte {

	length := len(msgByte) + 8
	udpHeader := make([]byte, 20, 20 + len(msgByte))
	/*
		UDP 伪首部
	*/
	udpHeader[0], udpHeader[1], udpHeader[2], udpHeader[3] = srcIP[12], srcIP[13], srcIP[14], srcIP[15]
	udpHeader[4], udpHeader[5], udpHeader[6], udpHeader[7] = dstIP[12], dstIP[13], dstIP[14], srcIP[15]

	udpHeader[8], udpHeader[9] = 0x00, 0x11

	udpHeader[10], udpHeader[11] = byte((length>>8)&0xff), byte(length&0xff)
	/*
		UDP 头部
	*/
	// 源端口
	udpHeader[12], udpHeader[13] = byte((srcPort>>8)&0xff), byte(srcPort&0xff)
	// 目的端口
	udpHeader[14], udpHeader[15] = byte((dstPort>>8)&0xff), byte(dstPort&0xff)
	// UDP 头长度
	udpHeader[16], udpHeader[17] = byte((length>>8)&0xff), byte(length&0xff)
	// 效验和
	udpHeader[18], udpHeader[19] = 0x00, 0x00

	pktData := append(udpHeader, msgByte...)
	//check := checkSum(pktData)
	//pktData[18], pktData[19] = byte(check>>8&0xff), byte(check&0xff)
	//fmt.Printf("checkout sum: %x %x\n", pktData[18], pktData[19])

	return pktData[12:]
}


func GenerateIP(srcIP, dstIP net.IP, msgLen int) *ipv4.Header {
	/*
		IP 头部
	*/
	ipHeader := &ipv4.Header{
		Version:  ipv4.Version,
		Len:      ipv4.HeaderLen,
		TotalLen: ipv4.HeaderLen + msgLen,
		Flags:    ipv4.DontFragment,
		TTL:      64,
		Protocol: 17,
		Checksum: 0,
		Src:      srcIP,
		Dst:      dstIP,
	}

	//header, err := ipHeader.Marshal()
	//if err != nil {
	//	log.Fatal("ip header marshal error: {}", err)
	//}
	//
	//ipHeader.Checksum = int(checkSum(header))

	return ipHeader
}



/**
 */
func checkSum(data []byte) uint16 {
	var (
		sum    uint32
		length int = len(data)
		index  int
	)
	for length > 1 {
		sum += uint32(data[index])<<8 + uint32(data[index+1])
		index += 2
		length -= 2
	}
	if length > 0 {
		sum += uint32(data[index])
	}
	sum += (sum >> 16)

	//
	return uint16(^sum) + 0x7f
}
