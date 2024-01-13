
import time
from os.path import isfile, join, splitext
from os import listdir, getcwd
from core.io.files import get_files, get_first_file
from core.audio.utils import is_port, format_port
from core.audio.manipulator import Manipulator
from core.res.cli_zynseqcmds import pcmds, lcmds
from core.res.cli_messages import MSG_USAGE, ERR_INVALID, ERR_MISSING_ARG


class REPL:

    def __init__(self):
        self.audio = None
        self.print = print
        self.custom_target = False
        self.events = {}
        self.last_multi = False

    def set_dir(self, snapshot_path, xrns_path):
        self.snapshot_path = snapshot_path
        self.xrns_path = xrns_path

    def set_print_method(self, cb):
        self.print = cb
        self.custom_target = True

    def register_event(self, event, cb):
        self.events[event] = cb

    def call_event_callback(self, event):
        if event in self.events:
            self.events[event]()

    def pprint(self, data):
        if type(data) == dict:
            for key, value in data.items():
                key = f'{key}'
                value = 'empty' if value == False else value
                self.print(f"  {key:<5s} : {value}")
        if type(data) == list:
            for el in data:
                if type(el) == tuple:
                    if is_port(el[0]):
                        self.print(format_port(el[0]))
                        for port in el[1]:
                            self.print('  ' + format_port(port))
                    else:
                        self.print(f"  {el[0]}: {el[1]}")
                else:
                    if is_port(el):
                        self.print('  ' + format_port(el))
                    else:
                        self.print(f"  {el}")

    def mprint(self, data):
        self.print('  ' + ' '.join([key for key in data.keys()]))

    def get_docstrings_for(self, cls, startswith=''):
        cmds = {}
        for method in cls.__dict__.items():
            if method[0].startswith('_'):
                continue
            if method[0].startswith(startswith):
                cmds[method[0][len(startswith):]] = method[1].__doc__
        return cmds

    def show_help(self, low_level=False, short=False):
        cmds_repl = self.get_docstrings_for(REPL, 'cmd_')
        cmds_man = self.get_docstrings_for(Manipulator)
        if short:
            self.mprint(cmds_repl)
            self.mprint(pcmds)
            self.mprint(cmds_man)
            return
        if not low_level:
            self.pprint(cmds_repl)
            self.pprint(pcmds)
            self.pprint(cmds_man)
            self.print('Type h+ to list low-level commands.')
        else:
            self.pprint(lcmds)

    def convert_params(self, par, specs):
        ret = []
        for num, typ in enumerate(specs):
            if typ == 'i':
                if par[num].isnumeric():
                    ret.append(int(par[num]))
                else:
                    self.print_newline_on(1)
                    self.print(f'{ERR_INVALID}: numeric')
                    return False
            if typ == 'b':
                nm = int(par[num])
                if nm >= 0 and nm < 2:
                    ret.append(False if nm == 0 else True)
                else:
                    self.print(f'{ERR_INVALID}: boolean')
                    return False
        return ret

    def invoke_lib_function(self, fn, specs, p):
        if len(p) < len(specs):
            arg = specs[len(p)]
            self.print(f'{ERR_MISSING_ARG}: {arg}')
            return False
        p = self.convert_params(p, specs)
        if p == None or p == False:
            return False
        lp = len(p)
        if lp == 0:
            r = fn()
        if lp == 1:
            r = fn(p[0])
        elif lp == 2:
            r = fn(p[0], p[1])
        elif lp == 3:
            r = fn(p[0], p[1], p[2])
        elif lp == 4:
            r = fn(p[0], p[1], p[2], p[3])
        elif lp == 5:
            r = fn(p[0], p[1], p[2], p[3], p[4])
        return r

    def load(self, par):
        if not par:
            self.print('Please specify file name.')
            return False
        zss = get_first_file(self.snapshot_path, 'zss', par[0])
        xrns = get_first_file(self.xrns_path, 'xrns', par[0])
        if zss:
            self.load_zss(zss)
            self.file = zss
        elif xrns:
            self.load_xrns(xrns)
            self.file = xrns
        self.file = ''

    def load_zss(self, file):
        success = self.audio.seq.load_file(
            self.snapshot_path, file)
        if success:
            self.audio.seq.get_statistics()
            if not self.emit_event('file_loaded'):
                self.pprint(self.audio.seq.statistics)
        else:
            return False

    def load_xrns(self, file):
        success = self.xrns.load(file)
        if not success:
            return
        self.audio.seq.import_project(file, self.xrns.project)
        # self.audio.seq.update_tempo()
        self.emit_event('file_loaded')

    def emit_event(self, event):
        if event in self.events:
            self.call_event_callback(event)
            return True
        else:
            return False

    def parse_libcmds(self, cmd, par):
        fnsplit = lcmds[cmd].split()
        fname = fnsplit[0]
        try:
            func = getattr(self.audio.seq.libseq, fname)
            ret = self.invoke_lib_function(func, fnsplit[1:], par)
            if ret:
                self.print(ret)
            else:
                return False
        except AttributeError as e:
            self.print(e)

    def parse_pycmds(self, cmd, par):
        fnsplit = pcmds[cmd].split()
        fname = fnsplit[0]
        func = getattr(self.audio.seq, fname)
        par = self.convert_params(par, fnsplit[1:])
        if par is False:
            return False
        if len(fnsplit) == 1:
            if callable(func):
                ret = func()
            else:
                ret = func
        if len(fnsplit) > 1:
            ret = func(*par)
        if ret:
            is_list = type(ret) is list
            is_dict = type(ret) is dict
            items = ret if is_list else ret.items()
            self.print_newline_on(len(items))
            if is_dict or is_list:
                self.pprint(ret)
            else:
                self.print(ret)

    def cmd_test(self, par):
        """play midi notes to test audio channels"""
        self.audio.seq.test_midi(self.print)

    def cmd_dir(self, par):
        """list ZSS files"""
        self.pprint(get_files(self.snapshot_path, 'zss'))
        self.pprint(get_files(self.xrns_path, 'xrns'))

    def cmd_load(self, par):
        """load ZSS file"""
        self.load(par)

    def cmd_save(self, par):
        """save ZSS file"""
        self.audio.seq.save_file()

    def cmd_ports(self, par):
        """list available jack ports"""
        if self.audio.client:
            self.pprint(self.audio.client.get_ports())

    def cmd_cons(self, par):
        """list jack connections"""
        if self.audio.client:
            self.pprint(self.audio.get_all_connections())

    def cmd_proc(self, par):
        """list running engines"""
        self.audio.check_services()

    def cmd_info(self, par):
        """print statistics"""
        self.pprint(self.audio.seq.statistics)

    def cmd_ls(self, par):
        """list properties of sequences"""
        prdct = self.audio.seq.get_props_of_sequences()
        props = [f'{num:2}:  {el["name"]:>2}/{el["group"]} ({el["trigger"]})' \
                for num, el in enumerate(prdct.values())]
        self.print("   ## nam/gr(tr)")
        self.pprint(props)

    def cmd_start(self, par):
        """start transport"""
        return self.audio.seq.transport_start('zt')

    def cmd_stop(self, par):
        """stop transport"""
        return self.audio.seq.transport_stop('zt')

    def check_events(self, cmd, redraw=False):
        if cmd == 'sp' or redraw:
            self.call_event_callback('pattern_changed')

    def print_newline_on(self, item_number):
        if item_number > 1:
            self.print('')
            self.last_multi = True
        else:
            if self.last_multi:
                self.print('')
            self.last_multi = False

    def evaluate(self, res):
        success = True
        force_redraw = False
        rsplit = res.split(' ')
        cmd = rsplit[0]
        par = rsplit[1:] if len(rsplit) > 1 else ''
        if cmd in ['x', 'exit', 'quit']:
            return False
        if cmd in ['h', 'help']:
            self.show_help()
        if cmd in ['h+', 'help+']:
            self.show_help(low_level=True)
        if cmd in ['u', 'usage']:
            self.print(MSG_USAGE)
        if hasattr(self, 'cmd_' + cmd):
            self.print('')
            getattr(self, 'cmd_' + cmd)(par)
            return True
        elif hasattr(self.audio.seq.man, cmd):
            getattr(self.audio.seq.man, cmd)(par)
            force_redraw = True
        elif cmd in lcmds:
            success = self.parse_libcmds(cmd, par)
        elif cmd in pcmds:
            success = self.parse_pycmds(cmd, par)
        else:
            return
        self.check_events(cmd, redraw=force_redraw)
        return True
