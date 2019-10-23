#!/usr/bin/python3

"""
Generic linux daemon base class for python 3.
Based on https://gist.github.com/andreif/cbb71b0498589dac93cb
"""

from sys import (
    stdin,
    stdout,
    stderr
)
import os
import time
import atexit
import signal


class daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""

    def __init__(self, process_name: str):
        self.pid_file = "/run/user/{}/{}/pid".format(str(os.getuid()), process_name)

    def daemonize(self):
        """Daemonize class. UNIX double fork mechanism."""

        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                exit(0)
        except OSError as err:
            stderr.write('fork #1 failed: {}\n'.format(err))
            exit(1)

        # decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit second parent
                exit(0)
        except OSError as err:
            stderr.write("fork #2 failed: {}\n".format(err))
            exit(1)

        # redirect standard file descriptors
        stdout.flush()
        stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), stdin.fileno())
        os.dup2(so.fileno(), stdout.fileno())
        os.dup2(se.fileno(), stderr.fileno())

        # write pid_file
        os.makedirs(os.path.dirname(self.pid_file), exist_ok=True, mode=0o755)
        atexit.register(self.delpid)
        with open(self.pid_file, 'w+') as f:
            f.write(str(os.getpid()) + '\n')

    def delpid(self):
        os.remove(self.pid_file)

    def start(self):
        """Start the daemon."""

        # Check for a pid_file to see if the daemon is already running
        try:
            with open(self.pid_file, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pid_file '{}' already exists (pid {}). Daemon already running?\n"
            stderr.write(message.format(self.pid_file, pid))
            exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon."""

        # Get the pid from the pid_file
        try:
            with open(self.pid_file, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            message = "pid_file '{}' does not exist. Daemon not running?\n"
            stderr.write(message.format(self.pid_file))
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if str(err.args).find("No such process") > 0:
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
            else:
                print(str(err.args))
                exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        print("Override the run() method in daemon.py to daemonize a process.")
        exit(1)
        """You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart()."""
