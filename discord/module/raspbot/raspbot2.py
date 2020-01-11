#!/usr/bin/python3

from discord.bot.bot import Bot, BotRunner

class Raspbot(Bot):
    """
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_command("hello", self._hello, self.log)

    async def _hello(self, message):
        await message.channel.send("Hey")


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-l", "--logfile", action="store_true", help="Log file")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()  # TODO unused

    BotRunner().run(Raspbot)
