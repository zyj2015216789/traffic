import math
import os
import random
import re
import threading
import time

from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug, output
from mininet.node import RemoteController
from mininet.util import waitListening

from configurations.controllers import *
from configurations.directories import *
from configurations import *
from topo.topos import SimpleTopo, build_mine, set_flowTable_limit
from utils.ratelimit import TokenBucket
from utils.output_monitor import OutputMonitor
from utils import waitUdpListening

def wait(seconds=3):
    info('wait %ds ...\n' % (seconds))
    time.sleep(seconds)


def transport_time(size, rate):
    return math.ceil(float(size) / float(rate * 128))


def iperf3(net, hosts=None, l4Type='TCP', udpBw='10M', fmt=None, seconds=5, port=5001):
    hosts = hosts or [ net.hosts[ 0 ], net.hosts[ -1 ] ]
    assert len( hosts ) == 2
    client, server = hosts
    output( '*** Iperf: testing', l4Type, 'bandwidth between',
            client, 'and', server, '\n' )
    server.cmd( 'killall -9 iperf' )
    iperfArgs = 'iperf3 -p %d ' % port
    bwArgs = ''
    if l4Type == 'UDP':
        iperfArgs += '-u '
        bwArgs = '-b ' + udpBw + ' '
    elif l4Type != 'TCP':
        raise Exception( 'Unexpected l4 type: %s' % l4Type )
    if fmt:
        iperfArgs += '-f %s ' % fmt
    server.sendCmd( iperfArgs + '-s' + '--one-off' )
    if l4Type == 'TCP' or l4Type == 'UDP':
        if not waitListening( client, server.IP(), port ):
            raise Exception( 'Could not connect to iperf on port %d'
                             % port )
    cliout = client.cmd( iperfArgs + '-t %d -c ' % seconds +
                         server.IP() + ' ' + bwArgs )
    debug( 'Client output: %s\n' % cliout )
    servout = ''
    # We want the last *b/sec from the iperf server output
    # for TCP, there are two of them because of waitListening
    count = 2 if l4Type == 'TCP' else 1
    while len( re.findall( '/sec', servout ) ) < count:
        servout += server.monitor( timeoutms=5000 )
    server.sendInt()
    servout += server.waitOutput()
    debug( 'Server output: %s\n' % servout )
    result = [ net._parseIperf( servout ), net._parseIperf( cliout ) ]
    if l4Type == 'UDP':
        result.insert( 0, udpBw )
    output( '*** Results: %s\n' % result )
    return result


def do_iperf2(net, h1, h2, bw, time, port, bg=None):
    info('### do iperf %s(%s) => %s(%s), bw: %sbps, time: %ds, port: %d\n' % 
        (h1.name, h1.IP(), h2.name, h2.IP(), bw, time, port))
    result = iperf3(net, [h1, h2], 'UDP', udpBw=bw, seconds=time, port=port)
    if bg:
        bg.ports[h2.name].put(port)

def do_itg(net, h1, h2, bw, size, port=None, bg=None):
    log_arg = '-x ../itg-log/{}-{}-{}'.format(h1.name, h2.name, time.time())
    dest_arg = '-a {}'.format(h2.IP())
    pro_arg = '-T UDP'
    delay_arg = '-m owdm'
    rp = random.randint(3000, 13000)
    sp = random.randint(3000, 13000)
    port_arg = '-rp {} -sp {}'.format(rp, sp)

    pkt_rate = int(math.ceil(bw * 128))

    pkt_arg = '-c 1024 -C {pkt_rate} -k {size}'.format(pkt_rate=pkt_rate, size=size)

    cmd = 'ITGSend {dest_arg} {pro_arg} {pkt_arg} {delay_arg} {port_arg} {log_arg}'.format(
        dest_arg=dest_arg, pro_arg=pro_arg, pkt_arg=pkt_arg, delay_arg=delay_arg,
        port_arg=port_arg, log_arg=log_arg)

    # print('>>> {}({}) do_ITG: {}'.format(h1.name, h1.IP(), cmd))

    h1.popen(cmd, shell=True)

