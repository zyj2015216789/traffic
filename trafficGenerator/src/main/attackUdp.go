package main

import (
	"flag"
	"log"
	"trafficGenerator/src/attacker"
	"trafficGenerator/src/utils"
)

func main() {
	log.SetFlags(log.Ltime|log.Lshortfile)

	var argNIC = flag.String("i", "lo", "network interface")
	var argRate = flag.Int("r", 100, "# of pkts per second")
	var argDstPort = flag.Int("p", 8888, "udp dst port")
	var argRandPort = flag.Bool("P", false, "enable random dst port")
	var argRandIP = flag.Bool("I", false, "enable random src ip")
	var argLog = flag.String("log", "", "log dir")

	flag.Parse()
	if *argLog != "" {
		log.SetOutput(utils.GetLogFile(*argLog, "attacker.log"))
	}

	dstIP := flag.Arg(0)
	if dstIP == "" {
		log.Fatalln("please specify a dst ip!")
	}

	flooder := attacker.NewUdpFlood(*argNIC, *argRandPort, *argRandIP, *argRate, dstIP, uint16(*argDstPort))

	flooder.SendPkt()
}
