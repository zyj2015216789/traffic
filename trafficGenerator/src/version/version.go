package version

import "log"

var Version = "0.1.2"

func PrintVersion() {
	log.Println("version: ", Version)
}
