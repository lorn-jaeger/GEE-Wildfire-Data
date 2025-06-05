
from tqdm import tqdm
import logging

class ConsoleUI:
    _bars = {}
    _verbose = True

    @classmethod
    def set_verbose(cls, verbose):
        cls._verbose = verbose

    @classmethod
    def set_bar_position(cls, key: str, value: int):
        """
        Set the current progress of the tqdm bar identified by `name`.

        Args:
            key(str): Identifier for the progress bar.
            value (int): Current progress value to set.
        """
        if key in cls._bars:
            bar = cls._bars[key]
            bar.n = value
            bar.refresh()
        # else:
        #     cls.log(f"[ConsoleUI] Warning: Tried to set position of non-existent bar '{name}'")


    @classmethod
    def add_bar(cls, key, total, desc=""):
        if key in cls._bars:
            bar = cls._bars[key]
            bar.total = total
            bar.desc = desc
            bar.n = 0
            bar.reset()
            bar.refresh()
        else:
            cls._bars[key] = tqdm(total=total, desc=desc, position=len(cls._bars), leave=True)
            
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
            del cls._bars[key]

    @classmethod
    def close_all_bars(cls):
        for key in cls._bars.keys():
            cls.close_bar(key=key)

    @classmethod
    def refresh_all(cls):
        for bar in cls._bars.values():
            bar.refresh()

    @classmethod
    def print(cls, message, end="\n"):
        if cls._verbose:
            tqdm.write(message, end=end)

    @classmethod
    def log(cls, message, level=logging.INFO):
        if cls._verbose:
            logging.log(level, message)
