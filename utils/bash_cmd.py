
import re
import subprocess
import sys
import os
import ossdownload
import logging

reload(sys)
sys.setdefaultencoding('utf8')

logger = logging.getLogger(__name__)
STDOUT = logging.StreamHandler(sys.stdout)
STDOUT.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(STDOUT)


class BashFailException(Exception):

    pass


def exec_args(args, **kwargs):
    kwargs.setdefault('shell', False)
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.PIPE)
    if not isinstance(args, (list, tuple)):
        raise ValueError("args should be list!")
    logger.debug('%s\n%s', '-'*30, ' '.join(args))
    ssh = subprocess.Popen(args, **kwargs)
    ssh.wait()
    if ssh.returncode != 0:
        error = ssh.stderr.read()
        logger.error('ERROR: %s', error)
        # sys.stderr.write("ERROR: %s" % error)
        print >>sys.stderr, "ERROR: %s" % error
        raise BashFailException("Failed: %s", error)
    result = ssh.stdout.read()
    logger.debug('SUCCESS: %s', result)
    return result


def scp_out(host, local_file, remote_file, remote_user=None):
    ''' scp /tmp/${war_name} {username}@${ip}:/tmp/ '''
    try:
        if remote_user:
            host = '%s@%s' % (remote_user, host)
        log = exec_args(
            ["scp", local_file, "%s:%s" % (host, remote_file)])
        logger.debug('scp file[%s] to server[%s] success.',
                     local_file, remote_file)
    except Exception:
        raise BashFailException('scp to %s: 传输文件失败', host)
    return log


def scp_in(host, local_file, remote_file, remote_user=None):
    ''' scp {username}@${ip}:{remote_file} {local_file} '''
    try:
        if remote_user:
            host = '%s@%s' % (remote_user, host)
        log = exec_args(
            ["scp", "%s:%s" % (host, remote_file), local_file])
        logger.debug('scp file[%s] from server[%s] success.',
                     local_file, remote_file)
    except Exception:
        raise BashFailException('scp from %s: 传输文件失败', host)
    return log


def netcat(host, port):
    ''' nc -v -z ip port '''
    try:
        log = exec_args(
            ["nc", "-v", "-z", '%s' % host, '%s' % port])
        logger.debug('netcat %s:%s success.', host, port)
    except Exception:
        raise BashFailException('%s:%s: 端口未启动' % (host, port))
    return log
