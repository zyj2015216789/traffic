#!/usr/bin/python
import Queue
import logging
import thread
import os
import pickle
import re
import socket
import subprocess
import time
import traceback
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.util import waitListening
from mininet.node import RemoteController

from apscheduler.schedulers.background import BackgroundScheduler

from entity import Result, Latency, BandWidth
from rpc.rpc import getRPCInstance
from topo.topos import SimpleTopo, set_flowTable_limit
from traffic.background import BackGroundTraffic, do_sendByPktCnt

from configurations.controllers import *
from configurations.directories import *
from configurations import *

logging.basicConfig()

onos_usr = 'loveacat'

wait_done = False




def iperf(hosts, l4Type='TCP', udpBw='10M', fmt=None,
          seconds=5, port=5001):
    """Run iperf between two hosts.
       hosts: list of hosts; if None, uses first and last hosts
       l4Type: string, one of [ TCP, UDP ]
       udpBw: bandwidth target for UDP test
       fmt: iperf format argument if any
       seconds: iperf time to transmit
       port: iperf port
       returns: two-element array of [ server, client ] speeds
       note: send() is buffered, so client rate can be much higher than
       the actual transmission rate; on an unloaded system, server
       rate should be much closer to the actual receive rate"""
    hosts = hosts
    assert len(hosts) == 2
    client, server = hosts
    print('*** Iperf: testing', l4Type, 'bandwidth between',
           client, 'and', server, '\n')
    server.cmd('killall -9 iperf')
    iperfArgs = 'iperf -p %d ' % port
    bwArgs = ''
    if l4Type == 'UDP':
        iperfArgs += '-u '
        bwArgs = '-b ' + udpBw + ' '
    elif l4Type != 'TCP':
        raise Exception('Unexpected l4 type: %s' % l4Type)
    if fmt:
        iperfArgs += '-f %s ' % fmt
    server.sendCmd(iperfArgs + '-s')
    if l4Type == 'TCP':
        if not waitListening(client, server.IP(), port):
            raise Exception('Could not connect to iperf on port %d'
                            % port)
    cliout = client.cmd(iperfArgs + '-t %d -c ' % seconds +
                        server.IP() + ' ' + bwArgs)
    servout = ''
    # We want the last *b/sec from the iperf server output
    # for TCP, there are two of them because of waitListening
    count = 2 if l4Type == 'TCP' else 1

    while len(re.findall('/sec', servout)) < count:
        servout += server.monitor(timeoutms=5000)

    server.sendInt()
    servout += server.waitOutput()
    result = [Mininet._parseIperf(servout), Mininet._parseIperf(cliout)]
    if l4Type == 'UDP':
        result.insert(0, udpBw)
    print('*** Results: %s\n' % result)

    return result

def test_bw(net, src, dst, seconds=10):
    "python, dst string is node name"
    # bw = 0.0
    client = net.getNodeByName(src)
    server = net.getNodeByName(dst)
    # info('*** start iperf between %s(%s) => %s(%s) duration: %ds\n' % 
    #     (python, client.IP(), dst, server.IP(), seconds))
    # popen = server.popen('exec iperf3 -f m -s -p 5201', shell=True, stdout=PIPE)
    # waitListening(client, server, 5201)
    # #TODO retry
    # stdout = popen.stdout
    # #stdout.readline()
    # client_popen = client.popen('iperf3 -Z -t %d -c %s -p 5201' % (seconds, server.IP()))

    # poll_obj = select.poll()
    # poll_obj.register(popen.stdout, select.POLLIN)
    # timeout = time.time() + 20
    # while True:
    #     line = poll_obj.poll(0)
    #     if not line:
    #         time.sleep(1)
    #         timeout -= 1
    #         if time.time() > timeout:
    #             print('iperf timeout!')
    #             break

    #         print('{}...'.format(timeout - time.time()))
    #         continue
    #     line = popen.stdout.readline()
    #     print(line[:-1])
    #     if 'receiver' in line:
    #         res = re.search(r'(\d+\.*\d*)\sMbits', line)
    #         bw = float(res.group(1))
    #         break

    # popen.kill()
    result = []
    bw = 0.0
    try:
        result = net.iperf([client, server], 'TCP', fmt='M', seconds=seconds)
    except Exception, e:
        print(repr(e))
    if result and len(result) == 2:
        res = re.search(r'(\d+\.*\d*) MBytes/sec', result[1])
        if res:
            bw_str = res.group(1)
            bw = float(bw_str)
    else:
        error('can not found pattern in: {}\n'.format(result))
    info('%s(%s) => %s(%s) bandwidth: %.3fMbps duration: %ds\n' %
       (src, client.IP(), dst, server.IP(), bw, seconds))
    return BandWidth(src, dst, bw, 'MBytes/sec')


