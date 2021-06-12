#!/usr/bin/env python3

import logging
import sys
import os

LOG_FORMAT = "%(asctime)s [%(levelname)s] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def simple_logging(filename, level=logging.INFO, stdout=False):
    """
    Set up a simple logging config that logs to a file.
    """
    logging.basicConfig(
        filename=f"{get_script_path()}/{filename}.log",
        filemode="a",
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )
    if stdout:
        begin_logging_to_stdout()


def begin_logging_to_stdout():
    """
    Assuming the logger is already configured, this will add a stream that
    will cause the logger to begin also logging to stdout.
    """
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    root.addHandler(handler)


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))
