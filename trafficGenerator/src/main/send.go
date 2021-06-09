package main

import (
	"flag"
	"fmt"
	"log"
	"trafficGenerator/src/traffic"
	"trafficGenerator/src/utils"
	"trafficGenerator/src/version"
)


func main() {
	var argName = flag.String("name", "default", "node name")
	var argRate = flag.Int("r", 100, "pkts per second")
	var argPkts = flag.Int("k", 0, "# of pkts to send")
	var argTime = flag.String("t", "0s", "duration")
	var argMeasure = flag.Bool("m", false, "measurement traffic")
	var argDstPort = flag.Int("p", 6667, "remote port")
	var argNic = flag.String("i", "lo", "network interface")
	var argLog = flag.String("log", "", "log file dir")

	flag.Parse()
	if *argLog != "" {
		log.SetOutput(utils.GetLogFile(*argLog, fmt.Sprintf("%s-sender.log", *argName)))
	}

	version.PrintVersion()

	var addr = flag.Arg(0)
	if addr == "" {
		log.Fatal("Please specify an IP address, ", addr)
	}

	duration := traffic.ParseDuration(*argTime)

	tfc := traffic.NewTrafficNIC(*argName, *argNic, addr, *argDstPort, *argRate, *argPkts, duration)
	tfc.Measure = *argMeasure

	tfc.Launch()
}
