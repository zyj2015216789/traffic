#!/usr/bin/python
import os
import subprocess
import traceback

import paramiko
from scp import SCPClient
try:
    import pwd
except ImportError:
    import winpwd as pwd

def getSSH(ip, user, passwd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, 22, user, passwd, timeout=5)
    return ssh

def execute(ssh, shell, stdin=''):
    cmd = "bash -l -c '{}'".format(shell)
    print(cmd)
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        for line in stdout:
            print(line.strip('\n'))
        for line in stderr:
            print(line.strip('\n'))
    except Exception as e:
        print('execute command %s error, error message is %s' % (cmd, repr(e)))
        print(traceback.format_exc())

def transportFile(ssh, src, dst):
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(src, dst)

def exec_cmd(USER, SHELL):

    try:
        pw_record = pwd.getpwnam(USER)
    except Exception, e:
        print('user {} is not exist'.format(USER))
        return False
    user_name      = pw_record.pw_name
    user_home_dir  = pw_record.pw_dir
    user_uid       = pw_record.pw_uid
    user_gid       = pw_record.pw_gid
    env = os.environ.copy()
    env[ 'HOME'     ]  = user_home_dir
    env[ 'LOGNAME'  ]  = user_name
    env[ 'PWD'      ]  = user_home_dir
    env[ 'USER'     ]  = user_name
    env[ 'PATH'     ]  += ':/home/loveacat/project/onos/tools/test/bin'
    cwd = user_home_dir

    cmd = SHELL
    print('excuting: {}'.format(cmd))
    proc = subprocess.Popen(cmd, preexec_fn=demote(user_uid, user_gid), cwd=cwd, env=env, shell=True)
    proc.wait()

    return proc.returncode == 0


def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result


if __name__ == '__main__':
    ssh = getSSH('127.0.0.1', 'loveacat', 'cat')
    execute(ssh, 'export PATH=$PATH:/home/loveacat/project/onos/tools/dev/bash_profile')
    execute(ssh, 'env')
    execute(ssh, 'onos localhost apps -s')
