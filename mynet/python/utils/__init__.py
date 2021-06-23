import shlex
import sys, os, random
from subprocess import check_output, STDOUT, CalledProcessError
from time import sleep
from functools import partial

from mininet.util import quietRun, run
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet

Python3 = sys.version_info[0] == 3
BaseString = str if Python3 else getattr( str, '__base__' )

def waitUdpListening(server, port=80, timeout=None):
    #runCmd = partial( quietRun, shell=True )
    cmd = 'lsof -i:{}'.format(port)
    condition = ':{}'.format(port)

    time = 0

    result = runCmd(server, cmd)
    while condition not in result:
        if timeout and time >= timeout:
            error('port {} is not open\n'.format(port))
            return False

        info('.')
        sleep(.5)
        time += .5
        result = runCmd(server, cmd)

    info('port {} is opening\n'.format(port))
    return True

def runCmd(host, cmd):
    runner = (host.cmd if host else
              partial(quietRun, shell=True))
    result = ''
    try:
        result = runner(cmd)
    except CalledProcessError, e:
        error(e)
        error(e.output)

    return result


def captureOutput(net, hosts):
    for host, msg in net.monitor(hosts):
        info("capture %s: %s\n" % (host, msg))

def kill_all_receiver():
    os.system("killall recv")
    os.system("killall tcpreplay")
    print("receiver killed!")

def kill_all_traffic():
    os.system('killall traffic')
    print('traffic killed!')

def getRandomMac():
    Maclist = []
    for i in range(1, 7):
        RANDSTR = "".join(random.sample("0123456789abcdef", 2))
        Maclist.append(RANDSTR)

    RANDMAC = ":".join(Maclist)
    return RANDMAC

def setRandomMac(host):
    host.setMAC(Mininet.randMac())

def requestIP(host):
    intf = host.defaultIntf()
    cmd = 'dhclient {}'.format(intf.name)
    info('{} request new ip: {}\n'.format(host.name, cmd))
    runCmd(host, cmd)
    info('{} new addr: {}\n'.format(host.name, intf.updateAddr()))

def id2name(id):
    return 'h{}'.format(id)