def do_sendPkt(net, h1, h2, bw, size, port, measure=False):
    '''
        size: KB
        bw: mbps
    '''
    pkt_rate = int(math.ceil(bw * 128))

    if measure:
        port = MEASURE_PORT
        if size < MEASURE_PKTS:
            size = MEASURE_PKTS
        pkt_rate = MEASURE_RATE
        print('>>> {}({}) send measure to {}: {}/s({})'.format(
            h1.name, h1.IP(), h2.IP(), pkt_rate, size))
    else:
        port = random.randint(RANDOM_MIN, RANDOM_MAX)

    do_sendByPktCnt(h1, h2, size, pkt_rate, port, measure)


def do_sendByPktCnt(h1, h2, pkts, rate, port, measure=False):
    nic = '{}-eth0'.format(h1.name)
    args = ''
    if measure:
        args = '-m'
    else:
        args = '-log {}'.format(LOG_DIR)

    cmd = 'send {args} -name {name} -r {rate} -k {pkts} -p {port} -i {nic} {dst}'.format(
        args=args, name=h1.name, rate=rate, pkts=pkts, port=port, nic=nic, dst=h2.IP())
    # print('>>> {}({}) do_sendPkt: {}'.format(h1.name, h1.IP(), cmd))
    if measure:
        h1.cmdPrint(cmd)
    else:
        h1.popen(cmd, shell=True)
    # h1.cmd(cmd)