def test_ping(src, dst, net, count=4):
    "python, dst string is node name"
    client = net.getNodeByName(src)
    server = net.getNodeByName(dst)
    info('*** start ping between %s(%s) => %s(%s) count: %d\n' % 
        (src, client.IP(), dst, server.IP(), count))
    client_popen = client.popen('ping -c %d %s' % (count, server.IP()))
    stdout = client_popen.stdout


    latency = Latency(src, dst, count)
    while True:
        line = stdout.readline()
        
        print(line[:-1])
        if 'packet loss' in line:
            res = re.search(r'(\d+\.*\d*)%\spacket loss', line)
            latency.loss = float(res.group(1))
        elif 'min/avg/max/mdev' in line:
            res = re.search(r'(\d+\.*\d*)/(\d+\.*\d*)/(\d+\.*\d*)/(\d+\.*\d*)\sms', line)
            latency.min, latency.avg, latency.max, latency.dev = float(res.group(1)), float(res.group(2)), float(res.group(3)), float(res.group(4))
            break
        elif 'time=' in line:
            #print(line)
            res = re.search(r'time=(\d+\.*\d*)\sms', line)
            latency.sequence.append(float(res.group(1)))
    if latency != None and len(latency.sequence) > 0:
        latency.first = latency.sequence[0]

    #info('%s(%s) => %s(%s) latency: %s\n' % 
    #    (python, client.IP(), dst, server.IP(), latency))
    return latency

def test_latency(src, dst, net, background):
    client = net.getNodeByName(src)
    server = net.getNodeByName(dst)
    info('*** start measure traffic between %s(%s) => %s(%s)' % 
        (src, client.IP(), dst, server.IP()))

    background.send_measure(src, dst)

def test_first(src, dst, net, background):
    client = net.getNodeByName(src)
    server = net.getNodeByName(dst)
    info('*** test first pkg latency between %s(%s) => %s(%s)' %
         (src, client.IP(), dst, server.IP()))

    do_sendByPktCnt(client, server, 1, 100, MEASURE_PORT, measure=True)


def table_count(switch, table=0):
    cmd = 'ovs-ofctl dump-flows %s "table=%d" | wc -l' % (switch, table)
    out = subprocess.check_output(cmd, shell=True)
    count =  int(out) - 1
    return count

def wait_table(switch):
    while table_count(switch) > 4:
        time.sleep(1)


def test_attack(src, dst, net, rate=500):
    attacker = net.getNodeByName(src)
    target = net.getNodeByName(dst)

    cmd = 'exec sendpkt -r -v %d %s' % (rate, target.IP())
    print('start attack: {}'.format(cmd))

    popen = attacker.popen(cmd, shell=True)

    return popen

def test_attack_udp(net, src, dst, rate=500, randDstPort=False, randSrcIP=False, log=None):
    attacker = net.getNodeByName(src)
    target = net.getNodeByName(dst)

    args = ''
    log_dir = LOG_DIR
    if randDstPort:
        args += '-P'
    if randSrcIP:
        if len(args) > 0:
            args += ' '
        args += '-I'
    # if log:
    #     log_dir = log

    nic = '%s-eth0' % src
    cmd = 'attackUdp {args} -i {nic} -r {rate} -log {logDir} {ip}'.format(
        args=args, nic=nic, rate=rate, logDir=log_dir, ip=target.IP())
    print('start UDP flooding: {} {}'.format(src, cmd))

    popen = attacker.popen(cmd, shell=True)

    return popen

def run_cmd(node, net, cmd):
    host = net.getNodeByName(node)

    cmd = 'exec {}'.format(cmd)
    print('{} excute {}'.format(node, cmd))

    popen = host.popen(cmd, shell=True)

    return popen


def clean_table(cmd='all'):
    if cmd == None:
        return

    print("clean flow table..." + cmd)
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_CLEAN))
    s.send('%s\n' % (cmd))
    print('{} | {}'.format(time.asctime(), s.recv(1024)))
    s.close()
    wait(3)


def wait(seconds=3):
    info('wait %ds ...\n' % (seconds))
    time.sleep(seconds)

def defend_point_host(net, host, opt='defend'):
    ip = net.getNodeByName(host).IP()
    defend_point(ip, opt)

