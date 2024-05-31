import logging
import os
import sys

# Define our log-level constants
CRITICAL = logging.CRITICAL  # 50
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10

LOGGER_NAME = "EPISODE"
LOGFILE_NAME = "episode.log"
LOGFILE_FORMAT = (
    "%(asctime)-24s %(processName)-12s %(threadName)-12s"
    "%(name)-10s %(levelname)-7s %(message)s"
)


def _initial_setup():
    episode_logger = logging.getLogger(LOGGER_NAME)

    episode_logger.setLevel(DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_formatter = logging.Formatter("%(message)s")
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(INFO)
    episode_logger.addHandler(stdout_handler)
    episode_logger.propagate = False

    return episode_logger, stdout_handler


EPISODE_LOGGER, STDOUT_HANDLER = _initial_setup()


def configure_file_logger(filename=LOGFILE_NAME, filepath="./", level=DEBUG):
    logfile_path = os.path.join(filepath, filename)

    try:
        file_handler = logging.FileHandler(logfile_path, encoding="utf-8")
    except IOError as err:
        # If we cannot open the logfile for any reason just continue
        # regardless, but log the error (it will go to stdout).
        EPISODE_LOGGER.error(
            "Cannot open log file at %s for writing: %s", logfile_path, err
        )
        return None
    else:
        file_handler.setLevel(level)
        formatter = logging.Formatter(LOGFILE_FORMAT)
        file_handler.setFormatter(formatter)
        EPISODE_LOGGER.addHandler(file_handler)

        EPISODE_LOGGER.debug("Enabled logging to file: %s", logfile_path)
        return file_handler
