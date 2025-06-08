
from tqdm import tqdm
import logging
import sys
import shutil
import contextlib
import os

from colorama import Fore, Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.styles import Style as S
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

    @classmethod
    def clear_screen(cls):
        if not cls._verbose:
            return
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')

    @classmethod
    def setup_logging(cls, log_file=None, level=logging.INFO):
        """
        Setup logging configuration for both console and optional log file.

        Args:
            log_file (str): Optional path to log file.
            level (int): Logging level, e.g., logging.INFO or logging.DEBUG.
        """
        handlers = [logging.StreamHandler(sys.stdout)]

        if log_file:
            file_handler = logging.FileHandler(log_file, mode='w')
            handlers.append(file_handler)

        logging.basicConfig(
            level=level,
            format='[%(asctime)s] %(levelname)s - %(message)s',
            handlers=handlers
        )

    @classmethod
    def set_verbose(cls, verbose):
        cls._verbose = verbose

    @classmethod
    def _get_bar_position(cls):
        # Line 0: status, Line 1: prompt, bars start at 2
        return len(cls._bars) + 2

    @classmethod
    def set_bar_position(cls, key: str, value: int):
        if key in cls._bars:
            bar = cls._bars[key]
            bar.n = value
            bar.refresh()

    @classmethod
    def _get_bar_format(cls):
        columns, rows = shutil.get_terminal_size()
        desc_length = int(columns/3)
        bar_length = int(columns/2)
        desc = "{" + f"desc:<{desc_length}" + "}"
        bar = "{" + f"bar:{bar_length}" +"}"
        output = f"{desc} | {bar} | " + "{percentage:>6.2f}% | {n_fmt:>7}/{total_fmt:<7} items"
        return output

    @classmethod
    def add_bar(cls, key, total, desc="", color="green"):
        if cls._verbose:
            bar_format = cls._get_bar_format()
            if key in cls._bars:
                bar = cls._bars[key]
                bar.total = total
                bar.desc = desc
                bar.colour=color
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
    def change_bar_desc(cls, key, desc):
        if key in cls._bars.keys():
            cls._bars[key].desc=desc

    @classmethod
    def change_bar_total(cls, key, total):
        if key in cls._bars.keys():
            cls._bars[key].total = total
            cls._bars[key].refresh()


    @classmethod
    def update_bar(cls, key, n=1):
        if key in cls._bars:
            cls._bars[key].update(n)

    @classmethod
    def reset_bar(cls, key, n=0):
        if key in cls._bars.keys():
            cls._bars[key].n=n
            cls._bars[key].update(n)

    @classmethod
    def close_bar(cls, key):
        if key in cls._bars:
            cls._bars[key].close()

    @classmethod
    def close_all_bars(cls):
        keys = cls._bars.keys()
        for key in keys:
            cls._bars[key].close()

    @classmethod
    def refresh_all(cls):
        for bar in cls._bars.values():
            bar.refresh()

    @classmethod
    def write(cls, message, end="\n"):
        if cls._verbose:
            tqdm.write(message, end=end)

    @classmethod
    def print(cls, message, color="green"):
        """
        Print a status line at the top (position 0) above all tqdm bars.
        """

        color_map = {
            "green": Fore.GREEN,
            "red": Fore.RED,
            "yellow": Fore.YELLOW,
        }
        if not cls._verbose:
            return

        term_width = shutil.get_terminal_size((80, 20)).columns
        padded = color_map[color] + f"[STATUS] {message}".ljust(term_width) + Style.RESET_ALL
        tqdm.write(padded, end="\r")

        # Flush to ensure immediate overwrite
        sys.stdout.flush()

    @classmethod
    def log(cls, message, level=logging.INFO):
        logging.log(level, message)

    @classmethod
    def prompt_path(cls, prompt="Enter file path: "):
        # Move cursor down from line 0 (status) to line 1, and clear it
        if not cls._verbose:
            return ""

        with _suspend_tqdm_output():
            sys.__stdout__.write("\n\033[1K")  # Move to next line, clear it
            sys.__stdout__.flush()

            session = PromptSession()
            completer = PathCompleter(expanduser=True)

            style = S.from_dict({
                'prompt': 'ansiblue',  # blue text
            })

            path = session.prompt(
                [('class:prompt', prompt)],
                completer=completer,
                style=style
            )

            # path = session.prompt(prompt, completer=completer)

            # Optional: write a blank line after input to maintain layout
            sys.__stdout__.write("\033[2A\033[2K")
            sys.__stdout__.flush()

            return path

def main():
    print(ConsoleUI._get_bar_format())


if __name__ == "__main__":
    main()
