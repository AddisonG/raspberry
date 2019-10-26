#!/usr/bin/python3.7

from discord.ext import commands
import sys
import time
import subprocess
import sqlite3
import random

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
    async def add(ctx, song_name):
        """Adds a song to the database."""
        try:
            raspbot.add_song(song_name)
        except Exception as e:
            await ctx.send("Error adding song: " + str(e))
            return
        await ctx.send("Added song '{}'.".format(song_name))

    @bot.command()
    async def remove(ctx, song_name):
        """Removes a song from the database."""
        try:
            raspbot.remove_song(song_name)
        except Exception as e:
            await ctx.send("Error removing song: " + str(e))
            return
        await ctx.send("Removed song '{}'.".format(song_name))

    @bot.command()
    async def delete(ctx):
        raspbot.remove(ctx)

    @bot.command()
    async def list(ctx):
        """Lists all the songs in the database."""
        try:
            await ctx.send(raspbot.list_songs())
        except Exception as e:
            await ctx.send("Error listing songs: " + str(e))
            return

    @bot.command()
    async def random(ctx):
        """Randomly selects a song from the database."""
        try:
            await ctx.send(raspbot.random_song())
        except Exception as e:
            await ctx.send("Error getting random song: " + str(e))
            return

    ############################################################################
    # HELPER METHODS
    ############################################################################

    @staticmethod
    def add_song(name):
        with sqlite3.connect("raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""INSERT INTO songs (name) VALUES (?)""", [name])
            except Exception as e:
                db.rollback()
                raise e

    @staticmethod
    def remove_song(name):
        with sqlite3.connect("raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""DELETE FROM songs WHERE name = ?""", [name])
            except Exception as e:
                db.rollback()
                raise e

    @staticmethod
    def list_songs():
        rows = None
        with sqlite3.connect("raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""SELECT name FROM songs""")
                rows = cur.fetchall()
            except Exception as e:
                db.rollback()
                raise e
        table = ""
        for row in rows:
            table += row[0] + "\n"
        return table if table else "No songs yet."

    @staticmethod
    def random_song():
        with sqlite3.connect("raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""SELECT name FROM songs""")
                rows = cur.fetchall()
            except Exception as e:
                db.rollback()
                raise e
        return rows[random.randrange(len(rows))][0] if rows else "No songs yet."

    @staticmethod
    def setup(self):
        """CREATE TABLE songs (name TEXT(100) PRIMARY KEY);"""
        pass

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
