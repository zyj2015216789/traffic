import sys, os

_file_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.dirname(_file_path))
print(sys.path)


import utils


def testRunCmd():
    cmd = 'lsof -i:22'
    res = utils.runCmd(cmd)
    print(res)


if __name__ == '__main__':
    testRunCmd()