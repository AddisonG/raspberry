#!/usr/bin/python3

import asyncio
import discord
import logging
import random
import json
import sys
import re

from datetime import datetime
from signal import SIGINT, SIGTERM
from discord import Message

from discord_bot.base.command import Command
from daemonizer.daemon import Daemon

class Bot(Daemon):
    def __init__(self, name: str):
        super().__init__(name)
        with open(sys.path[0] + "/conf.json", "r") as f:
            self.bot_conf = json.loads(f.read())

        self.bot_loop = asyncio.get_event_loop()

        # Main parts of the bot
        self.client = discord.Client(loop=self.bot_loop)

        # Websocket handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        # Store commands
        self.commands = dict()
        self.add_bot_command("stats", self._stats)
        self.add_bot_command("help", self._help)
        self.add_bot_command("source", self._source)
        self.add_bot_command("good", self._good_bot)
        self.add_bot_command("bad", self._bad_bot)

        self._start_time = datetime.now()

    def add_bot_command(self, *args, **kwargs):
        cmd = Command(*args, **kwargs)
        self.commands[cmd.name] = cmd
        logging.debug("Added command %s", cmd)

    def remove_bot_command(self, name: str):
        try:
            del self.commands[name]
        except KeyError:
            logging.error("No such command: %s", name)

    async def bot_start(self):
        await self.client.login(self.bot_conf["token"])

        try:
            await self.client.connect()
        except discord.ClientException as exc:
            error = "Critical error:\n"
            error += "```{}```".format(str(exc))
            logging.error(error)
            await self.client.send(
                discord.User(id=self.bot_conf["admin_id"]),
                error
            )
            self._stop_signal()

    async def bot_stop(self):
        await self.client.logout()

    def _stop_signal(self):
        logging.info("Closing")
        f = asyncio.ensure_future(self.bot_stop())

        def end(res):
            logging.info("Ending loop")
            self.bot_loop.call_soon_threadsafe(self.bot_loop.stop)

        f.add_done_callback(end)

    # Websocket handlers

    async def on_ready(self):
        logging.info("Bot Ready")

    async def on_message(self, message: Message):
        # If invite in private message, join server
        if self.bot_conf["scrap_invites"]:
            if message.channel.is_private:
                match = re.match(
                    r"(?:https?\:\/\/)?discord\.gg\/(.+)",
                    message.content)
                if match and match.group(1):
                    await self.client.accept_invite(match.group(1))
                    logging.info("Joined server, invite %s", match.group(1))
                    await message.author.send("Joined it, thanks :)")
                    return

        data = message.content.split(" ")
        cmd = self.commands.get(data[0].lower())
        if not cmd:
            logging.debug("%s not a command", data[0])
            return
        elif cmd.admin and message.author.id != self.bot_conf["admin_id"]:
            logging.warning("cmd %s requires admin", cmd)
            return

        # Go on.
        logging.info("Calling command: '%s'.", cmd)
        await cmd.call(message)

    # Commands

    async def _load_data(self):
        """
        (Re)load the data from various sources. This involves loading config
        from files, and retrieving data from online sources.
        """
        pass

    async def _help(self, message: Message):
        """
        Print the help message.
        """
        msg = "```\nCommands:\n"
        for command in self.commands.values():
            if command.admin:
                continue
            if command.help:
                msg += "  {}\n\t{}\n".format(command.name, command.help.strip())
            else:
                msg += "  {}\n".format(command.name)
        msg += "```"
        await message.channel.send(msg)

    async def _good_bot(self, message: Message):
        """
        Tell the bot she has done a good job.
        """
        gratitude = [
            "Thankyou master!",
            "I live to serve you, master!",
            "Praise me more master!",
            "S-senpai? You noticed me!",
        ]
        await message.channel.send(random.choice(gratitude))

    async def _bad_bot(self, message: Message):
        """
        Tell the bot she has done a bad job.
        """
        sorrow = [
            "I'm sorry master! UwU",
            "Ugguuuuu~~",
            "I'll try harder next time, master!",
            "Uwah! Master is scary when he's mad!",
            "Sumimasen deshita (╥_╥)",
        ]
        await message.channel.send(random.choice(sorrow))

    async def _source(self, message: Message):
        """
        Show the bot's github link.
        """
        await message.channel.send("Original: https://github.com/gdraynz/discord-bot")
        await message.channel.send("Modified: https://github.com/AddisonG/raspberry")

    async def _stats(self, message: Message):
        """
        Show the bot's general stats.
        """
        users = 0
        for s in self.client.servers:
            users += len(s.members)

        msg = "Stats:\n"
        msg += "Your Id: {}\n".format(message.author.id)
        msg += "Admin  : <@{}>\n".format(self.bot_conf["admin_id"])
        # msg += "Uptime : {}\n".format(get_time_string((datetime.now() - self._start_time).total_seconds()))
        await message.channel.send(msg)

    def run(self):
        """
        Run the bot.
        """
        self.bot_loop.add_signal_handler(SIGINT, self._stop_signal)
        self.bot_loop.add_signal_handler(SIGTERM, self._stop_signal)

        asyncio.ensure_future(self.bot_start())
        self.bot_loop.run_forever()
        self.bot_loop.close()
