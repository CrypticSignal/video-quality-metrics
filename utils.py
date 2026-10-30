import logging
import os
import sys

# The single logger used throughout the program.
log = logging.getLogger("vqm")


def setup_logging(log_file: str = "logs.log") -> None:
    """Log to the terminal and to a log file, which is overwritten on each run."""
    log.setLevel(logging.INFO)

    terminal_handler = logging.StreamHandler()
    terminal_handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(terminal_handler)

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    log.addHandler(file_handler)


def line() -> None:
    """Log a horizontal line that spans the width of the terminal."""
    try:
        width = os.get_terminal_size().columns
    except OSError:
        width = 80
    log.info("-" * width)


def exit_program(message: str) -> None:
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
