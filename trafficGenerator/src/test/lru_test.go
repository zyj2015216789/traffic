package test

import (
	"fmt"
	"log"
	"testing"
	"time"
	"trafficGenerator/src/analyzer"
)

func TestLru(t *testing.T) {
	timeout, err := time.ParseDuration("3s")
	if err != nil {
		t.Fatal("can not parse timeout")
	}
	lruMap := analyzer.NewLRUMap(timeout)

	nodes := 3

	for i := 0; i < nodes; i++ {
		flow := analyzer.NewFlowRecord(uint64(i), "h1", "h2", 200)
		lruMap.Put(flow.FlowId, &flow)
	}

	if lruMap.Size() != nodes {
		t.Fatal("map size is not ", nodes)
	}

	for i := nodes - 1; i >= 0; i-- {
		_, ok := lruMap.Get(uint64(i))
		fmt.Println("get ", i, ": ", lruMap.TimeList())
		if !ok {
			t.Fatal("can not get record", i)
		}
		//fmt.Printf("flowId: %d, from: %s, to: %s, rate: %d\n",
		//	f2.FlowId, f2.From, f2.To, f2.Rate)
	}
	fmt.Println(lruMap.TimeList())

	t.Log("wait for timeout...")
	time.Sleep(timeout * 2)

	size := lruMap.Size()
	flows := lruMap.RemoveByTime()
	if len(flows) != size {
		t.Fatalf("there is still some record not evict, num: %d, size: %d\n", len(flows), size)
	}
}

func TestLruRemove(t *testing.T) {
	timeout, err := time.ParseDuration("3s")
	if err != nil {
		t.Fatal("can not parse timeout")
	}
	lruMap := analyzer.NewLRUMap(timeout)
	nodes := 10

	for i := 0; i < nodes; i++ {
		flow := analyzer.NewFlowRecord(uint64(i), "h1", "h2", 200)
		lruMap.Put(flow.FlowId, &flow)
	}

	if lruMap.Size() != nodes {
		t.Fatal("map size is not 100")
	}
	fmt.Println(lruMap.TimeList())

	for i := nodes - 1; i >= 0; i-- {
		flow := lruMap.Remove(uint64(i))
		if flow == nil {
			log.Fatal("can not found key: ", i)
		}
		fmt.Printf("remove flow: %d\n", flow.FlowId)
	}

	if lruMap.Size() != 0 {
		log.Fatal("map size is not 0")
	}
}