from scapy.all import *
import heapq
import random
import shutil

def generalFilePktNumList(filesPath1, filesPath2):
    if filesPath1[len(filesPath1) - 1] != '/':
        filesPath1 = filesPath1 + '/'
    if filesPath2[len(filesPath2) - 1] != '/':
        filesPath2 = filesPath2 + '/'

    numList = {}
    try:
        files = os.listdir(filesPath1)
        for file in files:
            pkts = rdpcap(filesPath1 + file)
            numList[file] = len(pkts)
    except Exception as e:
        print (e)

    fo = open(filesPath2 + "FilePktNumList.txt", "w")
    for file, num in numList.iteritems():
        fo.write(file + ":" + str(num) + "\n")
    fo.close()

    return numList


def aRes(samples, m, path):
    """
    :samples: {(item, weight), ...}
    :m: number of selected items
    :returns: [(item, weight), ...]
    [eighted Random Sampling](https://lotabout.me/2018/Weighted-Random-Sampling/)
    """

    if path[len(path) - 1] != '/':
        path = path + '/'

    heap = [] # [(new_weight, item), ...]
    random.seed(int(time.time()))
    for sample, wi in samples.iteritems():
        ui = random.uniform(0, 1)
        # print(ui)
        ki = ui ** (1.0/wi)
        # print (ki)

        if len(heap) < int(m):
            heapq.heappush(heap, (ki, sample))
        elif ki > heap[0][0]:
            heapq.heappush(heap, (ki, sample))
            if len(heap) > int(m):
                heapq.heappop(heap)

    fo = open(path + "FileList.txt", "w")
    for item in heap:
        fo.write(item[1] + "\n")
    fo.close()

    return [item[1] for item in heap]


def fileCopy(items, pathSrc, pathDst):
    if pathSrc[len(pathSrc) - 1] != '/':
        pathSrc = pathSrc + '/'
    if pathDst[len(pathDst) - 1] != '/':
        pathDst = pathDst + '/'

    try:
        for item in items:
            # print (pathSrc + item)
            # print (pathDst)
            shutil.copy(pathSrc + item, pathDst)
    except Exception as e:
        print (1)
        print (e)

    print ("Weighted random sampling of flows finished, successfully~")


if __name__ == '__main__':  #1:sampling in path;2:sampling number;3:sampling out path
    print (len(sys.argv))
    if len(sys.argv) != 4:
        print("Need three parameters, the first description file folder, the second description the select number and the third description.")
        sys.exit()

    print(sys.argv[1])
    print(sys.argv[2])
    print(sys.argv[3])
    
    numList = generalFilePktNumList(sys.argv[1], sys.argv[3])

    items = aRes(numList, sys.argv[2], sys.argv[3])

    fileCopy(items, sys.argv[1], sys.argv[3])
