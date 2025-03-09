import logging
import os

from colorama import Fore, Style, init
from datetime import datetime

if os.name == "nt": init(autoreset=True, convert=True, strip=False)
elif os.name == "posix": init(autoreset=True, convert=False)
else: init(autoreset=True)


class LogFormatter(logging.Formatter):
    level_symbols = {
        logging.DEBUG: "~",
        logging.INFO: "i",
        logging.WARNING: "!",
        logging.ERROR: "-",
        logging.CRITICAL: "X",
    }

    level_colors = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        message = record.getMessage()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbol = self.level_symbols.get(record.levelno, "?")
        color = self.level_colors.get(record.levelno, Fore.WHITE)
        colored_symbol = f"{color}{symbol}{Fore.LIGHTBLACK_EX}"
        colored_name = f"{Fore.LIGHTMAGENTA_EX}{record.name}{Fore.LIGHTBLACK_EX}"
        formatted_message = (
            f"{Fore.LIGHTBLACK_EX}[{colored_symbol}] "
            f"[{timestamp}] "
            f"[{colored_name}] "
            f"[Line {Fore.LIGHTCYAN_EX}{record.lineno}{Fore.LIGHTBLACK_EX}] "
            f"{message}{Style.RESET_ALL}"
        )
        return formatted_message


def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        logger.handlers = []
    handler = logging.StreamHandler()
    handler.setFormatter(LogFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger