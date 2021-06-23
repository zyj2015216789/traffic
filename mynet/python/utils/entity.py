#!/usr/bin/python

from collections import namedtuple
import time

Util = namedtuple('Util', 'time cpu mem table tag')

class Result():
    def __init__(self, name='result', rate=0):
        self.name = name
        self.attack_rate = rate
        self.latency = {}   #key: python-dst value: [Latency, ...]
        self.bandwidth = {} #key: python-dst value: [avg-bw, ...]
        self.utilization = []

    def add_latency(self, result):
        key = '{}-{}'.format(result.src, result.dst)
        l = self.latency.get(key, [])
        l.append(result)
        self.latency[key] = l

    def add_bandwidth(self, result):
        key = '{}-{}'.format(result.src, result.dst)
        l = self.bandwidth.get(key, [])
        l.append(result)
        self.bandwidth[key] = l

    def add_util(self, cpu, mem, table, tag):
        self.utilization.append(Util(time.asctime(), cpu, mem, table, tag))

    def cpu(self):
        return [util.cpu for util in self.utilization]

    def __str__(self):
        s = 'result: {} utilizations: {}\n# latency:\n'.format(self.name, len(self.utilization))
        for k, v in self.latency.iteritems():
            for exp in v:
                s += '{}\n'.format(exp)

        s += '# bandwidth\n'
        for k, v in self.bandwidth.iteritems():
            for exp in v:
                s += '{} '.format(exp)

        return s

class BandWidth():
    def __init__(self, src, dst, bw, unit):
        self.src = src
        self.dst = dst
        self.bw = bw
        self.unit = unit

    def __str__(self):
        return '{} => {} bandwidth: {:>.3f}{}'.format(self.src, self.dst, self.bw, self.unit)

class Latency():
    def __init__(self, src, dst, count):
        self.src = src
        self.dst = dst
        self.min = -1
        self.max = -1
        self.dev = -1
        self.avg = -1
        self.loss = -1
        self.first = -1
        self.sequence = []
        self.count = count

    def check(self):
        return self.min >= 0 and self.max >= 0 and self.dev >= 0 and self.avg >= 0 and self.loss >= 0 and (
            len(self.sequence)) == self.count

    def __str__(self):
        return '%s => %s 1st: %.2f latency(min/avg/max/mdev): (%.2f, %.2f, %.2f, %.2f), loss: %.2f, count: %d, check:%s' % (
            self.src, self.dst, self.first, self.min, self.avg, self.max, self.dev, self.loss, self.count, self.check())

    __repr__ = __str__

