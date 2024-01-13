import __main__
import sys
import logging
from core.cli.colors import Col

# logging.basicConfig(format='%(message)s', level=logging.INFO)

try:
    unicode
    _unicode = True
except NameError:
    _unicode = False


class LoggerFactory:
    def __new__(cls, name):
        cls.name = name
        exec = __main__.__file__.split('/')[-1]
        tui_mode = '--tui' in sys.argv
        if exec == 'gui.py':
            ln = cls.getName(cls)
            return cls.getKivyLogger(cls), lambda x: f'{ln}: {x}'
        else:
            ln = cls.getName(cls)
            if tui_mode:
                return cls.getCursesLogger(cls, name), lambda x: x
            else:
                return cls.getDefaultLogger(cls, name), lambda x: x

    def getName(cls):
        return cls.name.split('.')[-1].capitalize()

    def getDefaultLogger(cls, name):
        import logging
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(SimpleColorFormatter())
        logger.addHandler(ch)
        return logger

    def getCursesLogger(cls, name):
        import logging
        return logging.getLogger(name)

    def getKivyLogger(cls):
        from kivy.logger import Logger
        return Logger


class SimpleColorFormatter(logging.Formatter):
    grey = "\\x1b[38;21m"
    yellow = "\\x1b[33;21m"
    red = '\033[0;31m'
    bold_red = "\\x1b[31;1m"
    reset = Col.RESET
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: Col.FAINT + format + reset,
        logging.INFO: Col.FAINT + format + reset,
        logging.WARNING: Col.GREEN + format + reset,
        logging.ERROR: Col.RED + format + reset,
        logging.CRITICAL: Col.RED + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CursesHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self.screen = screen.win
        self.win = screen

    def emit(self, record):
        try:
            msg = self.format(record)
            screen = self.screen
            fs = "\n%s"
            if not _unicode:
                screen.addstr(fs % msg)
                screen.refresh()
            else:
                try:
                    if (isinstance(msg, unicode)):
                        ufs = u'\n%s'
                        try:
                            screen.addstr(ufs % msg)
                            screen.refresh()
                        except UnicodeEncodeError:
                            screen.addstr((ufs % msg).encode(msg))
                            screen.refresh()
                    else:
                        screen.addstr(fs % msg)
                        screen.refresh()
                except UnicodeError:
                    screen.addstr(fs % msg.encode("UTF-8"))
                    screen.refresh()
            self.win.active_line += 1
            self.win.active_col = 0
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
