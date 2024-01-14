
import curses
import core.cli.colors as CLR
import logging
import time

logger = logging.getLogger()


class Screen:
    def __init__(self, screen) -> None:
        self.scr = screen
        self.scr.keypad(1)
        self.scr.notimeout(True)
        self.init_colors()

    def init_colors(self):
        CLR.set_colors()


class WindowManager:
    def __init__(self):
        self.maxy = curses.LINES - 1
        self.maxx = curses.COLS - 1

    def _update(self, dct):
        self.__dict__.update(dct)

    def add(self, **kwargs):
        for category in kwargs.keys():
            if category == 'standard':
                cls = Window
            elif category == 'message':
                cls = MessageWindow
            elif category == 'data':
                cls = DataWindow
            elif category == 'sequence':
                cls = SequenceWindow
            elif category == 'pattern':
                cls = PatternWindow

            for window_name, params in kwargs[category].items():
                pn = 'height', 'width', 'begin_y', 'begin_x', 'clr', 'hclr'
                separator = True if window_name \
                    in ['sequences', 'window2'] else False
                hide_empty = True if window_name == 'sequences' else False

                win = cls(
                    **{name: params[num] for num, name in enumerate(pn)},
                    hide_empty=hide_empty, separator=separator)
                self._update({window_name: win})

    def refresh_all(self):
        for name, object in self.__dict__.items():
            if hasattr(object, 'refresh'):
                object.get_data()
                object.refresh()


class Window:
    def __init__(
            self,
            scrollable=False, separator=False,
            **kwargs):
        self.win = curses.newwin(
            kwargs['height'], kwargs['width'],
            kwargs['begin_y'], kwargs['begin_x'])
        self.scrollable = scrollable
        self.separator = separator
        self.header = ''
        if scrollable:
            # self.win.setscrreg(0, 1)
            self.win.scrollok(True)
            self.win.leaveok(True)
            self.win.idlok(True)
        self.set_background(kwargs['clr'])
        self.active_line = 0
        self.active_col = 0
        self.height = kwargs['height']
        self.width = kwargs['width']
        self.clr = kwargs['clr']
        self.hclr = kwargs['hclr']

    def set_background(self, color_pair):
        self.win.bkgd(' ', curses.color_pair(color_pair))

    def focus(self, row=0):
        self.move(0, row)
        self.win.refresh()
        # curses.setsyx(1,0)
        # time.sleep(4)

    def focus_marker(self, y, x):
        self.move(y, x)
        self.print('[0', clr=3)
        self.win.refresh()

    def move(self, y, x):
        self.win.move(y, x)
        self.active_line = y
        self.active_col = x

    def move_pos_back(self):
        if self.active_col > 2:
            self.move(self.active_line, self.active_col-1)

    def backspace(self):
        self.move_pos_back()
        self.print(' ', end='')
        self.move_pos_back()

    def clear(self):
        self.win.erase()
        self.active_line = 0
        self.active_col = 0
        self.win.refresh()

    def write(self, char, move=True):
        self.win.addch(char)
        if move:
            self.active_col += 1
        self.win.refresh()

    def draw_separator(self):
        if self.separator:
            self.print('_' * (self.width), y=self.height - 2, end='')

    def parse_header(self):
        if '{' in self.header:
            hsplit = self.header.split('{')
            value = hsplit[1][:-1]
            ns, pr = value.split('.') if '.' in value else [value, '']
            return [hsplit[0], self.get_data_from_object(ns, pr)]
        else:
            return [self.header, '']

    def draw_header(self):
        key, value = self.parse_header()
        if value == {}:
            value = ''
        header = f' {key} {value}'
        self.print(header + ' ' * (self.width -
                   len(header) - 4), clr=self.hclr)
        self.print('')

    def print(self, msg, end='\n', x=0, y=0,
              pad=None, pad_chr=None, clr=0):
        clr = self.clr if clr == 0 else clr
        msg = str(msg)
        msg += end if not end == '\n' else ''
        if x == 0 and y == 0:
            y = self.active_line
            x = self.active_col
        if y < 0 or y > curses.LINES or x < 0 or x > curses.COLS:
            return
        if x + len(msg) > curses.COLS:
            s = msg[:curses.COLS - x]
        else:
            s = msg
            if pad:
                ch = pad_chr or " "
                if pad is True:
                    pad = curses.COLS  # pad to edge of screen
                    s += ch * (pad - x - len(msg))
                else:
                    # pad to given length (or screen width)
                    if x + pad > curses.COLS:
                        pad = curses.COLS - x
                    s += ch * (pad - len(msg))

        if not clr:
            clr = CLR.CLR_LOG1
        self.active_col += len(msg)
        maxy, maxx = self.win.getmaxyx()
        try:
            self.win.addstr(y, x, s, curses.color_pair(clr))
        except:
            logging.error('Curses Error while printing.')
        if self.active_line + 1 == maxy and self.height > 1:
            if self.scrollable:
                self.win.scroll()
                self.active_col = 0
        elif end == '\n':
            self.active_line += 1
            self.active_col = 0
            self.win.move(self.active_line-1, 0)
        self.win.refresh()


