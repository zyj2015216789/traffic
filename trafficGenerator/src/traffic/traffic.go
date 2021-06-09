package traffic

import (
	"fmt"
	"go.uber.org/ratelimit"
	"golang.org/x/net/ipv4"
	"log"
	"math/rand"
	"net"
	"time"
	"trafficGenerator/src/generator"
	"trafficGenerator/src/utils"
)

var pktLoad = make([]byte, 1024, 1024)
var random = rand.New(rand.NewSource(time.Now().UnixNano()))

type Traffic struct {
	SrcIP     net.IP
	DstIP     net.IP
	SrcPort   uint16
	DstPort   uint16
	Measure   bool
	rate      int
	sender    generator.RawSender
	generator generator.MsgIdGenerator
	limiter   ratelimit.Limiter
	duration  time.Duration
	pktTotal  uint64
}

func NewTraffic(name string, srcIP, dstIP net.IP, srcPort, dstPort uint16, rate, pkcs int, duration time.Duration) Traffic {
	return Traffic{
		SrcIP:     srcIP,
		DstIP:     dstIP,
		SrcPort:   srcPort,
		DstPort:   dstPort,
		Measure:   false,
		rate:      rate,
		sender:    generator.NewRawSender("ip4:udp", srcIP.String()),
		limiter:   ratelimit.New(rate),
		generator: generator.NewMsgIdGenerator(name),
		duration:  duration,
		pktTotal:  uint64(pkcs),
	}
}

func NewTrafficNIC(name, nic, dstIP string, dstPort int, rate, pkcs int, duration time.Duration) Traffic {
	// src ip
	srcIP, err := utils.GetIPv4Addr(nic)
	if err != nil {
		log.Fatalf("can not get ip from interface %s: %+v", nic, err)
	}

	return Traffic{
		SrcIP:     srcIP,
		DstIP:     net.ParseIP(dstIP),
		SrcPort:   uint16(3333 + random.Intn(1000)),
		DstPort:   uint16(dstPort),
		Measure:   false,
		rate:      rate,
		sender:    generator.NewRawSender("ip4:udp", srcIP.String()),
		limiter:   ratelimit.New(rate),
		generator: generator.NewMsgIdGenerator(name),
		duration:  duration,
		pktTotal:  uint64(pkcs),
	}
}


func (t *Traffic) emptyUdp() []byte {
	return generator.GenerateUdp(pktLoad, t.SrcIP, t.DstIP, t.SrcPort, t.DstPort)
}



func (t *Traffic) Launch() {
	log.Printf("Node \"%s\"(%s:%d) start to send traffic to %s:%d, id: %d\n",
		t.generator.NodeName, t.SrcIP, t.SrcPort, t.DstIP, t.DstPort, t.generator.FLowId)
	defer t.sender.Close()

	start := time.Now()
	byteSent := uint64(0)

	var (
		udpHeader		[]byte
		udp				[]byte
		iph				*ipv4.Header
	)

	iph = generator.GenerateIP(t.SrcIP, t.DstIP, 0)
	udpHeader = generator.GenerateUdpFullHeader(t.SrcIP, t.DstIP, t.SrcPort, t.DstPort)

	if !t.Measure {
		udp = generator.AppendUdpData(udpHeader, pktLoad)
		iph.Len = ipv4.HeaderLen + len(pktLoad)
	}

	for true {
		t.limiter.Take()
		if t.duration > 0 && time.Since(start) > t.duration {
			log.Printf("%s traffic done, quit by duration: %d\n", t.generator.NodeName, t.duration.String())
			break
		}

		if t.Measure {
			data := t.generator.NextMsg()
			data.Rate = t.rate
			dataByte := data.EncodeMsg()
			iph.Len = ipv4.HeaderLen + len(dataByte)
			udp = generator.AppendUdpData(udpHeader, dataByte)
		}

		byteSent += uint64(t.sender.Send(iph, udp))

		if t.pktTotal > 0 && t.sender.MsgSent >= t.pktTotal {
			log.Printf("%s traffic done, quit by pkt count: %d\n", t.generator.NodeName, t.pktTotal)
			break
		}
	}
	stop := time.Now()

	du := stop.Sub(start)
	log.Printf("traffic %s(%s) (m:%t) =>%s:%d | pkts: %d(%d), time: %s(%s), \n"+
		"\t Bytes sent: %d, speed: %.2f(%d)pps, %s\n",
		t.generator.NodeName, t.SrcIP,
		t.Measure,
		t.DstIP, t.DstPort, t.sender.MsgSent, t.pktTotal,
		du.String(), t.duration,
		byteSent,
		avgSpeed(t.sender.MsgSent, du), t.rate, avgBitRate(byteSent, du))
}

func avgSpeed(pkcs uint64, duration time.Duration) float64 {
	return float64(pkcs) / duration.Seconds()
}

func avgBitRate(byteSent uint64, duration time.Duration) string {
	v := float64(byteSent) / duration.Seconds() * 8
	i := 0
	for v > 1024 && i < 3 {
		v /= 1024
		i++
	}

	unit := "Bits"
	switch i {
	case 1:
		unit = "Kb"
	case 2:
		unit = "Mb"
	case 3:
		unit = "Gb"
	}

	return fmt.Sprintf("%.3f %sps", v, unit)
}

func ParseDuration(s string) time.Duration {
	duration, err := time.ParseDuration(s)
	if err != nil {
		log.Fatal("can not parse duration: {}", err)
	}
	return duration
}
