package test

import (
	"fmt"
	"net"
	"testing"
	"trafficGenerator/src/utils"
)

func TestGetAddr(t *testing.T) {
	interfaces, err := net.Interfaces()
	if err != nil {
		t.Fatal("can not get interfaces: ", err)
	}
	for i, interf := range interfaces {
		fmt.Printf("NIC %d: Index: %d, MTU: %d, name: %s, HW: %v, flags: %v\n",
			i, interf.Index, interf.MTU, interf.Name, interf.HardwareAddr, interf.Flags)
	}

	ip, err := utils.GetIPv4Addr("ens33")
	if err != nil {
		t.Fatal("can not get ip: ", err)
	}

	fmt.Printf("get ip: %+v\n", ip)
	if ip.To4() == nil {
		t.Fatal("Didn't get ipv4 address, but: ", ip.String())
	}
}