def defend_point(ip, opt='defend'):
    msg = "%s %s\n" % (opt, ip)
    print("%s point: %s" % (opt, ip))
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_DEFEND))
    s.send(msg)
    s.close()

def add_host_host(net, host, opt='add'):
    ip = net.getNodeByName(host).IP()
    add_host_ip(ip, opt)

def add_host_ip(ip, opt='add'):
    msg = "%s %s\n" % (opt, ip)
    print("%s point: %s" % (opt, ip))
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_DEFEND))
    s.send(msg)
    s.close()

def show_path(net, host1, host2):
    ip1 = net.getNodeByName(host1).IP()
    ip2 = net.getNodeByName(host2).IP()
    msg = '%s %s %s\n' % ('show', ip1, ip2)
    print('show path: %s' % msg)
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_DEFEND))
    s.send(msg)
    reply = s.recv(1024)
    print('path between {} <-> {}: \n{}'.format(host1, host2, reply))
    s.close()

    pattern = re.compile(r'of:[a-f0-9]+')
    res = re.findall(pattern, reply)
    print(res)
    switches = set()
    if res and len(res) > 0:
        for switch in res:
            switches.add('s%d' % (int(switch[3:], 16)))
        print('switches in the paths: {}'.format(' '.join(switches)))
    else:
        print('can not found any switch in the relpy')
    return list(switches)

def show_accu():
    msg = 'status 10.0.0.1\n'
    s = socket.socket()
    print(msg)
    s.connect((CONTROLLER_IP, CONTROLLER_DEFEND))
    s.send(msg)
    reply = s.recv(1024)
    print('detect status: {}'.format(reply))
    s.close()

def add_host_all(net, opt='add'):
    for host in net.hosts:
        add_host_ip(host.IP(), opt)

def observe_point(ip, opt='add'):
    msg = '%s %s\n' % (opt, ip)
    print('observe point: ', msg)
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_OBSERVE))
    s.send(msg)
    wait(1)
    s.close()


def shield_host_all(net, opt='register'):
    for host in net.hosts:
        shield_register(host.IP(), opt)


def shield_register_host(net, host, opt='register'):
    ip = net.getNodeByName(host).IP()
    shield_register(ip, opt)

def shield_register(ip, opt='register'):
    msg = '%s %s\n' % (opt, ip)
    print('shield register: ', msg)
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_SHIELD))
    s.send(msg)
    s.close()


def shield_point(ip, opt='add'):
    msg = '%s %s\n' % (opt, ip)
    print('shield point: ', msg)
    s = socket.socket()
    s.connect((CONTROLLER_IP, CONTROLLER_SHIELD))
    s.send(msg)
    s.close()
    
def shield_all(net, opt='add'):
    for host in net.hosts:
        shield_point(host.IP(), opt)


def make_permanent(path, result):
    if not os.path.exists(path):
        os.makedirs(path)

    file = os.path.join(path, '{}.pkl'.format(result.name))
    with open(file, 'wb') as f:
        pickle.dump(result, f)

    print('{} | result {} saved into {}'.format(time.asctime(), result.name, file))

def attack_group(attacks, net):
    group = []
    for attack in attacks:
        group.append(test_attack(attack[0], attack[1], net, rate=attack[2]))

    return group

def add_defend(attacks, net, opt='add'):
    for attack in attacks:
        ip = net.getNodeByName(attack[0]).IP()
        defend_point(ip, opt)


def defend_all(net, opt='defend'):
    for host in net.hosts:
        defend_point(host.IP(), opt)


def get_log_path():
    name = raw_input("experiment name: ")
    if len(name) < 1:
        info('no name input, use default\n')
        name = 'default'
    path = '{}/{}-{}'.format(
        RESULT_DIR, time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime()), name)
    print("set log path: {}".format(path))

    return path

def print_results(results):
    print('*' * 100)
    print('RESULTS')
    print('*' * 100)
    for result in results:
        print('*' * 100)
        print(result)

    print('*' * 100)
    print('result path: ' + RESULT_DIR)


