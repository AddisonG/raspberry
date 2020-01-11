#!/usr/bin/python3.7

import socket
import requests
import sys

from discord.ext import commands

from daemonizer.daemon import Daemon


class IpBot(Daemon):
    """
    This bot reports the Local and Global IP Address of the server it's
    running on to a discord channel.
    """

    TOKEN = 'NjMxNDYyNjAwMjE0ODM5Mjk3.XZ7MFQ.I0oMSIaCoVm6-8zjG7D27p120qM'
    bot = commands.Bot(command_prefix="?", description="Reports the IP Address of itself.")

    @bot.event
    async def on_ready():
        bot = IpBot.bot
        print('Logged in as:')
        print(bot.user.name + " (" + str(bot.user.id) + ")")
        print('-------------')

        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(IpBot.get_ip())
                    break

    @bot.command(name='ip')
    async def ip(ctx):
        """Prints the bots IP address."""
        await ctx.send(IpBot.get_ip())

    @staticmethod
    def get_ip():
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        global_ip = requests.get("https://icanhazip.com/").text
        return "Local IP Address: " + local_ip + "\n" + "Global IP Address: " + global_ip

    def run(self):
        """ This overrides the daemon run method."""
        IpBot.bot.run(IpBot.TOKEN)
        print("Bot shutdown.")


# ============================================================================
# Actually run the bot
# ============================================================================

instance = IpBot("ip-reporter")
command = sys.argv[1] if len(sys.argv) == 2 else None

if command == "start":
    instance.daemon_start()
elif command == "stop":
    instance.daemon_stop()
elif command == "enable":
    instance.daemon_enable()
elif command == "disable":
    instance.daemon_disable()
elif command == "restart":
    instance.daemon_restart()
elif command in ("debug", "test"):
    # Run without daemonizing
    instance.run()
else:
    print("Usage: {} [start|stop|restart|enable|disable]".format(sys.argv[0]))
    sys.exit(1)
