#!/usr/bin/python

import psutil
import time

onos_pid_file = '/tmp/onos.pid'

def getProcess(pName):
    process_lst = list()
    all_pids = psutil.pids()

    for pid in all_pids:
        p = psutil.Process(pid)
        #print(p.name())
        if p.name() == pName:
            process_lst.append(p)

    return process_lst

def getKarafPid():
    with open(onos_pid_file, 'r') as f:
        pid = int(f.readline())
        print('karaf pid: {}'.format(pid))
        return pid
    #return int(raw_input('onos pid: '))

def getOnosProcess():
    onos = None
    for proc in psutil.Process(getKarafPid()).children():
        if 'org.apache.karaf.main.Main' in proc.cmdline():
            onos = proc
            break
    return onos

def getCpu(process):
    return process.cpu_percent(None)

def getMemory(process):
    return process.memory_percent()

def main():
    onos = getOnosProcess()

    print('onos process: {}'.format(onos))
    while True:
        cpu = onos.cpu_percent(None)
        mem = onos.memory_percent()
        print('{} cpu: {}% memory: {:>.4f}%'.format(time.asctime(), cpu, mem))
        time.sleep(1)

if __name__ == '__main__':
    main()
