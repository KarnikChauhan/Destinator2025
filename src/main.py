import asyncio # pylint: disable=E0401
import os # pylint: disable=E0401
import platform # pylint: disable=E0401
import signal # pylint: disable=E0401
import sys # pylint: disable=E0401
import traceback # pylint: disable=E0401

import disnake # pylint: disable=E0401
from colorama import Fore # pylint: disable=E0401
from disnake.ext import commands # pylint: disable=E0401

from ext.logger import get_logger # pylint: disable=E0401
from ext.utils import CLI_Parser, Utils # pylint: disable=E0401


class Bot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_cogs()

    def load_cogs(self):
        logger = get_logger(__name__)
        try:
            path = Utils.resolve_path("src/cogs")
            for f in os.listdir(path):
                if f.endswith(".py") and f != "__init__.py":
                    self.load_extension(f"cogs.{f[:-3]}")
                    logger.info(f"Loaded {f[:-3]}")
        except disnake.ext.commands.ExtensionError as e:
            logger.error(f"Failed to load extension {e}")


bot = Bot(
    intents=disnake.Intents.all(),
    default_contexts=disnake.InteractionContextTypes.all(),
    default_install_types=disnake.ApplicationInstallTypes.all(),
    status=disnake.Status.online,
    activity=disnake.CustomActivity(name="Destinator"),
    #test_guilds=[],
)


@bot.event
async def on_ready():
    logger = get_logger(__name__)
    logger.info(
        f"Logged in as {Utils.highlight_text(bot.user.name, Fore.LIGHTBLUE_EX)} (ID: {Utils.highlight_text(bot.user.id, Fore.LIGHTBLUE_EX)})"
    )  # type: ignore


async def shutdown(signal, loop):
    """Graceful shutdown handler"""
    logger.info(f"Received {signal.name}, shutting down...")
    await bot.close()




if __name__ == "__main__":
    logger = get_logger(__name__)
    parser = CLI_Parser.from_sys_args()
    token = parser.get_argument("token")

    if not token:
        logger.error("Bot token not provided. Use --token")
        sys.exit(1)

    logger.info("Bot token found, initializing bot...")

    try:
        loop = asyncio.get_event_loop()
        if platform.system() != "Windows":
            signals = (signal.SIGINT, signal.SIGTERM)
            for s in signals:
                loop.add_signal_handler(
                    s, lambda s=s: asyncio.create_task(shutdown(s, loop))
                )
        else:
            logger.warning(
                "Signal handlers are not supported on Windows. Use Ctrl+C to stop the bot."
            )

        loop.run_until_complete(bot.start(token))
    except disnake.LoginFailure:
        logger.error("Invalid token provided. Please check your token and try again.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
