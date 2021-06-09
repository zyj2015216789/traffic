package main

import (
	"flag"
	"fmt"
	"log"
	"time"
	"trafficGenerator/src/analyzer"
	"trafficGenerator/src/generator"
	"trafficGenerator/src/utils"
	"trafficGenerator/src/version"
)

const (
	interval = 5 * time.Second
)
func main() {
	var argName = flag.String("name", "default", "host name")
	var argPort = flag.Int("p", 6667, "listen Port")
	var argPkts = flag.Int("k", 20, "pkt argName recv")
	var argResultDir = flag.String("d", "./", "result dir")
	var argTimeout = flag.String("t", "30s", "flow timeout")
	var argLog = flag.String("log", "", "log dir")


	flag.Parse()
	if *argLog != "" {
		log.SetOutput(utils.GetLogFile(*argLog, fmt.Sprintf("%s-recv.log", *argName)))
	}

	version.PrintVersion()

	timeout, err := time.ParseDuration(*argTimeout)
	if err != nil {
		log.Fatal("can not parse timeout value: ", *argTimeout)
	}

	utils.MkDirs(*argResultDir)

	recv := generator.NewReceiver("0.0.0.0", *argPort)
	defer recv.Close()

	log.Printf("Node %s listening at argPort: %d, timeout: %s\n",
		*argName, *argPort, *argTimeout)

	//var flows = make(map[uint64]*analyzer.FlowRecord)
	var flows = analyzer.NewLRUMap(timeout)

	stop := make(chan struct{})
	go timer(flows, *argResultDir, stop)

	for {
		msg, err := recv.ReceiveMsg()
		if err != nil {
			continue
		}

		flowRecord, ok := flows.Get(msg.FlowId)
		if !ok {
			newFlow := analyzer.NewFlowRecord(msg.FlowId, msg.From, *argName, msg.Rate, 0)
			flowRecord = &newFlow
			flows.Put(msg.FlowId, flowRecord)
		}

		if len(flowRecord.Records) >= *argPkts {
			continue
		}

		now := time.Now()
		record := analyzer.PacketRecord{
			Id:       msg.Id,
			SendTime: msg.SendTime,
			RecvTime: now,
			Latency:  now.Sub(msg.SendTime).Nanoseconds(),
		}

		flowRecord.AppendRecord(record)
		if len(flowRecord.Records) >= *argPkts {
			flows.Remove(msg.FlowId)
			go flowRecord.WriteToDisk(*argResultDir)
		}
	}

	//stop <- struct{}{}
}

func timer(lru *analyzer.LRUMap, path string, stop chan struct{}) {
	log.Printf("timer start, interval: %v\n", interval)
	for {
		select {
		case <- stop:
			return
		default:
			flows := lru.RemoveByTime()
			if len(flows) != 0 {
				log.Println("# of nodes timeout: ", len(flows))
				for _, flow := range flows {
					go flow.WriteToDisk(path)
				}
			}

			time.Sleep(interval)
		}
	}
}