import threading

from utils import captureOutput


class OutputMonitor(threading.Thread):
    def __init__(self, net, hosts):
        threading.Thread.__init__(self)
        self.net = net
        self.hosts = hosts

        self.setDaemon(True)

    def run(self):
       captureOutput(self.net, self.hosts)