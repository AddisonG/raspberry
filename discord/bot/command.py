#!/usr/bin/python3

import asyncio
import re

class Command(object):
    def __init__(self, name, handler, log, admin=False, regexp=r""):
        self.name = name
        self.admin = admin
        self.log = log
        self.regexp = re.compile(regexp) if regexp else None
        if not asyncio.iscoroutinefunction(handler):
            self.log.warning("A command must be a coroutine")
            handler = asyncio.coroutine(handler)
        self.handler = handler
        self.help = handler.__doc__ or ""

    def __str__(self):
        return "<Command {}: admin={}, regexp={}>".format(
            self.name, self.admin, bool(self.regexp))

    async def call(self, message):
        data = " ".join(message.content.split(" ")[2:])
        if self.regexp:
            self.log.info("Regexp required for command %s", self)
            match = self.regexp.match(data)
            if not match:
                self.log.error("Regexp failed")
                return
            self.log.debug("kwargs for cmd: %s", match.groupdict())
            self.log.info("Calling handler with kwargs for command %s", self)
            await self.handler(message, **match.groupdict())
        else:
            self.log.info("Calling handler for command %s", self)
            await self.handler(message)
