#!/usr/bin/python3

import asyncio
import logging
import re

class Command(object):
    def __init__(self, name: str, handler, admin=False, regexp=r""):
        self.name = name
        self.admin = admin
        self.regexp = re.compile(regexp) if regexp else None
        if not asyncio.iscoroutinefunction(handler):
            logging.warning("A command must be a coroutine")
            handler = asyncio.coroutine(handler)
        self.handler = handler
        self.help = handler.__doc__ or ""

    def __str__(self):
        return self.name

    async def call(self, message):
        data = " ".join(message.content.split(" ")[2:])
        if self.regexp:
            logging.info("Regexp required for command %s", self)
            match = self.regexp.match(data)
            if not match:
                logging.error("Regexp failed")
                return
            logging.debug("kwargs for cmd: %s", match.groupdict())
            logging.info("Calling handler with kwargs for command %s", self)
            await self.handler(message, **match.groupdict())
        else:
            logging.info("Calling handler for command %s", self)
            await self.handler(message)
