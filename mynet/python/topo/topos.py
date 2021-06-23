import shlex
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.topo import Topo
from mininet.util import custom
from subprocess import check_output, CalledProcessError

from configurations.controllers import CONTROLLER_IP, CONTROLLER_PORT

def build_mine(topo, total_cpu=.2, sched='cfs', period_us=100000):
    nb_hosts = len(topo.hosts())

    host = custom( CPULimitedHost, sched=sched,
                       period_us=period_us,
                       cpu=total_cpu/nb_hosts)
    info('*** allocated %.2f%%(%.2f%%) cpu to each hosts\n' %
        (total_cpu / nb_hosts * 100, total_cpu * 100))
    net = Mininet(topo=topo, host=host, controller=None)
    net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT)
    return net

def set_flowTable_limit(topo, limit, table=0, policy='refuse'):
    print("set flow table size")
    switches = topo.switches()

    for switch in switches:
        cmd = 'ovs-vsctl  --  --id=@ft  \
            create  Flow_Table flow_limit=%d \
            overflow_policy=refuse -- set Bridge %s flow_tables=%d=@ft' % \
              (limit, switch, table)

        if policy == 'evict':
            cmd = 'ovs-vsctl  --  --id=@ft  \
            create  Flow_Table flow_limit=%d \
            overflow_policy=evict groups=\'\"NXM_OF_IP_PROTO[]\"\' \
            -- set Bridge %s flow_tables:%d=@ft' % (limit, switch, table)

        cmd = shlex.split(cmd)
        info(cmd)

        output = 0
        try:
            output = check_output(cmd)
        except CalledProcessError, e:
            print('error: %d set limit "%s": %s' % (output, switch, repr(e)))
        else:
            info('set limit: %s => %d' % (switch, limit))
        finally:
            info('\n\n')


def set_host_mac(net):
    nb_hosts = len(net.hosts)

    for i in range(1, nb_hosts + 1):
        mac = '0c:0c:0c:0c:0c:%02d' % i
        name = 'h%d' % i
        h = net.getNodeByName(name)
        h.setMAC(mac, intf=h.defaultIntf())
        info('set {} mac {}, result: {}\n'.format(name, mac, h.defaultIntf().updateAddr()))


class BaseTopo(Topo):
    def __init__(self, bw=None, max_queue_size=None):
        Topo.__init__(self)
        self.bandwidth = bw
        self.max_queue_size = max_queue_size

    def addTCLink(self, node1, node2):
        self.addLink(node1, node2, cls=TCLink, bw=self.bandwidth, max_queue_size=self.max_queue_size)

    def showLinks(self):
        print('total {} links'.format(len(self.links())))
        for link in self.links():
            print(self.linkInfo(link[0], link[1]))



class SimpleTopo(BaseTopo):

    def __init__(self, bw=None, max_queue_size=None):
        BaseTopo.__init__(self)

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        self.addLink(s1, s2, cls=TCLink, bw=bw, max_queue_size=max_queue_size)
        self.addLink(s2, s3, cls=TCLink, bw=bw, max_queue_size=max_queue_size)

        self.addLink(h1, s1, cls=TCLink, bw=bw, max_queue_size=max_queue_size)
        self.addLink(h2, s1, cls=TCLink, bw=bw, max_queue_size=max_queue_size)
        self.addLink(h5, s1, cls=TCLink, bw=bw, max_queue_size=max_queue_size)

        self.addLink(h3, s3, cls=TCLink, bw=bw, max_queue_size=max_queue_size)
        link = self.addLink(h4, s3, cls=TCLink, bw=bw, max_queue_size=max_queue_size)



class FloodShield(BaseTopo):
    def __init__(self, bw=None, max_queue_size=None):
        BaseTopo.__init__(self)

        self.bandwidth = bw
        self.max_queue_size = max_queue_size

        hosts = [self.addHost('h%d' % (i)) for i in range(1, 9)]

        switches = [self.addSwitch('s%d' % (i)) for i in range(1, 11)]

        switch_connections = [
                        (1, 3), (1, 7), (2, 4), (2, 8),
                        (3, 5), (3, 6), (4, 5), (4, 6),
                        (7, 9), (7, 10), (8, 9), (8, 10),
                        ]

        host_connections = [
                        (1, 5), (2, 5), (3, 6), (4, 6), (5, 9), (6, 9), (7, 10), (8, 10)
                        ]

        #switch links
        for link in switch_connections:
            self.addTCLink(switches[link[0] - 1], switches[link[1] - 1])

        #edge links
        for link in host_connections:
            self.addTCLink(hosts[link[0] - 1], switches[link[1] - 1])

class FatTree(BaseTopo):
    def __init__(self, bw=None, max_queue_size=None):
        BaseTopo.__init__(self)
        self.bandwidth = bw
        self.max_queue_size = max_queue_size

        hosts = [self.addHost('h%d' % (i)) for i in range(1, 17)]
        switches = [self.addSwitch('s%d' % (i)) for i in range(1, 21)]

        switch_connections = [
            # core
            (1, 5), (1, 7), (1, 9), (1, 11),
            (2, 5), (2, 7), (2, 9), (2, 11),
            (3, 6), (3, 8), (3, 10), (3, 12),
            (4, 6), (4, 8), (4, 10), (4, 12),
            # pod 1
            (5, 13), (5, 14), (6, 13), (6, 14),
            # pod 2
            (7, 15), (7, 16), (8, 15), (8, 16),
            # pod 3
            (9, 17), (9, 18), (10, 17), (10, 18),
            # pod 4
            (11, 19), (11, 20), (12, 19), (12, 20),
        ]

        host_connections = [
            (1, 13), (2, 13), (3, 14), (4, 14),
            (5, 15), (6, 15), (7, 16), (8, 16),
            (9, 17), (10, 17), (11, 18), (12, 18),
            (13, 19), (14, 19), (15, 20), (16, 20),
        ]

        # switch links
        for link in switch_connections:
            self.addTCLink(switches[link[0] - 1], switches[link[1] - 1])

        # edge links
        for link in host_connections:
            self.addTCLink(hosts[link[0] - 1], switches[link[1] - 1])


class LinkedTopo(BaseTopo):
    def __init__(self, nb_switches, nb_hosts, switch_connections, host_connections, bw=None, max_queue_size=None):
        BaseTopo.__init__(self)
        self.bandwidth = bw
        self.max_queue_size = max_queue_size

        hosts = [self.addHost('h%d' % (i)) for i in range(1, nb_hosts+1)]

        switches = [self.addSwitch('s%d' % (i)) for i in range(1, nb_switches+1)]

        #switch links
        for link in switch_connections:
            self.addTCLink(switches[link[0] - 1], switches[link[1] - 1])

        #edge links
        for link in host_connections:
            self.addTCLink(hosts[link[0] - 1], switches[link[1] - 1])


if __name__ == '__main__':
    setLogLevel('info')
    cleanup()
    topo = SimpleTopo()

    net = build_mine(topo, total_cpu=.4)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()
    set_flowTable_limit(topo, 2000, policy='evict')

    topo.showLinks()

    #net.pingAll()

    CLI(net)
    cleanup()