#!/usr/bin/python3.7

from discord.ext import commands
import socket
import requests
import sys

sys.path.append('/home/pi/projects/daemonizer')
from daemon import daemon


class ip_bot(daemon):
    """
    This bot reports the Local and Global IP Address of the server it's
    running on to a discord channel.
    """

    TOKEN = 'NjMxNDYyNjAwMjE0ODM5Mjk3.XZ7MFQ.I0oMSIaCoVm6-8zjG7D27p120qM'
    bot = commands.Bot(command_prefix="?", description="Reports the IP Address of itself.")

    @bot.event
    async def on_ready():
        bot = ip_bot.bot
        print('Logged in as:')
        print(bot.user.name + " (" + str(bot.user.id) + ")")
        print('-------------')

        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(ip_bot.get_ip())
                    break

    @bot.command()
    async def ip(ctx):
        """Prints the bots IP address."""
        await ctx.send(ip_bot.get_ip())

    @staticmethod
    def get_ip():
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        global_ip = requests.get("https://icanhazip.com/").text
        return "Local IP Address: " + local_ip + "\n" + "Global IP Address: " + global_ip

    def run(self):
        """ This overrides the daemon run method."""
        ip_bot.bot.run(ip_bot.TOKEN)
        print("Bot shutdown.")


# ============================================================================
# Actually run the bot
# ============================================================================

instance = ip_bot("ip-reporter")

if len(sys.argv) == 1:
    print("Usage: " + sys.argv[0] + " [start|stop|restart]")
    sys.exit(1)

command = sys.argv[1]
if command == "start":
    instance.start()
elif command == "stop":
    instance.stop()
elif command == "restart":
    instance.restart()
elif command == "debug":
    # Run without daemonizing
    instance.run()
else:
    print("Usage: " + sys.argv[0] + " [start|stop|restart]")
    sys.exit(1)
