import logging


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_ = "%(levelname)s | %(asctime)s | (%(filename)s:%(lineno)d) - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_ + reset,
        logging.INFO: grey + format_ + reset,
        logging.WARNING: yellow + format_ + reset,
        logging.ERROR: red + format_ + reset,
        logging.CRITICAL: bold_red + format_ + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def configure_logging(level=logging.DEBUG, logger=None):
    """
    Configures a simple console logger with the givel level.
    A usecase is to change the formatting of the default handler of the root logger
    """
    logger = logger or logging.getLogger()  # either the given logger or the root logger
    logger.setLevel(level)
    # If the logger has handlers, we configure the first one. Otherwise we add a
    # handler and configure it
    if logger.handlers:
        console = logger.handlers[
            0
        ]  # we assume the first handler is the one we want to configure
    else:
        console = logging.StreamHandler()
        logger.addHandler(console)
    console.setFormatter(CustomFormatter())
    console.setLevel(level)
