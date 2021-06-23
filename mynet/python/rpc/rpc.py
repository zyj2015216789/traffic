#!/usr/bin/python

from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy
from apscheduler.schedulers.background import BackgroundScheduler

from configurations.controllers import *

from utilization import getOnosProcess, getCpu, getMemory, getKarafPid
from utils.ssh import exec_cmd

import time

scheduler = BackgroundScheduler()
onos = None
#default_addr = ('127.0.0.1', 2334)

local_usr='loveacat'

def check_onos():
    global onos
    if not onos or not onos.is_running():
        print('onos is down, get pid again! {}'.format(onos))
        onos = getOnosProcess()

def getUtilization():
    check_onos()
    res = (getCpu(onos), getMemory(onos))
    print('{} cpu utilization: {}'.format(time.asctime(), res))
    return res

def refreshProcess():
    check_onos()
    print('refresh onos process, pid: {}'.format(onos.pid))

def switch_naive():
    ret = True
    cmd = 'onos localhost app deactivate xyz.loveacat.detect xyz.loveacat.defendfwd'
    ret = ret and exec_cmd(local_usr, cmd)
    cmd = 'onos localhost app activate org.onosproject.fwd'
    ret = ret and exec_cmd(local_usr, cmd)

    return ret

def switch_defend():
    ret = True
    cmd = 'onos localhost app deactivate org.onosproject.fwd'
    #subprocess.check_call(cmd)
    ret = ret and exec_cmd(local_usr, cmd)
    cmd = 'onos localhost app activate xyz.loveacat.defendfwd xyz.loveacat.detect'
    #subprocess.check_call(cmd)
    ret = ret and exec_cmd(local_usr, cmd)

    return ret

def kill_onos():
    onos.kill()


def getRPCInstance(ip=None, port=0):
    print('get RPC from: %s:%d' % (ip, port))
    if ip == None or port == 0:
        return ServerProxy("http://{}:{}".format(CONTROLLER_IP, CONTROLLER_RPC))
    return ServerProxy("http://{}:{}".format(ip, port))

def startRPCServer(ip=None, port=0):
    server = None
    if ip == None or port == 0:
        server = SimpleXMLRPCServer((CONTROLLER_IP, CONTROLLER_RPC))
    else:
        server = SimpleXMLRPCServer((ip, port))

    scheduler.add_job(refreshProcess, 'interval', seconds=10)
    #scheduler.start()

    print('start rpc server: {}'.format(server))
    server.register_function(getUtilization)
    server.register_function(refreshProcess)
    server.register_function(switch_defend)
    server.register_function(switch_naive)
    #server.register_function(check_onos)
    server.serve_forever()



if __name__ == '__main__':
    onos = getOnosProcess()
    print('onos pid: {}'.format(getKarafPid()))
    startRPCServer(ip='0.0.0.0', port=2334)
