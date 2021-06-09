package test

import (
	"os"
	"runtime/pprof"
	"testing"
	"time"
	"trafficGenerator/src/traffic"
)

func TestTrafficUni(t *testing.T) {
	//duration := traffic.ParseDuration("8s")
	f, err := os.Create("cpu_profile")
	if err != nil {
		t.Fatal("can not open log file")
	}

	err = pprof.StartCPUProfile(f)
	if err != nil {
		t.Fatal("can not start profile")
	}
	defer pprof.StopCPUProfile()

	pkcs := int(1e6)
	rate := int(5e4)

	tfc := traffic.NewTrafficNIC("traffic", "ens33", "192.168.200.1", 5555, rate, pkcs, time.Duration(0))
	tfc.Measure = false

	tfc.Launch()
}
