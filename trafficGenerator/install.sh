#!/usr/bin/env bash

dir=$(pwd)
export GOOS=linux
export GOBIN="$dir/bin"
#export GOPATH="$GOPATH:$dir"
#export GOPATH="/home/onos/netScript"
echo"GOBIN: $GOBIN"

echo "GOPATH: $GOPATH"

go install src/main/attack.go
go install src/main/recv.go
go install src/main/send.go
go install src/main/traffic.go
go install src/main/attackUdp.go
