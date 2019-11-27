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
    bot = commands.Bot(
        command_prefix="",
        description="Generic bot for misc reporting and testing."
    )

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
    async def add(ctx, *, song_name):
        """Adds a song to the database."""
        try:
            raspbot.add_song(song_name)
        except Exception as e:
            await ctx.send("Error adding song: " + str(e))
            return
        await ctx.send("Added song '{}'.".format(song_name))

    @bot.command(name='remove')
    async def remove(ctx, *, song_name):
        """Removes a song from the database."""
        try:
            raspbot.remove_song(song_name)
        except Exception as e:
            await ctx.send("Error removing song: " + str(e))
            return
        await ctx.send("Removed song '{}'.".format(song_name))

    @bot.command(name='delete')
    async def delete(ctx):
        """Removes a song from the database."""
        await raspbot.remove(ctx)

    @bot.command(name='list')
    async def list_all(ctx):
        """Lists all the songs in the database."""
        try:
            await ctx.send(raspbot.list_songs())
        except Exception as e:
            await ctx.send("Error listing songs: " + str(e))
            return

    @bot.command()
    async def random(ctx, *tags):
        """Randomly selects a song from the database, with the given tag.
        Please only supply one tag - only the first is read."""
        try:
            if tags:
                await ctx.send(raspbot.random_song(tags[0]))
            else:
                await ctx.send(raspbot.random_song())
        except Exception as e:
            await ctx.send("Error getting random song: " + str(e))
            return

    ############################################################################
    # HELPER METHODS
    ############################################################################

    @staticmethod
    def add_song(song):
        # This method is nearly my username - addisong!
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""INSERT INTO songs (song) VALUES (?)""", [song])
            except Exception as e:
                db.rollback()
                raise e

    @staticmethod
    def remove_song(song):
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""DELETE FROM songs WHERE song = ?""", [song])
            except Exception as e:
                db.rollback()
                raise e

    @staticmethod
    def list_songs():
        songs = None
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""SELECT song FROM songs""")
                songs = cur.fetchall()
                # cur.execute("""SELECT (song, tag) FROM song_tag_map""")
                # song_tag_map = cur.fetchall()
            except Exception as e:
                db.rollback()
                raise e
        table = ""
        for song in songs:
            # TODO FIXME
            table += song[0] + "\n"
        return table if table else "No songs yet."

    @staticmethod
    def list_tags():
        tags = None
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()
                cur.execute("""SELECT tag FROM tags""")
                tags = cur.fetchall()
            except Exception as e:
                db.rollback()
                raise e
        table = ""
        for tag in tags:
            table += tag[0] + "\n"
        return table if table else "No tags yet."

    @staticmethod
    def random_song(tag=None):
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()
                if tag is not None:
                    cur.execute("""SELECT song FROM song_tag_map where tag = ?""", [tag])
                else:
                    cur.execute("""SELECT song FROM songs""")
                rows = cur.fetchall()
            except Exception as e:
                db.rollback()
                raise e
        return rows[random.randrange(len(rows))][0] if rows else "No songs yet."

    @staticmethod
    def setup(self):
        with sqlite3.connect("/home/pi/projects/discord/raspbot/raspbot.db") as db:
            try:
                cur = db.cursor()

                cur.execute("""
                    PRAGMA foreign_keys = 1;
                """)

                cur.execute("""
                    CREATE TABLE songs (
                        song TEXT(100) NOT NULL PRIMARY KEY
                    );
                """)

                cur.execute("""
                    CREATE TABLE tags (
                        tag TEXT(100) NOT NULL PRIMARY KEY
                    );
                """)

                cur.execute("""
                    CREATE TABLE song_tag_map (
                        song TEXT(100) NOT NULL,
                        tag TEXT(100),
                        PRIMARY KEY (song, tag),
                        FOREIGN KEY (song) REFERENCES songs(song) ON DELETE CASCADE,
                        FOREIGN KEY (tag) REFERENCES tags(tag) ON DELETE CASCADE
                    );
                """)
            except Exception as e:
                db.rollback()
                raise e
        return "Setup complete."

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
elif command == "enable":
    instance.enable()
elif command == "disable":
    instance.disable()
elif command == "restart":
    instance.restart()
elif command in ("debug", "test"):
    # Run without daemonizing
    instance.run()
else:
    print("Usage: {} [start|stop|restart|enable|disable]".format(sys.argv[0]))
    sys.exit(1)
