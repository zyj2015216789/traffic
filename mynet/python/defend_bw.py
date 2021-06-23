#!/usr/bin/python
import os
import traceback, threading
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections

from configurations.directories import *
from topo.topos import *
from traffic.background import BackGroundTraffic, test_send
from utils.experiment import *
from utils import *

#switches = ['s2', 's4', 's5', 's6', 's13']
switches = []
host_pairs = [(1, 5), (1, 9), (1, 13)]
#host_pairs = [(2, 5), (2, 9), (2, 13)]
bg_list = [i for i in range(1, 17, 2)]
#bg_list.append(2)
#bg_list = [1]
def start_experiment(name, attack_rate):
    result_path = get_log_path()

    #topo = SimpleTopo(bw=100)
    topo = FatTree(bw=100)
    result = Result(name)

    #topo = FloodShield(bw=100)
    net = None
    sched = None
    popens = None
    bg = None
    proc = None
    try:
        net = build_mine(topo, total_cpu=.5)

        net.start()

        set_host_mac(net)
        set_flowTable_limit(topo, 2000, table=0, policy='refuse')
        #set_flowTable_limit(topo, 2000, table=1, policy='refuse')
        dumpNodeConnections(net.hosts)

        # net.startTerms()
        # net.runCpuLimitTest(.25)
        CLI(net)

        net.pingAll()
        #defend_all(net)
        add_host_all(net, opt='add')
        #observe_point('10.0.0.1', opt='add')

        bg = BackGroundTraffic(net, 20, os.path.join(result_path, 'latency'))
        bg.listen_measure()
        #bg.start_traffic()
        show_path(net, 'h2', 'h16')
        # background status
        sched, q = start_util(result, topo, switches)
        wait(3)
        #CLI(net)
        popens = bg.start_tcpreplay('origin_rewrite_tshark', bg_list)

        # for i in range(5):
        #     print('>>>>>>>>>>>>>>>>> {}:bandwidth round {}'.format(name, i))
        #     for hosts in host_pairs:
        #         bw = test_bw(net, id2name(hosts[0]), id2name(hosts[1]))
        #         result.add_bandwidth(bw)

        if attack_rate > 0:
            add_host_host(net, 'h2', opt='attack')
            proc = test_attack_udp(net, 'h2', 'h1', rate=attack_rate, randDstPort=True,
                                   log=result_path)

        wait(6)
        #proc.kill()
        #CLI(net)
        #wait(100)
        #
        # """
        #     experiment start here
        # """
        #
        print("start experiment {}... attack rate = {}".format(name, attack_rate))

        # for i in range(20):
        #     wait(30)
        #     show_accu()

        for hosts in host_pairs:
            for i in range(10):
                print('****************** {}:latency round {}'.format(hosts, i + 1))
                bg.send_measure(id2name(hosts[0]), id2name(hosts[1]))

        for i in range(5):
            print('>>>>>>>>>>>>>>>>> {}:bandwidth round {}'.format(name, i + 1))
            for hosts in host_pairs:
                bw = test_bw(net, id2name(hosts[0]), id2name(hosts[1]))
                result.add_bandwidth(bw)

        make_permanent(result_path, result)
        print_results([result])
        #CLI(net)
        show_accu()


    except Exception, e:
        print(traceback.format_exc())
        print(repr(e))
        cleanup()
    finally:
        if bg:
            bg.stop_tcpreplay(popens)
            #bg.stop_traffic()
            bg.stop_recv()
        if sched:
            sched.shutdown()
        if proc:
            print('kill attackers...')
            proc.kill()
        if net:
            net.stop()



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
    os.system('killall tcpreplay')
    setLogLevel('info')
    cleanup()

    rate = 1100
    name = 'df-{}-h2-h1'.format(rate)
    print(name)
    start_experiment(name, rate)


if __name__ == '__main__':
    print("start experiment demo")
    kill_all_receiver()
    main()
