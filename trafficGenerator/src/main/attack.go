package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"syscall"
	"trafficGenerator/src/attacker"
	"trafficGenerator/src/version"
)

func main() {
	var argRate = flag.Int("r", 100, "pkts per second")
	var argPkts = flag.Int("k", 0, "total pkts to send")
	var argRand = flag.Bool("rand", false, "enable random src ip")

	flag.Parse()

	version.PrintVersion()


	fd, err := syscall.Socket(syscall.AF_INET, syscall.SOCK_RAW, syscall.IPPROTO_RAW)
	if err != nil {
		log.Fatalf("sendPkt: %v\n", err)
	}
	defer syscall.Shutdown(fd, syscall.SHUT_RDWR)

	dst := os.Args[len(os.Args)-1]
	fmt.Printf("send packet to %s, rate: %d, random src ip: %v\n", dst, *argRate, *argRand)
	attacker.SendPkt(fd, dst, *argRate, *argPkts, *argRand)
	fmt.Printf("done!")
}
