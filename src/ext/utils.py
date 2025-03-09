import functools
import os
import sys
from pathlib import Path
from typing import Any, Dict

import colorama


class CLI_Parser:
    """
    A custom parser class to handle CLI arguments
    """

    def __init__(self, **kwargs):
        self.args = {}
        # Initialize with any provided kwargs
        for key, value in kwargs.items():
            self.args[key] = value

    def parse_sys_args(self) -> None:
        """
        Parse arguments from sys.argv
        Handles formats like:
        --key=value
        --key value
        --flag (boolean flag)
        """
        i = 1  # Skip program name
        while i < len(sys.argv):
            arg = sys.argv[i]

            # Handle --key=value format
            if arg.startswith("--") and "=" in arg:
                key, value = arg[2:].split("=", 1)
                self.add_arguments(key, value)
                i += 1

            # Handle --key value format
            elif (
                arg.startswith("--")
                and i + 1 < len(sys.argv)
                and not sys.argv[i + 1].startswith("--")
            ):
                key = arg[2:]
                value = sys.argv[i + 1]
                self.add_arguments(key, value)
                i += 2

            # Handle --flag format (boolean flags)
            elif arg.startswith("--"):
                key = arg[2:]
                self.add_arguments(key, True)
                i += 1

            else:
                # Positional argument - can be extended as needed
                i += 1

    @classmethod
    def from_sys_args(cls) -> "CLI_Parser":
        """
        Factory method to create a parser and immediately parse sys.argv

        Returns:
            CLI_Parser with arguments from command line
        """
        parser = cls()
        parser.parse_sys_args()
        return parser

    def add_arguments(self, param: str, value: Any) -> None:
        """
        Add a new argument to the parser

        Args:
            param: The parameter name
            value: The parameter value
        """
        self.args[param] = value

    def get_argument(self, param: str, default: Any = None) -> Any:
        """
        Get an argument value

        Args:
            param: The parameter name
            default: Default value if parameter doesn't exist

        Returns:
            The parameter value or default if not found
        """
        return self.args.get(param, default)

    def has_argument(self, param: str) -> bool:
        """
        Check if an argument exists

        Args:
            param: The parameter name

        Returns:
            True if parameter exists, False otherwise
        """
        return param in self.args

    def get_all_arguments(self) -> Dict[str, Any]:
        """
        Get all arguments

        Returns:
            Dictionary containing all arguments
        """
        return self.args

    def require_arguments(self, *params: str) -> bool:
        """
        Check if all required parameters are present

        Args:
            *params: Parameter names to check

        Returns:
            True if all required parameters exist, False otherwise
        """
        for param in params:
            if not self.has_argument(param):
                return False
        return True


class Utils:
    """
    Utility class for resolving file paths and other common operations
    """

    @staticmethod
    def get_project_root() -> Path:
        """
        Get the project root directory

        Returns:
            Path object representing the project root directory
        """
        # Assuming src is one level down from project root
        return Path(__file__).parent.parent.parent

    @staticmethod
    def resolve_path(relative_path: str) -> Path:
        """
        Resolve a path relative to the project root

        Args:
            relative_path: Path relative to project root

        Returns:
            Absolute path as a Path object
        """
        return Utils.get_project_root() / relative_path

    @staticmethod
    def read_file(relative_path: str, encoding: str = "utf-8") -> str:
        """
        Read a file from a path relative to project root

        Args:
            relative_path: Path relative to project root
            encoding: File encoding

        Returns:
            File contents as string
        """
        file_path = Utils.resolve_path(relative_path)
        with open(file_path, "r", encoding=encoding) as file:
            return file.read()

    @staticmethod
    def write_file(relative_path: str, content: str, encoding: str = "utf-8") -> None:
        """
        Write content to a file at path relative to project root

        Args:
            relative_path: Path relative to project root
            content: Content to write to file
            encoding: File encoding
        """
        file_path = Utils.resolve_path(relative_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as file:
            file.write(content)

    @staticmethod
    def ensure_str(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            new_args = tuple(str(arg) for arg in args)
            new_kwargs = {key: str(value) for key, value in kwargs.items()}
            return func(*new_args, **new_kwargs)

        return wrapped

    @staticmethod
    @ensure_str
    def highlight_text(text: str, fore: colorama.Fore):
        return f"{fore}{text}{colorama.Style.RESET_ALL}"
