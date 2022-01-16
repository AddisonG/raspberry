#!/usr/bin/env python3

import traceback
import logging
import gspread
import random
import sys
import re

from discord import Message
from oauth2client.service_account import ServiceAccountCredentials
from discord_bot.base.bot import Bot
from local_utilities.string_utils import titlecase
from local_utilities.logging_utils import get_script_path


class SongBot(Bot):
    """
    This bot comes up with songs for Rowan to sing.

    TODO - make the bot suggest valid tags?
    TODO - add, remove, tag songs
    TODO - make the bot suggest songs randomly throughout the day?
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_bot_command("random", self.random_song)
        self.add_bot_command("another", self.another_song)
        self.add_bot_command("again", self.another_song)
        self.add_bot_command("list", self.list_songs)
        self.add_bot_command("add", self.add_song)
        self.add_bot_command("delete", self.delete_song)
        self.add_bot_command("tag", self.tag_song)
        self.add_bot_command("reload", self.reload_songs)

    async def random_song(self, message: Message):
        """
        Provides a random song - accepts a source and/or tags as a parameter.
        """
        # Store the message, in case an "another" request is made
        self.last_message = message

        # Filter songs according to arguments
        filtered_songs = self.song_list
        for arg in message.content.split(" ")[1:]:
            arg = arg.lower()
            filtered_songs = [song for song in filtered_songs if arg in (song["tag_1"], song["tag_2"], song["tag_3"]) or arg in song["source"]]

        if not filtered_songs:
            await message.channel.send("No songs found")
            return

        # Compose and send message
        song = filtered_songs[random.randrange(len(filtered_songs))]
        song_message = "'{}' by {}".format(titlecase(song["name"]), titlecase(song["source"]))
        await message.channel.send(song_message)

    async def another_song(self, message: Message):
        """
        Provides another song with the same parameters as the previous request.
        """
        await self.random_song(self.last_message)

    async def list_songs(self, message: Message):
        """
        Lists all the songs available.
        """

        # Use regex to break song list into fragments <2000 in length.
        for songs_fragment in re.findall(r'[\s\S]{1,2000}\n', "\n".join(self.simple_song_list)):
            await message.channel.send(songs_fragment)

        await message.channel.send("===============\nListed {} songs".format(len(self.simple_song_list)))

    async def add_song(self, message: Message):
        """
        Adds a song to the database.
        """
        await message.channel.send("Not yet implemented.")

    async def delete_song(self, message: Message):
        """
        Removes a song from the database.
        """
        await message.channel.send("Not yet implemented.")

    async def tag_song(self, message: Message):
        """
        Tags a song in the database.
        """
        await message.channel.send("Not yet implemented.")

    async def reload_songs(self, message: Message):
        """
        Reloads the song database.
        """
        response = "Reloaded data."
        # Display "Bot is typing a message" while it loads
        async with message.channel.typing():
            try:
                await self.load_songs()
            except Exception as e:
                response = "Failed to reload data. See logs for error."
                logging.error("{}\n{}".format(type(e), str(e)))
        await message.channel.send(response)

    async def load_songs(self):
        """
        (Re)loads the songs.
        This is a back-end function. It has no output. It may throw exceptions.
        """
        gscope = ["https://www.googleapis.com/auth/drive"]
        gcreds = ServiceAccountCredentials.from_json_keyfile_name(get_script_path() + "/credentials.json", gscope)
        gclient = gspread.authorize(gcreds)
        gsheet = gclient.open("Rowan's Songs").get_worksheet(0)
        self.song_list = gsheet.get_all_records()

        # Convert all values to lowercase for searching
        self.song_list = [{k: v.lower() for k, v in song.items()} for song in self.song_list]

        # Simple song list is only used for listing all songs - Titlecase them
        self.simple_song_list = [titlecase(song['name']) for song in self.song_list]

    async def on_ready(self):
        await super().on_ready()
        greeting = "Songbot ready!"
        try:
            await self.load_songs()
        except Exception as e:
            greeting = "Fatal: Could not load songs. See logs for error. Songbot not ready!"
            logging.error("ERR: {}\n{}\n{}".format(type(e), str(e), traceback.format_exc()))
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(greeting)


# ============================================================================
# Actually run the bot
# ============================================================================

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) == 2 else None
    instance = SongBot("songbot")

    if command == "start":
        instance.daemon_start()
    elif command == "stop":
        status = instance.daemon_stop()
        exit(status)
    elif command == "enable":
        instance.daemon_enable()
    elif command == "disable":
        instance.daemon_disable()
    elif command == "restart":
        instance.daemon_restart()
    elif command == "status":
        # TODO
        print("TODO - Not yet implemented")
        pass
    elif command in ("debug", "test"):
        # Run without daemonizing
        instance.run()
    else:
        print("Usage: {} [start|stop|restart|enable|disable]".format(sys.argv[0]))
        sys.exit(1)
