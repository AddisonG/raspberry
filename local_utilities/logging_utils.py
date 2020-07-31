#!/usr/bin/env python3

import logging
import sys

def begin_logging_to_stdout():
    """
    Assuming the logger is already configured, this will add a stream that
    will cause the logger to begin also logging to stdout.
    """
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    root.addHandler(handler)
