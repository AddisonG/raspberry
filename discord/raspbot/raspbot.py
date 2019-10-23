#!/usr/bin/python3.7

from discord.ext import commands
import sys
import time
import subprocess

sys.path.append('/home/pi/projects/daemonizer')
from daemon import daemon


class raspbot(daemon):
    """
    This bot encapsulates miscellaneous and half-baked functionality. I expect
    that many partially developed features will live here for long periods of
    time.
    """

    start_time = time.time()
    TOKEN = 'NjM2NTQ4NzQ5OTIwODI5NDUw.XbBQdA.egeyn13aaU7slBz9339fKivQpUs'
    bot = commands.Bot(command_prefix="?",
        description="Generic bot for misc reporting and testing.")

    @bot.event
    async def on_ready():
        bot = raspbot.bot
        print('Logged in as:')
        print(bot.user.name + " (" + str(bot.user.id) + ")")
        print('-------------')

        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send("Raspbot ready!")
                    break

    @bot.command()
    async def uptime(ctx):
        """Prints the uptime of the server and this service."""
        sys_uptime = subprocess.check_output('uptime -p', shell=True).rstrip()
        srv_uptime = time.time() - raspbot.start_time
        await ctx.send("System Uptime: {}\nService Uptime: {} seconds"
            .format(sys_uptime, srv_uptime))

    def run(self):
        """ This overrides the daemon run method."""
        raspbot.bot.run(raspbot.TOKEN)
        print("Raspbot shutting down.")


# ============================================================================
# Actually run the bot
# ============================================================================

instance = raspbot("raspbot")

if len(sys.argv) == 1:
    print("Usage: {} [start|stop|restart]".format(sys.argv[0]))
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
    print("Usage: {} [start|stop|restart]".format(sys.argv[0]))
    sys.exit(1)
