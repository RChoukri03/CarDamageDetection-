import logging
import sys

from utils.singleton import Singleton


class ColorFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)


class Logger(object, metaclass=Singleton):
    rootLogger = None

    def __init__(self, logLevel=logging.INFO):
        self.rootLogger = logging.getLogger()
        self.rootLogger.setLevel(logging.INFO)

        fmt = "{asctime} - {levelname:>3.3} - {name:>10.10} - {message}"
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(ColorFormatter(fmt))

        fileHandler = logging.FileHandler("logs")
        fileHandler.setFormatter(logging.Formatter(fmt, style="{"))

        self.rootLogger.addHandler(streamHandler)
        self.rootLogger.addHandler(fileHandler)

        self.setRootLogLevel(logLevel)

    def setRootLogLevel(self, level):
        self.rootLogger.setLevel(level)

    def getLogger(self, name):
        return logging.getLogger(name)


logger = Logger()


def getLogger(logName):
    return logger.getLogger(logName)