class BackGroundTraffic(threading.Thread):
    def __init__(self, net, rate, log_dir):
        threading.Thread.__init__(self)
        self.net = net
        self.hosts = net.hosts
        self.rate = rate
        self.bucket = TokenBucket(1, rate)
        self.isRunning = True
        # self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitor = OutputMonitor(net, net.hosts)
        self.latency_dic = log_dir
        info('BackGroundTraffic: %d/s "latency dir: %s"\n' % (rate, log_dir))

    def listen_measure(self):
        info('start to open receiver... %d left\n' % (len(self.hosts)))
        #self.monitor.start()
        for host in self.hosts:
            #host.popen('ITGRecv')
            cmd = 'recv -name {} -p {} -k {} -d {} -t {} -log {}'.format(
                host.name, MEASURE_PORT, MEASURE_PKTS, self.latency_dic, FLOW_TIMEOUT, LOG_DIR)
            info('%s run: %s\n' % (host.name, cmd))
            host.popen(cmd, shell=True)
            #host.cmdPrint(cmd)
            res = waitUdpListening(host, MEASURE_PORT, timeout=3)
            info('%s start to listen port: %d, listening: %s\n' % (host.name, MEASURE_PORT, res))


    def pick_hosts(self):
        h1 = random.choice(self.hosts)
        h2 = random.choice(self.hosts)
        while h2 == h1:
            h2 = random.choice(self.hosts)

        return h1, h2

    def send_mice(self, h1, h2, measure=False):
        '''
            mice flow is between 100KB - 200KB, 
            and bit rate is below 3.3Mbps
        '''
        size = random.randint(100, 200)
        rate = random.randint(1, 4) * 128
        #self.executor.submit(send_traffic, h1, h2, size, rate)
        #send_traffic(h1, h2, size, rate)
        #port = self.ports[h2.name].get()
        
        #do_iperf(self.net, h1, h2, '%dM' % rate, transport_time(size, rate), port, self)
        #self.executor.submit(do_itg, self.net, h1, h2, rate*1024, size, port, self)
        do_sendPkt(self.net, h1, h2, rate, size, 0, measure)

    def send_elephant(self, h1, h2, measure=False):
        '''
            elephant flow is between 10MB - 20 MB
            and bit rate is upon 3.3Mbps
        '''
        size = random.randint(10, 20) * 1024
        rate = random.uniform(4, 100) * 128
        #self.executor.submit(send_traffic, h1, h2, size, rate)
        #port = self.ports[h2.name].get()
        #do_iperf(self.net, h1, h2, '%dM' % rate, transport_time(size, rate), port, self)
        # self.executor.submit(do_itg, self.net, h1, h2, rate*1024, size, port, self)
        do_sendPkt(self.net, h1, h2, rate, size, 0, measure)


    def create_flow(self):
        h1, h2 = self.pick_hosts()
        type_traffic = random.randint(1, 10)

        if(type_traffic > 9):
            #info('### create elephant %s => %s\n' % (h1.name, h2.name))
            self.send_elephant(h1, h2)
        else:
            #info('### create mice %s => %s\n' % (h1.name, h2.name))
            self.send_mice(h1, h2)

    def send_measure(self, hn1, hn2):
        h1 = self.net.getNodeByName(hn1)
        h2 = self.net.getNodeByName(hn2)

        self.send_mice(h1, h2, measure=True)

    def start_host_traffic(self, name):
        host = self.net.getNodeByName(name)
        print('get node: ', host.name)
        ip_list = [h.IP() for h in self.hosts]
        ip_str = ' '.join(ip_list)
        rate = int(self.rate / len(ip_list))
        if rate < 1:
            rate = 1

        nic = '{}-eth0'.format(host.name)

        cmd = 'traffic -name {name} -r {rate} -i {nic} -log {log} -p {port} -range 1000 {ips}'.format(
            name=host.name, rate=rate, nic=nic, log=LOG_DIR, port=MEASURE_PORT, ips=ip_str
        )
        print(cmd)
        host.popen(cmd, shell=True)

    def start_traffic(self):
        info("start traffic...\n")
        ip_list = [host.IP() for host in self.hosts]
        ip_str = ' '.join(ip_list)
        rate = int(self.rate / len(ip_list))
        if rate < 1:
            rate = 1
        for host in self.hosts:
            nic = '{}-eth0'.format(host.name)

            cmd = 'traffic -name {name} -r {rate} -i {nic} -log {log} -p {port} -range 1000 {ips}'.format(
                name=host.name, rate=rate, nic=nic, log=LOG_DIR, port=MEASURE_PORT, ips=ip_str
            )
            print(cmd)
            host.popen(cmd, shell=True)

    def stop_traffic(self):
        for host in self.hosts:
            info('kill traffic on host %s\n' % host.name)
            host.cmd('killall traffic')
        info('traffic stop...\n')


    def start_tcpreplay(self, prefix, host_list=None):
        info('TCP REPLAY: {}\n'.format(prefix))
        hosts = None
        popens = []
        if not host_list:
            hosts = self.hosts
        else:
            hosts = [self.net.getNodeByName('h%d' % x) for x in host_list]
        info('host list: {}\n'.format([h.name for h in hosts]))
        for host in hosts:
            pcap_name = '{}_{}.pcap'.format(prefix, host.IP())
            file_name = os.path.join(PCAP_DIR, pcap_name)
            cmd = 'tcpreplay -i {} {}'.format(host.defaultIntf().name, file_name)
            info('{} start tcpreplay: {}\n'.format(host.name, cmd))
            popen = host.popen(cmd)
            popens.append(popen)

        return popens

    def stop_tcpreplay(self, popens):
        if not popens:
            info('no tcpreplay process\n')
            return

        info('stop TCP REPLAY\n')
        for popen in popens:
            popen.kill()


    def run(self):
        info("start to generate background traffic, rate: %d\n" % (self.rate))
        count = 0
        prev = time.time()
        while self.isRunning:
            if self.bucket.consume(1):
                self.create_flow()
                count += 1
            else:
                time.sleep(0.001)
                now = time.time()
                if now - prev > 60:
                    print('### flow created: {}, rate: {:.1f}'.format(count,
                         count / float(now - prev)))
                    prev = now
                    count = 0


    def stop_recv(self):
        self.isRunning = False
        for host in self.hosts:
            info('kill receiver on host %s\n'% host.name)
            host.cmd("killall recv")
        info('background stop...\n')


def test_send(net, h1, h2):
    client = net.getNodeByName(h1)
    server = net.getNodeByName(h2)

    do_sendPkt(net, client, server, 100, 1, 0, measure=False)

def main():
    setLogLevel('info')
    cleanup()
    #topo = BaseTopo()

    # h1 = topo.addHost('h1')
    # h2 = topo.addHost('h2')

    # s1 = topo.addSwitch('s1')

    # topo.addLink(h1, s1, cls=TCLink, bw=100, max_queue_size=100)
    # topo.addLink(h2, s1, cls=TCLink, bw=100, max_queue_size=100)

    topo = SimpleTopo()
    net = build_mine(topo, total_cpu=.5)
    net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT)
    net.start()
    set_flowTable_limit(topo, 2000, policy='evict')

    topo.showLinks()

    net.pingAll()
    wait(3)

    bg = BackGroundTraffic(net, 10, LATENCY_DIR)
    bg.start()

    #bg.send_measure('h1', 'h3')
    # wait(20)
    # test_send(net)
    # msgs = net.monitor([net.getNodeByName('h3')])
    # for msg in msgs:
    #     print(msg)

    CLI(net)
    bg.stop()
    cleanup()

if __name__ == '__main__':
    main()