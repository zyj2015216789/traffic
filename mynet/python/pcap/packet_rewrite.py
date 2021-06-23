# encoding: utf-8

from scapy.all import *
import sys
import json
import os
import time


def print_process(count, total):
    percent = float(count) / float(total)
    print('{}/{} processed, {:>5.2f}'.format(count, total, percent))


def generate_shell(host_num, filename_input, filename_output, shell):
    print('generate_shell ...')
    input_pcap = PcapReader(filename_input).read_all()
    #input_pcap = rdpcap(filename_input)
    output = PcapWriter(filename_output)

    # hosts, IP : MAC
    count = 0
    hosts = {}
    for packet in input_pcap:
        if 'IP' in packet and 'Ether' in packet:
            if packet['IP'].src in hosts:
                hosts[packet['IP'].src].append(packet['Ether'].src)
            else:
                hosts[packet['IP'].src] = []
                hosts[packet['IP'].src].append(packet['Ether'].src)

            if packet['IP'].dst in hosts:
                hosts[packet['IP'].dst].append(packet['Ether'].dst)
            else:
                hosts[packet['IP'].dst] = []
                hosts[packet['IP'].dst].append(packet['Ether'].dst)
        count += 1
        if count % 100000 == 0:
            print_process(count, 1)

    input_pcap.close()
    # output ips
    ips = []
    for i in range(1, host_num + 1):
        ips.append("10.0.0.%s" % (i))

    flag = 0
    idx = 0
    f = open(shell, "wb")
    f.write("#!/bin/bash\n\n")
    f.write("tcprewrite --infile=%s --outfile=%s --skipbroadcast --skip-soft-errors --skipl2broadcast --pnat=" % (filename_input, filename_output))
    for i in hosts:
        hosts[i] = list(set(hosts[i]))
        if not flag:
            f.write('"%s":"%s"' % (i, ips[idx]))
            flag = 1
        else:
            f.write(',"%s":"%s"' % (i, ips[idx]))
        idx += 1
        idx %= host_num
    f.close()

    print("Generate %s successfully!\n" % (shell))

def exec_shell(shell):
    output = os.popen('./%s' % (shell))
    print output.read()


def list_ips(filename_input, host_num, output_ips, output_macs, output_ip_macs):
    print('list ips ...')
    input_pcap = PcapReader(filename_input)
    #input_pcap = rdpcap(filename_input)
    #print('total {} packets'.format(len(input_pcap)))
    # hosts, IP : MAC
    hosts = {}
    count = 0
    for packet in input_pcap:
        if 'IP' in packet and 'Ether' in packet:
            if packet['IP'].src in hosts:
                hosts[packet['IP'].src].append(packet['Ether'].src)
            else:
                hosts[packet['IP'].src] = []
                hosts[packet['IP'].src].append(packet['Ether'].src)

            if packet['IP'].dst in hosts:
                hosts[packet['IP'].dst].append(packet['Ether'].dst)
            else:
                hosts[packet['IP'].dst] = []
                hosts[packet['IP'].dst].append(packet['Ether'].dst)

        count += 1
        if count % 100000 == 0:
            print_process(count, 1)

    input_pcap.close()
    # output ips
    ips = []
    for i in range(1, host_num + 1):
        ips.append("10.0.0.%s" % (i))

    macs = []
    for i in range(1, host_num + 1):
        macs.append("0c:0c:0c:0c:0c:0%s" % (i))

    flag = 0
    idx = 0
    f = open(output_ips, "wb")
    f.write("{")
    for i in hosts:
        hosts[i] = list(set(hosts[i]))
        if not flag:
            f.write('\n"%s":"%s"' % (i, ips[idx]))
            flag = 1
        else:
            f.write(',\n"%s":"%s"' % (i, ips[idx]))
        idx += 1
        idx %= host_num
    f.write("\n}")
    f.close()

    flag = 0
    idx = 0
    f = open(output_macs, "wb")
    f.write("{")
    for i in ips:
        if not flag:
            f.write('\n"%s":"%s"' % (i, macs[idx]))
            flag = 1
        else:
            f.write(',\n"%s":"%s"' % (i, macs[idx]))
        idx += 1
    f.write("\n}")
    f.close()

    # output ip_macs
    f = open(output_ip_macs, "wb")
    f.write(json.dumps(hosts))
    f.close()

    # ip_macs format json
    os.system("cat ip_macs.json | python -m json.tool > ip_macs2.json")
    os.system("mv ip_macs2.json ip_macs.json")


def rewrite_ips(filename_input, filename_output, host_num, output_ips, output_macs, output_ip_macs):
    print('rewrite ips ...')
    input_pcap = PcapReader(filename_input)
    #input_pcap = rdpcap(filename_input)
    output_pcap = PcapWriter(filename_output, sync=True)
    #print('total {} packets'.format(len(input_pcap)))
    # ips_json and macs_json
    ips_json = json.loads(open(output_ips).read())
    macs_json = json.loads(open(output_macs).read())

    # ips and macs
    ips = []
    for i in range(1, host_num + 1):
        ips.append("10.0.0.%s" % (i))

    macs = []
    for i in range(1, host_num + 1):
        macs.append("0c:0c:0c:0c:0c:%02x" % (i))

    # rewrite
    count = 0
    for packet in input_pcap:
        if 'IP' in packet:
            if packet['IP'].src in ips_json:
                packet['IP'].src = ips_json[packet['IP'].src]
                if 'Ether' in packet and packet['Ether'].src:
                    packet['Ether'].src = macs_json[packet['IP'].src]
            if packet['IP'].dst in ips_json:
                packet['IP'].dst = ips_json[packet['IP'].dst]
                if packet['IP'].dst == packet['IP'].src:
                    packet['IP'].dst = ips[(ips.index(packet['IP'].src) + 1) / host_num]
                if 'Ether' in packet and packet['Ether'].dst:
                    packet['Ether'].dst = macs_json[packet['IP'].dst]
                    if packet['Ether'].dst == packet['Ether'].src:
                        packet['Ether'].dst = macs[(macs.index(packet['Ether'].src) + 1) / host_num]
            if 'TCP' in packet and 'Raw' in packet:
                packet['Raw'].load = '0' * (packet['IP'].len - 40)

        # packet.show()
        if 'IP' in packet and ('TCP' in packet or 'UDP' in packet):
            output_pcap.write(packet)
        count += 1
        if count % 100000 == 0:
            print_process(count, 1)
    output_pcap.close()
    input_pcap.close()

    # ip_macs format json
    os.system("rm -r ips.json")
    os.system("rm -r macs.json")
    os.system("rm -r ip_macs.json")


def main():
    print('packet_rewrite: {}'.format(sys.argv))
    type = sys.argv[1]
    host_num = int(sys.argv[3])
    filename_input = sys.argv[2]
    filename_output = sys.argv[4]
    if type == "tcprewrite":
        shell = sys.argv[5]
        generate_shell(host_num, filename_input, filename_output, shell)
        exec_shell(shell)
    elif type == "rewrite":
        output_ips = sys.argv[5]
        output_macs = sys.argv[6]
        output_ip_macs = sys.argv[7]
        list_ips(filename_input, host_num, output_ips, output_macs, output_ip_macs)

        filename_input = sys.argv[2]
        rewrite_ips(filename_input, filename_output, host_num, output_ips, output_macs, output_ip_macs)


if __name__ == "__main__":
    main()