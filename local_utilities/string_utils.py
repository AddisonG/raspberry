#!/usr/bin/env python3

import re

def titlecase(s):
    return re.sub(r"\w[\w']*", lambda m: m.group(0).capitalize(), s)