def experiment():

    rpc = getRPCInstance(ip=CONTROLLER_IP, port=CONTROLLER_RPC)
    results = []
    path = get_log_path()

    #topo = FloodShield(bw=100)
    topo = SimpleTopo(bw=100)

    #net = build_mine(topo, total_cpu=.5)
    net = Mininet(topo=topo, controller=None)
    net.addController('c0', controller=RemoteController, 
        ip=CONTROLLER_IP, port=CONTROLLER_PORT)

    net.start()

    bg = BackGroundTraffic(net, 10, path)


    rpc.switch_naive()

    #CLI(net)
    wait(1)
    net.pingAll()
    wait(1)
    clean_table()

    set_flowTable_limit(topo, 2000, policy='evict')

    '''
        fwd normal
    '''
    
    # rpc.switch_naive()
    # res = start_single(net, topo, name='fwd-normal', clean='org.onosproject.fwd')
    # results.append(res)
    # make_permanent(path, res)
    
    '''
        defend normal
    '''
    rpc.switch_defend()
    '''
    wait(6)
    res = start_single(net, topo, name='defend-normal', clean='xyz.loveacat.fwd')
    results.append(res)
    make_permanent(path, res)
    '''

    '''
        attack env
        fwd attack
    '''
    
    for r in range(2):
        rate = 500 * r
        attacks = [('h2', 'h4', rate)]
        '''
            defend attack
        '''
        rpc.switch_defend()
        #defend_point('10.0.0.1', opt='add')
        #add_defend(attacks, net, opt='add')
        defend_all(net)
        res = start_single(net, topo, bg, attacks=attacks, name='defend-%d'%(rate), clean='xyz.loveacat.fwd')
        results.append(res)
        make_permanent(path, res)
        add_defend(attacks, net, opt='remove')

        #defend_point('10.0.0.5', opt='add')

        rpc.switch_naive()
        res = start_single(net, topo, bg, attacks=attacks, name='fwd-%d'%(rate), clean='org.onosproject.fwd')
        results.append(res)
        make_permanent(path, res)
        

    CLI(net)

def get_table_count_all(topo):
    table = {}
    for s in topo.switches():
        table[s] = table_count(s)
    return table

def get_table_count(switches, table=0):
    table_counts = {}
    for s in switches:
        table_counts[s] = table_count(s, table)
    return table_counts


def start_util(result, topo, switches=None, table_id=0):
    scheduler = BackgroundScheduler()
    rpc = getRPCInstance(CONTROLLER_IP, port=CONTROLLER_RPC)
    #rpc.check_onos()
    #q = Queue.Queue()
    def timedTask():
        tag = None
        cpu, mem = rpc.getUtilization()
        table = None
        if switches and len(switches) > 0:
            table = get_table_count(switches, table_id)
        # if not switches:
        #     table = get_table_count_all(topo)
        # try:
        #     tag = q.get(False)
        # except Queue.Empty, e:
        #     pass
        # except Exception, e:
        #     print(traceback.format_exc())
        #     print(repr(e))

        result.add_util(cpu, mem, table, tag)

    scheduler.add_job(timedTask, 'interval', seconds=3)
    scheduler.start()

    return scheduler, None


def start_single(net, topo, bg, attacks=None, name='exp', clean='all'):

    result = Result(name)
    # background status
    sched, q = start_util(result, topo)
    wait(3)

    try:
        # if bg:
        #     bg.start()

        #net.pingAll()
        #wait(1)
        #clean_table()

        attack_proc = None
        if attacks:
            attack_proc = attack_group(attacks, net)
            q.put('attack')
            wait(15)

        ## test start ##
        # rtt
        q.put('latency start')
        for i in range(10):
            print('****************** ### {} round {}'.format(name, i))
            #latency = test_ping('h5', 'h3', net, count=5)
            #result.add_latency(latency)
            #latency = test_ping('h1', 'h3', net, count=4)
            bg.send_measure('h1', 'h3')
            #result.add_latency(latency)
            #result.add_latency(test_ping('h1', 'h5', net, count=3))
            #result.add_latency(test_ping('h1', 'h7', net, count=3))
            clean_table(cmd=clean)
            # wait(15)
        q.put('latency end')
        wait(5)

        # bandwidth
        
        q.put('bandwidth start')
        for i in range(3):
            bw = test_bw('h1', 'h3', net)
            print('>>>>>>>>>>>>>>>>> {} round {} {}'.format(name, i, bw))
            result.add_bandwidth(bw)
            clean_table(cmd=clean)
        q.put('bandwidth end')
        
        if attack_proc:
            print('kill attackers...')
            for proc in attack_proc:
                proc.kill()

    except Exception, e:
        print(traceback.format_exc())
        print(repr(e))
        result = None
        
    if sched:
        sched.shutdown()

    return result


def main():
    setLogLevel('info')
    cleanup()
    experiment()
    cleanup()

if __name__ == '__main__':
    print("start experiment demo")
    main()
