package traffic

import (
	"fmt"
	"log"
	"math/rand"
	"net"
	"time"
	"trafficGenerator/src/utils"

	"go.uber.org/ratelimit"
)

var (
	zeroDuration = ParseDuration("0s")
	Random       = rand.New(rand.NewSource(time.Now().UnixNano()))
)

type BackGroundTraffic struct {
	Running  bool
	Name     string
	Rate     int
	nic      string
	HostIP   net.IP
	ipList   []net.IP
	portMin  uint16
	ports    int32
	limiter  ratelimit.Limiter
	duration time.Duration
}

func NewBackGroundTraffic(name, nic string, rate int, ipListStr []string,
	portMin uint16, ports int32, duration time.Duration) BackGroundTraffic {
	// src ip
	hostIP, err := utils.GetIPv4Addr(nic)
	if err != nil {
		log.Fatalf("can not get ip from interface %s: %+v\n", nic, err)
	}

	var ipList = make([]net.IP, 0)
	for _, str := range ipListStr {
		ip := net.ParseIP(str)
		if ip != nil && !ip.Equal(hostIP) {
			ipList = append(ipList, ip)
			log.Println("load dst ip: ", ip)
		} else {
			log.Printf("%s is not a valid remote ip\n", str)
		}
	}

	if len(ipList) == 0 {
		log.Fatalln("no valid dst ip found")
	}

	return BackGroundTraffic{
		Name:     name,
		Rate:     rate,
		nic:      nic,
		HostIP:   hostIP,
		ipList:   ipList,
		portMin:  portMin,
		ports:    ports,
		limiter:  ratelimit.New(rate),
		duration: duration,
	}
}

//func (bgf *BackGroundTraffic) setupElephant(low)

func (bgf *BackGroundTraffic) RandomTraffic() Traffic {

	flowType := Random.Intn(100)
	if flowType >= 95 {
		return bgf.elephant()
	} else {
		return bgf.mice()
	}
}

// elephant traffic 512KB/s ~ 1024KB/s
func (bgf *BackGroundTraffic) elephant() Traffic {
	ipIndex := Random.Int() % len(bgf.ipList)
	srcPort := bgf.portMin + uint16(Random.Int31()%bgf.ports)
	dstPort := bgf.portMin + uint16(Random.Int31()%bgf.ports)
	pkts := (10 + Random.Intn(10)) * 1024
	rate := 512 + Random.Intn(512)
	return NewTraffic(fmt.Sprintf("%s-elephant", bgf.Name),
		bgf.HostIP, bgf.ipList[ipIndex],
		srcPort, dstPort,
		rate, pkts, zeroDuration)
}

// mice traffic 50 KB/s ~ 100 KB/s
func (bgf *BackGroundTraffic) mice() Traffic {
	ipIndex := Random.Int() % len(bgf.ipList)
	srcPort := bgf.portMin + uint16(Random.Int31()%bgf.ports)
	dstPort := bgf.portMin + uint16(Random.Int31()%bgf.ports)
	pkts := 1 + Random.Intn(100)
	rate := 50 + Random.Intn(50)
	return NewTraffic(fmt.Sprintf("%s-mice", bgf.Name),
		bgf.HostIP, bgf.ipList[ipIndex],
		srcPort, dstPort,
		rate, pkts, zeroDuration)
}

func (bgf *BackGroundTraffic) Start() {
	bgf.Running = true

	//stop := time.Now().Add(bgf.duration)
	log.Printf("%s start to generate background traffic, rate: %d, duration: %s\n",
		bgf.Name, bgf.Rate, bgf.duration.String())

	start := time.Now()
	for bgf.Running {
		bgf.limiter.Take()

		traffic := bgf.RandomTraffic()
		hostIP, err := utils.GetIPv4Addr(bgf.nic)
		if err != nil {
			log.Fatalf("can not get ip from interface %s: %+v\n", bgf.nic, err)
		}
		traffic.SrcIP = hostIP

		go traffic.Launch()

		if bgf.duration > 0 && time.Since(start) > bgf.duration {
			log.Printf("traffic time done! %+v\n", bgf.duration)
			bgf.Running = false
		}
	}

}
