package utils

import (
	"log"
	"net"
	"os"
	"fmt"
	"path/filepath"
)

type LogType int

const (
	INFO_TYPE	LogType = 0
	ERROR_TYPE	LogType = 1
)

var (
	INFO *log.Logger
	ERROR *log.Logger
)

func GetIPv4Addr(nic string) (net.IP, error) {
	interfaces, err := net.InterfaceByName(nic)
	if err != nil {
		return nil, err
	}

	addrs, err := interfaces.Addrs()
	if err != nil {
		return nil, err
	}

	var ip net.IP
	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && ipnet.IP.To4() != nil && !ipnet.IP.IsLoopback(){
			ip = ipnet.IP
			fmt.Printf(">>>>> addr: %s, is global unicast? %t\n", addr.String(), ip.IsGlobalUnicast())
		}
	}

	return ip, nil

}

func CheckFileIsExist(filename string) bool {
	var exist = true
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		exist = false
	}
	return exist
}

func MkDirs(dir string) {
	if !CheckFileIsExist(dir) {
		err := os.MkdirAll(dir, os.ModePerm)
		if err != nil {
			log.Fatalf("can not create dir \"%s\": %v\n", dir, err)
		} else {
			log.Println("create dir: ", dir)
		}
	}
}

func GetLogFile(path, filename string) *os.File {

	MkDirs(path)
	logFile, err := os.Create(filepath.Join(path, filename))
	if err != nil {
		log.Fatalf("can not open file %s: %v\n", filename, err)
	}

	return logFile
}

func GetLogger(path, filename string, prefix LogType) *log.Logger {

	logFile := GetLogFile(path, filename)

	logger := log.New(logFile, "", log.LstdFlags | log.Lshortfile)
	switch prefix {
	case INFO_TYPE:
		logger.SetPrefix("|  INFO |")
	case ERROR_TYPE:
		logger.SetPrefix("| ERROR |")
	}

	return logger
}

func InitLogger(path, filename string) {
	INFO = GetLogger(path, filename, INFO_TYPE)
	ERROR = GetLogger(path, filename, ERROR_TYPE)
}
