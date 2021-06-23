#!/usr/env python
import time

from configurations.controllers import *
from rpc.rpc import getRPCInstance

rpc = getRPCInstance(CONTROLLER_IP, port=CONTROLLER_RPC)

cpu_total = 0.0
ticks = 0

try:
    while True:
        cpu, mem = rpc.getUtilization()
        print("cpu: {}".format(cpu))
        cpu_total += cpu
        ticks += 1
        time.sleep(1)
except KeyboardInterrupt, e:
    print("evarage cpu: {}".format(cpu_total / float(ticks)))