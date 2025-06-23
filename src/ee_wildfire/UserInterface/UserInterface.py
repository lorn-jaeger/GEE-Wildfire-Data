import contextlib
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Union

from colorama import Fore, Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.styles import Style as S
from tqdm import tqdm

from ee_wildfire.constants import DEFAULT_LOG_DIR, LOG_LEVELS

color_map = {
    "green": Fore.GREEN,
    "red": Fore.RED,
    "yellow": Fore.YELLOW,
    "white": Fore.WHITE,
}


@contextlib.contextmanager
def _suspend_tqdm_output():
    # Temporarily disable tqdm output (stdout hijack)
    original_stdout = sys.stdout
    try:
        sys.stdout = sys.__stdout__
        yield
    finally:
        sys.stdout = original_stdout


class ConsoleUI:
    _bars = {}
    _verbose = True
    _status_line_position = 0
    _logger = None
    _log_dir = Path("")
    _log_file = ""
    _lock = RLock()

    # ========================================
    #               Misc Public Methods
    # ========================================

    @classmethod
    def clear_screen(cls):
        if not cls._verbose:
            return
        if os.name == "nt":  # Windows
            os.system("cls")
        else:  # Unix/Linux/Mac
            os.system("clear")

    @classmethod
    def set_verbose(cls, verbose):
        cls._verbose = verbose

    # ========================================
    #               Private Methods
    # ========================================

    @classmethod
    def _get_bar_position(cls) -> int:
        # Line 0: status, Line 1: prompt, bars start at 2
        with cls._lock:
            return len(cls._bars) + 2

    @classmethod
    def _get_bar_format(cls) -> str:
        columns, _ = shutil.get_terminal_size()
        desc_length = int(columns / 3)
        bar_length = int(columns / 2)
        desc = "{" + f"desc:<{desc_length}" + "}"
        bar = "{" + f"bar:{bar_length}" + "}"
        output = (
            f"{desc} | {bar} | "
            + "{percentage:>6.2f}% | {n_fmt:>7}/{total_fmt:<7} items"
        )
        return output

    @classmethod
    def _create_log_file(cls, tag="run") -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d:%H")
        filename = f"{timestamp}-{tag}.log"
        cls._log_file = cls._log_dir / filename

    # ========================================
    #               Bars
    # ========================================

    @classmethod
    def add_bar(cls, key: str, total: int, desc="", color="green"):
        with cls._lock:
            if cls._verbose:
                bar_format = cls._get_bar_format()
                if key in cls._bars:
                    bar = cls._bars[key]
                    bar.total = total
                    bar.desc = desc
                    bar.colour = color
                    bar.n = 0
                    bar.reset()
                    bar.refresh()
                else:
                    cls._bars[key] = tqdm(
                        total=total,
                        desc=desc,
                        position=cls._get_bar_position(),
                        leave=True,
                        file=sys.stdout,
                        colour=color,
                        ascii=False,
                        bar_format=bar_format,
                    )

    @classmethod
    def set_bar_position(cls, key: str, value: int):
        with cls._lock:
            if key in cls._bars:
                bar = cls._bars[key]
                bar.n = value
                bar.refresh()

    @classmethod
    def change_bar_desc(cls, key: str, desc: str):
        with cls._lock:
            if key in cls._bars.keys():
                cls._bars[key].desc = desc

    @classmethod
    def change_bar_total(cls, key: str, total: int):
        with cls._lock:
            if key in cls._bars.keys():
                cls._bars[key].total = total
                cls._bars[key].refresh()

    @classmethod
    def update_bar(cls, key: str, n=1):
        with cls._lock:
            if key in cls._bars:
                cls._bars[key].update(n)
                cls._bars[key].refresh()

    @classmethod
    def reset_bar(cls, key: str, n=0):
        with cls._lock:
            if key in cls._bars.keys():
                cls._bars[key].n = n
                cls._bars[key].update(n)

    @classmethod
    def close_all_bars(cls):
        with cls._lock:
            keys = cls._bars.keys()
            for key in keys:
                cls._bars[key].close()

    @classmethod
    def refresh_all(cls):
        with cls._lock:
            for bar in cls._bars.values():
                bar.refresh()

    # ========================================
    #           Text and Status Line
    # ========================================

    @classmethod
    def write(cls, message: str, end="\n"):
        if cls._verbose:
            tqdm.write(message, end=end)

    @classmethod
    def print(cls, message: str, color="green"):
        """
        Print a status line at the top (position 0) above all tqdm bars.
        """

        logger = cls._logger
        if logger:
            logger.info(message)

        if not cls._verbose:
            return

        with cls._lock:
            term_width = shutil.get_terminal_size((80, 20)).columns
            padded = (
                color_map[color]
                + f"[STATUS] {message}".ljust(term_width)
                + Style.RESET_ALL
            )
            tqdm.write(padded, end="\r")
            # tqdm.write(padded)

            # Flush to ensure immediate overwrite
            sys.stdout.flush()

    @classmethod
    def prompt_path(cls, prompt="Enter file path: "):
        if not cls._verbose:
            return ""

        with _suspend_tqdm_output():
            sys.stdout.write("\n\033[1K")  # Move to next line, clear it
            sys.stdout.flush()

            session = PromptSession()
            completer = PathCompleter(expanduser=True)

            style = S.from_dict(
                {
                    "prompt": "ansiblue",  # blue text
                }
            )

            path = session.prompt(
                [("class:prompt", prompt)], completer=completer, style=style
            )

            sys.stdout.write("\033[2A\033[2K")
            sys.stdout.flush()

            cls.log(f"Path input: {path}")

            return path

    # ========================================
    #               Logging
    # ========================================

    @classmethod
    def setup_logging(cls, log_dir: Union[Path, str], log_level="info", file_tag="run"):
        cls._log_dir = Path(log_dir)
        cls._create_log_file(tag=file_tag)
        cls._logger = logging.getLogger("ConsoleUI")
        cls.set_log_level(log_level)

        # Remove any old handlers (for reruns)
        if cls._logger.hasHandlers():
            cls._logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(cls._log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        cls._logger.addHandler(file_handler)

    @classmethod
    def get_log_handlers(cls):
        with cls._lock:
            if cls._logger:
                return cls._logger.handlers

    @classmethod
    def set_log_level(cls, level: str):
        with cls._lock:
            if cls._logger:
                cls._logger.setLevel(LOG_LEVELS[level])

    @classmethod
    def debug(cls, message: str):
        with cls._lock:
            if message:
                if cls._logger:
                    cls._logger.log(logging.DEBUG, message)

    @classmethod
    def log(cls, message: str):
        with cls._lock:
            if message:
                if cls._logger:
                    cls._logger.log(logging.INFO, message)

    @classmethod
    def warn(cls, message: str):
        with cls._lock:
            if message:
                if cls._logger:
                    cls._logger.log(logging.WARNING, message)

    @classmethod
    def error(cls, message: str):
        with cls._lock:
            if message:
                if cls._logger:
                    cls._logger.log(logging.ERROR, message)


def main():
    ConsoleUI.setup_logging(DEFAULT_LOG_DIR, "debug")
    ConsoleUI.log("logging stuff")
    ConsoleUI.debug("debuggin stuff")
    ConsoleUI.warn("Warnign here!")
    ConsoleUI.error("Something went wrong")


if __name__ == "__main__":
    main()
