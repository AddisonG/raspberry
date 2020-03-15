#!/usr/bin/env python3

"""
Generic linux daemon base class for python 3.
Based on https://gist.github.com/andreif/cbb71b0498589dac93cb
"""

from sys import stdin, stdout, stderr
import os
import time
import atexit
import signal
import logging

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
        self.name = name
        self.pid_file = "/run/user/{}/{}/pid".format(str(os.getuid()), name)

        # Set up logging
        log_format = "%(asctime)s [%(levelname)s] - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        logging.basicConfig(
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

        # write pid_file
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
            message = "pid_file '%s' already exists (pid %s). Daemon already running?\n"
            logging.error(message, self.pid_file, pid)
            exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def daemon_stop(self):
        """
        Stop the daemon.
        """

        # Get the pid from the pid_file
        try:
            with open(self.pid_file, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            message = "pid_file '%s' does not exist. Daemon not running?\n"
            logging.error(message, self.pid_file)
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

    def daemon_enable(self):
        """
        Enable this daemon to run as a service.
        """

        filename = self.name + ".service"
        service_file = """\
[Unit]
Description={service_name}
StartLimitIntervalSec=0

[Service]
User=pi
Type=forking
PIDFile=/run/user/1000/{service_name}/pid
RestartSec=60
Restart=always
ExecStart={cwd}/{service_name}.py start
ExecStop={cwd}/{service_name}.py stop
ExecReload={cwd}/{service_name}.py restart

[Install]
WantedBy=multi-user.target
"""
        try:
            fd = open(filename, "w+")
            logging.debug("Writing file '%s'.", filename)
            fd.write(service_file.format(service_name=self.name, cwd=os.getcwd()))
            os.chmod(filename, 0o644)
            logging.debug("Linking file '%s'.", filename)
            os.symlink("{}/{}".format(os.getcwd(), filename), "/etc/systemd/system/" + filename)
        except FileExistsError as e:
            logging.info("The service is already enabled.")
            exit(REDUNDANT_COMMAND)
        except PermissionError as e:
            logging.warn("Root permissions are required to enable a service.")
            exit(PERMISSION_DENIED)
        except Exception as e:
            logging.error(e)
            exit(UNKNOWN_ERROR)
        return
        # ALSO NEED TO RUN: sudo systemctl enable raspbot
        # OUTPUT:
        # Created symlink /etc/systemd/system/multi-user.target.wants/raspbot.service → /home/pi/projects/discord/raspbot/raspbot.service.

    def daemon_disable(self):
        """Disable this daemon from running as a service."""
        filename = self.name + ".service"
        try:
            logging.debug("Removing systemd service file: '%s'.", filename)
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

    def daemon_restart(self):
        """Restart the daemon."""
        self.daemon_stop()
        self.daemon_start()

    def run(self):
        print("Override the run() method in daemon.py to daemonize a process.")
        exit(1)
        """You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by
        daemon_start() or daemon_restart()."""
