#!/usr/bin/env python3

"""
Generic linux daemon base class for python 3.
Based on https://gist.github.com/andreif/cbb71b0498589dac93cb
"""

from sys import stdin, stdout, stderr
import os
import sys
import time
import atexit
import signal
import logging
import setproctitle

from local_utilities.logging_utils import begin_logging_to_stdout

# Normal exit codes
SUCCESS = 0
REDUNDANT_COMMAND = 1
PERMISSION_DENIED = 2

# Fatal errors
FORK_ERROR = 98
UNKNOWN_ERROR = 99


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the daemon class and override the run() method.
    """

    def __init__(self, name: str):
        uid = os.getuid()
        self.name = name
        self.pid_file = f"/run/user/{uid}/{name}/pid"

        # Change the process title
        setproctitle.setproctitle(name)

        # Set up logging
        log_format = "%(asctime)s [%(levelname)s] - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        logging.basicConfig(
            filename=f"{sys.path[0]}/{name}.log",
            filemode="a",
            level=logging.INFO,
            format=log_format,
            datefmt=date_format
        )

    def daemonize(self):
        """
        Daemonize class. UNIX double fork mechanism.
        """

        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                exit(0)
        except OSError as err:
            logging.error("Fork #1 failed: '{}'", err)
            exit(FORK_ERROR)

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit second parent
                exit(0)
        except OSError as err:
            logging.error("Fork #2 failed: '{}'", err)
            exit(FORK_ERROR)

        # Redirect standard file descriptors
        si = open(os.devnull, "r")
        so = open(os.devnull, "a+")
        se = open(os.devnull, "a+")

        stdout.flush()
        stderr.flush()
        os.dup2(si.fileno(), stdin.fileno())
        os.dup2(so.fileno(), stdout.fileno())
        os.dup2(se.fileno(), stderr.fileno())

        # Create pid_file
        os.makedirs(os.path.dirname(self.pid_file), exist_ok=True, mode=0o755)
        atexit.register(self._delpid)
        with open(self.pid_file, "w+") as f:
            f.write(str(os.getpid()) + "\n")

    def _delpid(self):
        os.remove(self.pid_file)

    def daemon_start(self):
        """
        Start the daemon.
        """
        # Check for a pid_file to see if the daemon is already running
        try:
            with open(self.pid_file, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = f"pid_file '{self.pid_file}' already exists (pid {str(pid)}). Daemon already running?"
            logging.error(message)
            exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def daemon_stop(self):
        """
        Stop the daemon. Returns exit status.
        """
        # Get the pid from the pid_file
        try:
            with open(self.pid_file, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            message = f"pid_file '{self.pid_file}' does not exist. Daemon not running?"
            logging.error(message)
            print(message)
            return 1

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
                return 1
        return 0

    def daemon_enable(self):
        """
        Enable this daemon to run as a service.
        """
        begin_logging_to_stdout()

        filename = self.name + ".service"
        file_contents = """\
[Unit]
Description={service_name}
StartLimitIntervalSec=0

[Service]
User=pi
Type=forking
PIDFile=/run/user/1000/{service_name}/pid
RestartSec=60
Restart=always
ExecStart={dir}/{service_name}.py start
ExecStop={dir}/{service_name}.py stop
ExecReload={dir}/{service_name}.py restart

[Install]
WantedBy=multi-user.target
"""
        try:
            fd = open(filename, "w+")
            logging.debug(f"Writing file '{sys.path[0]}/{filename}'.")
            fd.write(file_contents.format(service_name=self.name, dir=sys.path[0]))
            os.chmod(filename, 0o644)
            logging.debug("Creating link in /etc/systemd/system/.")
            os.symlink("{}/{}".format(sys.path[0], filename), "/etc/systemd/system/" + filename)
        except FileExistsError as e:
            logging.info("The service is already enabled.")
            exit(REDUNDANT_COMMAND)
        except PermissionError as e:
            logging.warn("Root permissions are required to enable a service.")
            exit(PERMISSION_DENIED)
        except Exception as e:
            logging.error(e)
            exit(UNKNOWN_ERROR)
        logging.info(f"Remember to run 'sudo systemctl enable {self.name}'.")
        # ALSO NEED TO RUN: sudo systemctl enable <service_name>
        # OUTPUT:
        # Created symlink /etc/systemd/system/multi-user.target.wants/my.service → /home/me/my.service.

    def daemon_disable(self):
        """
        Disable this daemon from running as a service.
        """
        begin_logging_to_stdout()
        filename = self.name + ".service"
        try:
            logging.debug(f"Removing systemd service file: '{filename}'.")
            os.remove("/etc/systemd/system/" + filename)
        except FileNotFoundError as e:
            logging.warn("The service is already disabled.")
            exit(REDUNDANT_COMMAND)
        except PermissionError as e:
            logging.warn("Root permissions are required to disable a service.")
            exit(PERMISSION_DENIED)
        except Exception as e:
            logging.error(e)
            exit(UNKNOWN_ERROR)
        exit()

    def daemon_restart(self):
        """
        Restart the daemon.
        """
        self.daemon_stop()
        self.daemon_start()

    def run(self):
        """
        Override this method when subclassing `Daemon`.

        It will be called after the process has been daemonized by
        `daemon_start()` or `daemon_restart()`.
        """
        print("Override the run() method to daemonize a process.")
        exit(1)
