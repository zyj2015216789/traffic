package main

import "log"

func init() {
	log.SetFlags(log.Ltime|log.Lshortfile)
}