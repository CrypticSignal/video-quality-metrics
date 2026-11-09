import logging
import os
import sys
from typing import NoReturn

# The single logger used throughout the program.
log = logging.getLogger("vqm")


def setup_logging() -> None:
    """Log to the terminal."""
    log.setLevel(logging.INFO)

    terminal_handler = logging.StreamHandler()
    terminal_handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(terminal_handler)


def line() -> None:
    """Log a horizontal line that spans the width of the terminal."""
    try:
        width = os.get_terminal_size().columns
    except OSError:
        width = 80
    log.info("-" * width)


class VideoError(Exception):
    """An error that stops one input video from being processed, but not the others."""


def fail(message: str) -> NoReturn:
    """Stop processing the current input video. main.py logs the message and moves on to the
    next input video, if there is one."""
    raise VideoError(message)


def exit_program(message: str) -> NoReturn:
    """Exit because of an error that would affect every input video, e.g. FFmpeg not being
    installed."""
    line()
    log.error(f"{message}\nThis program will now exit.")
    line()
    sys.exit(1)


def format_si(value: float, unit: str, decimal_places: int) -> str:
    """Format a value using SI prefixes, e.g. format_si(1234567, "B", 3) -> "1.235 MB"."""
    prefixes = ["", "K", "M", "G", "T"]
    index = 0
    while value >= 1000 and index < len(prefixes) - 1:
        value /= 1000
        index += 1

    if index == 0:
        decimal_places = 0

    return f"{value:.{decimal_places}f} {prefixes[index]}{unit}"
