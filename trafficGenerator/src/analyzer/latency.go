package analyzer

import (
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"time"
	"trafficGenerator/src/utils"
)

var header = "id,seq,send_time,recv_time,latency(ns),latency(ms)\n"
var timeFormat = "2006-01-02 15:04:05.999999999"

func NanoToMilli(t int64) float64 {
	return float64(t) / 1e6
}

type PacketRecord struct {
	Id       uint64
	Seq		uint64
	SendTime time.Time
	RecvTime time.Time
	Latency  int64
}

func (r *PacketRecord) String() string {
	return fmt.Sprintf("%d,%d,%s,%s,%d,%f",
		r.Id,
		r.Seq,
		r.SendTime.Format(timeFormat),
		r.RecvTime.Format(timeFormat),
		r.Latency,
		NanoToMilli(r.Latency))
}

type FlowRecord struct {
	FlowId  uint64
	From    string
	To      string
	Rate    int
	Total	int
	NextSeq uint64
	Records []PacketRecord
}

func NewFlowRecord(flowId uint64, from, to string, rate, total int) FlowRecord {
	return FlowRecord{
		FlowId:  flowId,
		From:    from,
		To:      to,
		Rate:    rate,
		Total:	 total,
		NextSeq: 1,
		Records: make([]PacketRecord, 0, 25),
	}
}

func (fr *FlowRecord) String() string {
	return fmt.Sprintf("flow %d | %s => %s, rate: %d\n\tfirst: %d(%f ms), avg: %f ms, pkts: %d/%d",
		fr.FlowId, fr.From, fr.To, fr.Rate, fr.Records[0].Id,
		NanoToMilli(fr.Records[0].Latency), fr.avgLatency(), len(fr.Records), fr.Total)
}

func (fr *FlowRecord) avgLatency() float64 {
	if len(fr.Records) < 1 {
		return -1.0
	}

	var tmp int64 = 0
	for _, record := range fr.Records {
		tmp += record.Latency
	}

	return float64(tmp) / (float64(len(fr.Records)) * 1e6)
}

func (fr *FlowRecord) AppendRecord(record PacketRecord) {
	record.Seq = fr.NextSeq
	fr.NextSeq++
	fr.Records = append(fr.Records, record)
}

func (fr *FlowRecord) WriteToDisk(path string) {
	log.Println(fr)
	filename := fmt.Sprintf("%s-%s-%d-%d.csv", fr.From, fr.To, fr.FlowId, fr.Rate)
	save(fr.Records, filepath.Join(path, filename))
}

func save(records []PacketRecord, logFileName string) {
	var f *os.File
	var err error
	if utils.CheckFileIsExist(logFileName) { //如果文件存在
		//f, err = os.OpenFile(logFileName, os.O_APPEND, 0666) //打开文件
		log.Println("file exists, just ignore: ", logFileName)
		return
	} else {
		f, err = os.Create(logFileName) //创建文件
	}
	if err != nil {
		log.Printf("can not open file \"%s\": %+v\n", logFileName, err)
		return
	}
	defer f.Close()

	_, err = io.WriteString(f, header)
	if err != nil {
		log.Println("write header error: ", err)
	}

	var errors = 0
	for n, record := range records {
		//record.Latency = float64(record.RecvTime.Sub(record.SendTime).Nanoseconds()) / float64(1e6)
		_, err = io.WriteString(f, record.String()+"\n")
		if err != nil {
			log.Printf("write error! %d writed, file: %s, error: %v",
				n+1, logFileName, err)
			errors++
		}
	}

	log.Printf("record saved to path: %s, write error: %d\n", logFileName, errors)
}


