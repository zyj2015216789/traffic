package main

import (
	"fmt"
	"os"
	"os/exec"
	"sync"
)

func main() {
	ipList := []string{"10.0.0.2", "10.0.0.3"}

	var wg sync.WaitGroup
	for _, ip := range ipList {
		wg.Add(1)
		go func(ip string) {
			defer wg.Done()
			var res []byte
			var err error
			cmdStr := fmt.Sprintf("echo %s", ip)
			cmd := exec.Command("sh", "-c", cmdStr)
			if res, err = cmd.Output(); err != nil {
				fmt.Print(err)
				os.Exit(1)
			}
			fmt.Println(string(res))
		}(ip)
	}
	wg.Wait()
	fmt.Print("done\n")
}
