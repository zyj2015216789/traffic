from rpc.rpc import *

if __name__ == '__main__':
    print("start rpc server...")
    onos = getOnosProcess()
    print('onos pid: {}'.format(onos.pid))
    startRPCServer(ip='0.0.0.0', port=2334)