import curses

class Col:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    FAINT = '\033[2m'
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'


class BCol:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def set_colors():
    global CLR_HEADING, CLR_FOOTER
    global CLR_CMDLINE, CLR_INPUT, CLR_LOG1, CLR_LOG2
    global CLR_LOG_DEBUG, CLR_LOG_ERROR, CLR_LOG_CMDMESSAGE

    if curses.has_colors():
        # window colors
        curses.init_pair(1, 7, 0)
        curses.init_pair(2, 0, 7)
        curses.init_pair(3, 7, 0)
        curses.init_pair(4, 3, 0)
        curses.init_pair(5, 2, 0)
        curses.init_pair(6, 0, 1)
        curses.init_pair(7, 6, 0)
        curses.init_pair(8, 0, 7)

        # highlight colors
        curses.init_pair(10, 0, 2)
        curses.init_pair(11, 7, 1)

        # group colors
        curses.init_pair(20, 4, 0)
        curses.init_pair(21, 6, 0)
        curses.init_pair(22, 3, 0)
        curses.init_pair(23, 5, 0)

    CLR_LOG1 = curses.color_pair(3)
    CLR_LOG2 = curses.color_pair(6)
    CLR_LOG_DEBUG = curses.color_pair(4)
    CLR_LOG_ERROR = curses.color_pair(2)
    CLR_LOG_CMDMESSAGE = curses.color_pair(2)
