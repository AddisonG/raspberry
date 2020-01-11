#!/usr/bin/python3

import gspread
import random
import sys

from discord import Message
from oauth2client.service_account import ServiceAccountCredentials
from discord_bot.base.bot import Bot
from utilities.util import titlecase


class SongBot(Bot):
    """
    This bot comes up with songs for Rowan to sing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_command("random", self._random_song)
        self.add_command("list", self._list_songs)
        self.add_command("add", self._add_song)
        self.add_command("delete", self._delete_song)
        self.add_command("tag", self._tag_song)
        self.add_command("reload", self._reload)


    async def _random_song(self, message: Message):
        args = message.content.split(" ")[1:]

        # Filter songs according to arguments
        filtered_songs = self.song_list
        for arg in args:
            arg = arg.lower()
            filtered_songs = [song for song in filtered_songs if arg in (song["source"], song["tag_1"], song["tag_2"], song["tag_3"])]

        if not filtered_songs:
            await message.channel.send("No songs found")
            return

        # Compose and send message
        song = filtered_songs[random.randrange(len(filtered_songs))]
        song_message = "'{}' by {}".format(titlecase(song["name"]), titlecase(song["source"]))
        await message.channel.send(song_message)

    async def _list_songs(self, message: Message):
        for song in self.song_list:
            song_list_message += song["name"] + "\n"
        await message.channel.send(song_list_message)

    async def _add_song(self, message: Message):
        pass

    async def _delete_song(self, message: Message):
        pass

    async def _tag_song(self, message: Message):
        pass

    async def _reload(self, message: Message):
        async with message.channel.typing():
            await self._load_songs()
        await message.channel.send("Reloaded!")

    async def _load_songs(self):
        gscope = ["https://www.googleapis.com/auth/drive"]
        gcreds = ServiceAccountCredentials.from_json_keyfile_name(sys.path[0] + "/credentials.json", gscope)
        gclient = gspread.authorize(gcreds)
        gsheet = gclient.open("Rowan's Songs").get_worksheet(0)
        self.song_list = gsheet.get_all_records()

        # Convert all values to lowercase
        self.song_list = [{k: v.lower() for k, v in song.items()} for song in self.song_list]

    async def on_ready(self):
        await super().on_ready()
        await self._load_songs()
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send("Songbot ready!")
                    break



# ============================================================================
# Actually run the bot
# ============================================================================

instance = SongBot("songbot")
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
