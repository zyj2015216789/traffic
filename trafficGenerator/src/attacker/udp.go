package attacker

import (
	"fmt"
	"go.uber.org/ratelimit"
	"log"
	"math/rand"
	"net"
	"time"
	"trafficGenerator/src/generator"
	"trafficGenerator/src/utils"
)

var (
	random = rand.New(rand.NewSource(time.Now().UnixNano()))
)

type UdpFlood struct {
	sender    		generator.RawSender
	randDstPort		bool
	randSrcIP		bool
	Rate			int
	limiter 		ratelimit.Limiter
	HostIP			net.IP
	DstIP			net.IP
	SrcPort			uint16
	DstPort 		uint16
}

func (f *UdpFlood) String() string {
	return fmt.Sprintf("UDP flood: hostIP: %s(%t) dst: %s:%d(%t), rate: %d",
		f.HostIP, f.randSrcIP, f.DstIP, f.DstPort, f.randDstPort, f.Rate)
}

func NewUdpFlood(nic string, randDstPort, randSrcIP bool, rate int, dstIP string, dstPort uint16) UdpFlood {

	hostIP, err := utils.GetIPv4Addr(nic)
	if err != nil {
		log.Fatalln("can not get nic ip: ", err)
	}

	ip := net.ParseIP(dstIP)
	if ip == nil {
		log.Fatalln("can not parse dst ip: ", err)
	}

	return UdpFlood{
		sender:      generator.NewRawSenderNIC("ip4:udp", nic),
		randDstPort: randDstPort,
		randSrcIP:   randSrcIP,
		Rate:        rate,
		limiter:     ratelimit.New(rate),
		HostIP:      hostIP,
		DstIP:       ip,
		SrcPort:     9999,
		DstPort:     dstPort,
	}
}

func (f *UdpFlood) SendPkt() {
	log.Println("start: ", f.String())

	var bytes uint64 = 0
	var pkts uint64 = 0

	quit := make(chan struct{})

	go func() {
		previousPkt := pkts
		previousBytes := bytes
		start := time.Now()
		past := time.Now()
		time.Sleep(1000 * time.Millisecond)
		for {
			select {
			case <-quit:
				log.Printf("timer quit!\n")
				break
			default:
				_pkts := pkts
				_bytes := bytes
				deltaPkts := _pkts - previousPkt
				deltaBytes := _bytes - previousBytes
				duration := time.Since(past)

				past = time.Now()

				speed := float64(deltaPkts) / duration.Seconds()
				bitRate := float64(deltaBytes) / 128.0
				log.Printf("total pkts: %8d || time: %5.1fs, pkts: %5d, speed: %7.3fpps, %6.2fKbps\n",
					_pkts, time.Since(start).Seconds(), deltaPkts, speed, bitRate)
				previousPkt = _pkts
				previousBytes = _bytes
				time.Sleep(1000 * time.Millisecond)
			}
		}
	}()

	for {
		f.limiter.Take()

		var srcIP net.IP
		if f.randSrcIP {
			srcIP = net.IPv4(10,
				byte(random.Intn(255)),
				byte(random.Intn(255)),
				byte(random.Intn(254)+1))
		} else {
			srcIP = f.HostIP
		}

		var dstPort uint16
		var srcPort uint16
		if f.randDstPort {
			dstPort = uint16(7777 + random.Intn(20000))
			srcPort = uint16(7777 + random.Intn(20000))
		} else {
			dstPort = f.DstPort
			srcPort = f.SrcPort
		}


		iph := generator.GenerateIP(srcIP, f.DstIP, 0)
		udp := generator.GenerateUdp(nil, srcIP, f.DstIP, srcPort, dstPort)

		bytes += f.sender.Send(iph, udp)
		pkts++
	}

}

