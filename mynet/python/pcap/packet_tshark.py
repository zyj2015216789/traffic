# encoding: utf-8

import sys
import os


# tshark -r smallFlowsHandled.pcap -Y "ip.src == 10.0.0.4" -w smallFlowsHandled_10.0.0.4.pcap
def generate_tshark(host_num, filename_input, filename_output, shell):
    f = open(shell, "wb")
    f.write("#!/bin/bash\n\n")

    for i in range(1, host_num + 1):
        f.write("tshark -r %s -Y \"ip.src == 10.0.0.%d\" -w %s_10.0.0.%d.pcap\n" % (filename_input, i, filename_output, i))
    f.close()

    print("Generate %s successfully!" % (shell))


def exec_shell(shell):
    output = os.popen('./%s' % (shell))
    print output.read()


def main():
    host_num = int(sys.argv[2])
    filename_input = sys.argv[1]
    filename_output = sys.argv[3]
    shell = sys.argv[4]
    generate_tshark(host_num, filename_input, filename_output, shell)
    exec_shell(shell)


if __name__ == "__main__":
    main()

