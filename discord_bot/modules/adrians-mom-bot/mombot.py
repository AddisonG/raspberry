#!/usr/bin/env python3

import sys
import os

import openai
import logging

from discord import Message
from discord_bot.base.bot import Bot
from local_utilities.logging_utils import begin_logging_to_stdout


OPENAPI_KEY_FILE = "openai-api.key"

class MomBot(Bot):
    """
    This bot simplifies medical text for Adrians Mom.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not os.path.isfile(OPENAPI_KEY_FILE):
            # No openapi key - we need one to function
            with open(OPENAPI_KEY_FILE, "w") as key_file:
                error_msg = f"You need an OpenAI API key. Please fill in the one just created. See {OPENAPI_KEY_FILE}."
                print(error_msg)
                logging.error(error_msg)
                key_file.write("sk-svcacct-qwertyuiop-key-here")


        with open(OPENAPI_KEY_FILE) as key_file:
            key = key_file.readline().strip()
            openai.api_key = key

    async def on_message(self, message: Message):
        """
        We want to respond to ALL messages - not just certain commands
        Thus, we're overwriting the default on_message behaviour.
        """

        if message.author.bot:
            # Don't respond to bots - prevent infinite loops
            return

        await self.help_mom(message)

    async def help_mom(self, message: Message):
        async with message.channel.typing():
            response_message = await self.openapi_response(message)

        # Split the response into chunks of 2000 characters or less, prioritizing spaces or newlines
        chunk_size = 2000
        chunks = []

        while len(response_message) > chunk_size:
            # Find the last space or newline within the chunk size limit
            split_point = max(response_message.rfind(' ', 0, chunk_size), response_message.rfind('\n', 0, chunk_size))

            # If no space or newline found, just split at chunk_size
            if split_point == -1:
                split_point = chunk_size

            chunks.append(response_message[:split_point])
            response_message = response_message[split_point:].lstrip()

        # Add the remaining part (if any)
        if response_message:
            chunks.append(response_message)

        # Send each chunk
        for chunk in chunks:
            await message.channel.send(chunk)


    async def openapi_response(self, message: Message):
        prep = (
            "I am a carer for persons with disabilities.\n"
            "Please summarise my following message in professional language\n"
            "Include these sections, and elaborate/extrapolate where needed:\n"
            "# Summary of work performed\n"
            "# Benefits provided\n"
            "# Justificaton for actions\n"
            "\n"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prep + message.content}
            ],
        )

        return response.choices[0].message['content']

    async def on_ready(self):
        await super().on_ready()
        greeting = "MomBot ready!"

        # Say hello when you come online
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(greeting)


# ============================================================================
# Actually run the bot
# ============================================================================

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) == 2 else None
    instance = MomBot(name="mombot")

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
        begin_logging_to_stdout()
        instance.run()
    else:
        print("Usage: {} [start|stop|restart|enable|disable]".format(sys.argv[0]))
        sys.exit(1)
