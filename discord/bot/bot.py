#!/usr/bin/python3

import asyncio
import discord
import json
import logging
import re
from datetime import datetime
from signal import SIGINT, SIGTERM
from command import Command

from daemonizer.daemon import Daemon

class Bot(object):
    def __init__(self, loop, log):
        with open("conf.json", "r") as f:
            self.conf = json.loads(f.read())

        self.loop = loop
        self.log = log

        # Main parts of the bot
        self.client = discord.Client(loop=loop)

        # Websocket handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        # Store commands
        self.commands = dict()
        self.add_command("stats", self._stats, self.log)
        self.add_command("help", self._help, self.log)
        self.add_command("info", self._info, self.log)
        self.add_command("source", self._source, self.log)

        self._start_time = datetime.now()

    def add_command(self, *args, **kwargs):
        cmd = Command(*args, **kwargs)
        self.commands[cmd.name] = cmd
        self.log.info("Added command %s", cmd)

    def remove_command(self, name):
        try:
            del self.commands[name]
        except KeyError:
            self.log.error("No such command: %s", name)

    async def start(self):
        await self.client.login(self.conf["token"])

        try:
            await self.client.connect()
        except discord.ClientException as exc:
            error = "Something broke, I'm out!\n"
            error += "```{}```".format(str(exc))
            self.log.error(error)
            await self.client.send(
                discord.User(id=self.conf["admin_id"]),
                error
            )
            self.stop_signal()

    async def stop(self):
        await self.client.logout()

    def stop_signal(self):
        self.log.info("Closing")
        f = asyncio.ensure_future(self.stop())

        def end(res):
            self.log.info("Ending loop")
            self.loop.call_soon_threadsafe(self.loop.stop)

        f.add_done_callback(end)

    # Websocket handlers

    async def on_ready(self):
        self.log.info("READY")
        print("READY")
        pass

    async def on_message(self, message):
        # If invite in private message, join server
        if self.conf["scrap_invites"]:
            if message.channel.is_private:
                match = re.match(
                    r"(?:https?\:\/\/)?discord\.gg\/(.+)",
                    message.content)
                if match and match.group(1):
                    await self.client.accept_invite(match.group(1))
                    self.log.info("Joined server, invite %s", match.group(1))
                    await message.author.send("Joined it, thanks :)")
                    return

        data = message.content.split(" ")
        cmd = self.commands.get(data[0])
        if not cmd:
            self.log.debug("%s not a command", data[0])
            return
        elif cmd.admin and message.author.id != self.conf["admin_id"]:
            self.log.warning("cmd %s requires admin", cmd)
            return

        # Go on.
        self.log.info("Found command %s, calling it", cmd)
        await cmd.call(message)

    # Commands

    async def _load_data(self):
        """
        (Re)load the data from various sources. This involves loading config
        from files, and retrieving data from online sources.
        """
        pass

    async def _help(self, message):
        """Print the help message"""
        msg = "Commands:"
        for command in self.commands.values():
            if command.admin:
                continue
            if command.help:
                msg += "{} : {}\n".format(command.name, command.help)
            else:
                msg += "{}\n".format(command.name)

        await message.channel.send(msg)

    async def _info(self, message):
        """Print your id"""
        await message.channel.send("Your id: `%s`" % message.author.id)

    async def _source(self, message):
        """Show the bot"s github link"""
        await message.channel.send("Original: https://github.com/gdraynz/discord-bot")
        await message.channel.send("Modified: https://github.com/AddisonG/raspberry")

    async def _stats(self, message):
        """Show the bot"s general stats"""
        users = 0
        for s in self.client.servers:
            users += len(s.members)

        msg = "`Stats:\n"
        msg += "Admin  : <@{}>\n".format(self.conf["admin_id"])
        msg += "Uptime : {}`\n".format(get_time_string((datetime.now() - self._start_time).total_seconds()))
        await message.channel.send(msg)

class BotRunner(object):
    def run(self, bot_class):
        loop = asyncio.get_event_loop()
        log = logging.getLogger(__name__)

        bot = bot_class(loop, log)

        loop.add_signal_handler(SIGINT, bot.stop_signal)
        loop.add_signal_handler(SIGTERM, bot.stop_signal)

        asyncio.ensure_future(bot.start())
        loop.run_forever()
        loop.close()
