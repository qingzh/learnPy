# -*- coding: utf-8 -*-
import threading
import time


def f(i, results):
    results.append(i)
    print threading.current_thread().name, ' [START]'
    time.sleep(i)
    print threading.current_thread().name, ' [END]'


def main():
    g = []
    func_thread = lambda x: threading.Thread(target=f, name=x, args=(x, g))
    threads = map(func_thread, [5, 8, 12, 9])
    # the whole program will wait for the alive non-daemon threads
    daemonic = False
    map(lambda x: x.setDaemon(daemonic), threads)
    map(lambda x: x.start(), threads)
    map(lambda x: x.join(), threads)

import multiprocessing as mp
import subprocess
import shlex
import os

reldir = os.path.dirname(os.path.relpath(__file__))
SCRIPT_PATH = os.path.join(reldir, 'test2.py')  # or './test2.py'


def worker(q):
    while True:
        # Get an argument from the queue
        x = q.get()

        # You might change this to run your C++ program
        proc = subprocess.Popen(
            shlex.split('python {s} {x}'.format(s=SCRIPT_PATH, x=x)), stdout=subprocess.PIPE)
        out, err = proc.communicate()

        print('{name}: using argument {x} outputs {o}'.format(
            x=x, name=mp.current_process().name, o=out))

        q.task_done()

        # Put a new argument into the queue
        q.put(int(out))


def mp_main():
    q = mp.JoinableQueue()

    # Put some initial values into the queue
    for t in range(1, 3):
        q.put(t)

    # Create and start a pool of worker processes
    for i in range(3):
        p = mp.Process(target=worker, args=(q,))
        p.daemon = True
        p.start()
    q.join()
    print "Finished!"

if __name__ == '__main__':
    mp_main()