class MessageWindow(Window):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, scrollable=True)


class DataWindow(Window):
    def __init__(self, vertical=True, hide_empty=False, **kwargs):
        scrollable = True if vertical else False
        super().__init__(**kwargs, scrollable=scrollable)
        self.data = {}
        self.vertical = True if kwargs['height'] > 1 else False
        self.pending = False
        self.hide_empty = hide_empty
        self.cb_get_data = None

    def add_get_data_cb(self, object, namespace, prop):
        self.cb_get_data = [object, namespace, prop]

    def get_data_from_object(self, namespace, prop):
        data = {}
        if namespace == '':
            if hasattr(self.obj, prop):
                data = getattr(self.obj, prop)
                if callable(data):
                    data = data()
        else:
            if hasattr(self.obj, namespace):
                sub = getattr(self.obj, namespace)
                if hasattr(sub, prop):
                    data = getattr(sub, prop)
        return data

    def get_data(self):
        self.data = {}
        cb = self.cb_get_data
        if not cb:
            return False
        getter = cb[0]
        self.obj = getter()
        if cb and self.obj:
            self.data = self.get_data_from_object(cb[1], cb[2])

    def render_item(self, item):
        key, value = item
        if self.vertical:
            key = f'{key:02}' if type(key) is int \
                else f'{str(key):9}'
        msg = f' {key}: {str(value)}'
        if not self.vertical and key == 'file':
            value = 'untitled' if not value else value
            msg = f' {str(value)} '
        msg = msg if self.vertical else f' {msg} '
        self.print(
            msg, end='\n' if self.vertical else '')

    def refresh(self):
        self.clear()
        if self.header and self.vertical:
            self.draw_header()
        if self.data:
            for item in self.data.items():
                if not (item[1] == '' and self.hide_empty):
                    self.render_item(item)
        self.draw_separator()


class SequenceWindow(DataWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {}

    def render_item(self, item):
        key, value = item
        grp = value['group']
        if not value['name']:
            return
        self.print(f'{key:02}: ', end='')
        clr = 20 + grp if grp and grp >= 0 and grp < 5 else 0
        self.print(value['name'], end='\n', clr=clr)


class PatternWindow(DataWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {}
        self.cb_line_renderer = None

    def add_line_renderer(self, cb):
        self.cb_line_renderer = cb

    def refresh(self):
        if not self.data or not self.cb_line_renderer:
            return
        self.clear()
        if type(self.data) is list:
            for step in self.data:
                if len(step) > 1:
                    repr = self.cb_line_renderer(step[1])
                else:
                    repr = ''
                self.print(f'[{step[0]:02}] {repr}')
