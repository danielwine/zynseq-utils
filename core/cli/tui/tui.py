import logging
import curses
from sys import stdout
from .screen import Screen, WindowManager
from .layout import get_layout
from ..repl import REPL
from core.io.logger import CursesHandler
from core.audio.backend import AudioManager
from core.lib.tracker import Note
from core.lib.xrns import XRNS
from core.res.cli_messages import MSG_HEADER

messageWindow = None
ctrl_c_was_pressed = False
logger = logging.getLogger()


def print(message):
    if hasattr(messageWindow, 'print'):
        messageWindow.print(message)


def ctrl_c_handler(signum, frame):
    global ctrl_c_was_pressed
    ctrl_c_was_pressed = True


def ctrl_c_pressed():
    global ctrl_c_was_pressed
    if ctrl_c_was_pressed:
        ctrl_c_was_pressed = False
        return True
    else:
        return False


class TUIApp(REPL):
    def __init__(self, stdscr, debug=False) -> None:
        super().__init__()
        self.debug = debug
        self.audio = AudioManager(
            init_delay=0.2, verbose=False, debug=self.debug)
        self.xrns = XRNS()
        self.screen = Screen(stdscr)
        self.screen.init_colors()
        self.initialize_screen()
        self.print_help()
        self.print('')
        if self.debug:
            print('DEBUG mode on.')
        self.start()

    def setup_logging(self, message_window):
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                logging.StreamHandler(),
                CursesHandler(message_window)
            ]
        )

    def on_pattern_change(self):
        self.win.window2.get_data()
        self.win.window2.refresh()
        self.win.pattern.get_data()
        self.win.pattern.refresh()

    def register_events(self):
        global messageWindow
        messageWindow = self.win.messages
        self.set_print_method(messageWindow.print)
        self.register_event('file_loaded', self.win.refresh_all)
        self.register_event('pattern_changed', self.on_pattern_change)

    def add_data_cb(self, win, namespace, method):
        def get_seq():
            if hasattr(self, 'audio'):
                if hasattr(self.audio, 'seq'):
                    return self.audio.seq
            return False
        win.add_get_data_cb(get_seq, namespace, method)

    def initialize_menu(self):
        menu = {}
        menu_line = '  '
        for key, name in menu.items():
            menu_line += f'{key} {name}   '
        self.win.footer.print(menu_line)

    def initialize_windows(self):
        def get_audio():
            if hasattr(self, 'audio'):
                return self.audio

        self.initialize_menu()
        self.win.console.write('>')
        self.win.sequences.header = 'SCENE {.bank}'
        self.win.window2.header = 'PATTERN {pattern.id}'
        self.win.status2.add_get_data_cb(
            get_audio, '', 'audio_status')
        self.add_data_cb(self.win.status, '', 'statistics')
        self.add_data_cb(self.win.sequences, '', 'get_props_of_sequences')
        self.add_data_cb(self.win.window2, 'pattern', 'info')
        self.add_data_cb(self.win.pattern, 'pattern', 'notes')

    def initialize_renderers(self):
        self.win.pattern.add_line_renderer(Note.get_string)

    def initialize_screen(self):
        self.win = WindowManager()
        self.win.add(**get_layout(self.win.maxx, self.win.maxy))
        self.initialize_windows()
        self.setup_logging(self.win.messages)
        self.register_events()

    def print_help(self):
        self.win.messages.print(MSG_HEADER, clr=1)
        print('Commands (type help for details):')
        self.show_help(short=True)

    def start(self):
        self.audio.initialize()
        self.set_dir(self.audio.context['path_snapshot'],
                     self.audio.context['path_xrns'])

        self.win.refresh_all()
        self.win.console.focus(2)
        self.audio.start()
        self.initialize_renderers()
        self.win.refresh_all()
        self.win.console.focus(2)
        self.loop()

    def loop(self):
        self.win.console.win.keypad(1)
        try:
            while True:
                c = 0
                c = self.win.console.win.getch()
                code = 0

                try:
                    if ctrl_c_pressed():
                        c = 24
                    # else:
                    #     self.screen.scr.timeout(1)
                    #     c = self.screen.scr.get_wch()
                    #     if c == -1:
                    #         continue
                    #     pass
                except curses.error as e:
                    logger.error(f'Error: {e}')

                if isinstance(c, int):
                    code = c
                else:
                    code = ord(c)

                # self.screen.scr.timeout(-1)   # resume blocking
                if code == curses.KEY_F1:
                    self.win.pattern.focus_marker(0, 0)
                    # self.screen.scr.refresh()
                elif c == curses.KEY_RESIZE:
                    # Generated by Curses when window/screen
                    # has been resized
                    y, x = self.screen.scr.getmaxyx()
                    curses.resizeterm(y, x)
                    c = self.screen.scr.get_wch()
                elif code == 10:
                    res = self.win.console.win.instr(0, 2).decode('utf-8')
                    self.win.console.clear()
                    self.win.console.print('> ', end='')
                    if not self.evaluate(res):
                        break
                    self.win.console.focus(2)
                elif code == 24 or code == curses.KEY_F10:
                    break
                elif code == curses.KEY_BACKSPACE:
                    self.win.console.backspace()
                # elif c == curses.KEY_DOWN:
                #     self.win.messages.print('DOWN')
                elif (code >= 48 and code <= 57) or (
                        (code >= 97 and code <= 122)) or code == 32:
                    self.win.console.write(chr(code))
                # elif code != -1:
                #     self.win.messages.print(code)

        finally:
            self.stop()
            self.screen.scr.erase()
            self.screen.scr.refresh()
            messageWindow = None
            self.screen.scr = None

    def stop(self):
        self.audio.stop()
        curses.endwin()
