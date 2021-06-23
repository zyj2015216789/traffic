#!/usr/bin/python
import os
import traceback, threading
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections

from configurations.directories import *
from topo.topos import set_flowTable_limit, SimpleTopo, build_mine, FloodShield, FatTree
from traffic.background import BackGroundTraffic, test_send
from utils.experiment import *
from utils import *

switches = ['s13']
host_pairs = [(1, 3), (1, 5), (1, 9), (1, 13)]


def start_experiment(name, attack_rate):
    result_path = get_log_path()

    #topo = SimpleTopo(bw=100)
    topo = FatTree(bw=100)
    result = Result(name)
    # background status
    sched, q = start_util(result, topo, switches)

    #topo = FloodShield(bw=100)

    popens = None
    bg = None

    try:
        net = build_mine(topo, total_cpu=.5)

        net.start()

        set_flowTable_limit(topo, 2000, table=0, policy='refuse')
        set_flowTable_limit(topo, 2000, table=1, policy='refuse')
        dumpNodeConnections(net.hosts)

        # net.startTerms()
        # net.runCpuLimitTest(.25)
        CLI(net)


        wait(2)
        net.pingAll()
        #defend_all(net)
        add_host_all(net, opt='add')
        #observe_point('10.0.0.1', opt='add')

        bg = BackGroundTraffic(net, 20, os.path.join(result_path, 'latency'))
        bg.listen_measure()
        #bg.start_traffic()
        #popens = bg.start_tcpreplay()

        proc = None
        if attack_rate > 0:
            proc = test_attack_udp(net, 'h2', 'h1', rate=attack_rate, randDstPort=True)

        wait(3)


        """
            experiment start here
        """

        print("start experiment {}... attack rate = {}".format(name, attack_rate))

        for hosts in host_pairs:
            for i in range(10):
                print('****************** {}:latency round {}'.format(hosts, i))
                bg.send_measure(id2name(hosts[0]), id2name(hosts[1]))
            #wait(13)


        # for i in range(10):
        #     print('>>>>>>>>>>>>>>>>> {}:bandwidth round {}'.format(name, i))
        #     for hosts in host_pairs:
        #         bw = test_bw(net, id2name(hosts[0]), id2name(hosts[1]))
        #         result.add_bandwidth(bw)


        #CLI(net)

        if proc:
            print('kill attackers...')
            proc.kill()

        if sched:
            sched.shutdown()

        make_permanent(result_path, result)

        bg.stop_traffic()
        bg.stop_recv()
        net.stop()

    except Exception as e:
        print(traceback.format_exc())
        print(repr(e))
        cleanup()
    finally:
        if bg:
            bg.stop_tcpreplay(popens)



class IPRequester(threading.Thread):
    def __init__(self, host, interval=3.0):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.is_running = True
        self.host = host
        self.interval = interval

    def run(self):
        info('start to shift ip address...')
        while self.is_running:
            sleep(self.interval)
            setRandomMac(self.host)
            requestIP(self.host)
            intf = self.host.defaultIntf()
            print('{} get new ip: {}'.format(
                self.host.name, intf.updateAddr()))

    def stop(self):
        self.is_running = False

def main():
    setLogLevel('info')
    cleanup()

    rate = 0
    name = 'df-{}-noback'.format(rate)

    start_experiment(name, rate)


if __name__ == '__main__':
    print("start experiment demo")
    kill_all_receiver()
    main()
