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
	log.SetFlags(log.Ltime|log.Lshortfile)

	//f, err := os.Create("cpu_profile")
	//if err != nil {
	//	log.Fatal("can not open log file")
	//}
	//
	//err = pprof.StartCPUProfile(f)
	//if err != nil {
	//	log.Fatal("can not start profile")
	//}
	//defer pprof.StopCPUProfile()

	var argName = flag.String("name", "default", "name")
	var argRate = flag.Int("r", 10, "# of flows per second")
	var portMin = flag.Int("p", 6668, "min random port")
	var portRange = flag.Int("range", 1000, "range of random port")
	var argDuration = flag.String("t", "0s", "traffic duration")
	var argNic = flag.String("i", "ens3", "network interface")
	var argLog = flag.String("log", "", "log file dir")

	flag.Parse()
	if *argLog != "" {
		log.SetOutput(utils.GetLogFile(*argLog, fmt.Sprintf("%s-back.log", *argName)))
	}

	version.PrintVersion()

	ipList := flag.Args()
	if len(ipList) == 0 {
		log.Fatalln("no ip list")
	}

	duration := traffic.ParseDuration(*argDuration)

	background := traffic.NewBackGroundTraffic(*argName, *argNic, *argRate, ipList,
		uint16(*portMin), int32(*portRange), duration)


	//go func() {
	//	time.Sleep(30 * time.Second)
	//	background.Running = false
	//}()

	background.Start()

	log.Println("traffic done!")
}
