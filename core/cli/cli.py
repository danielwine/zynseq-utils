from .repl import REPL
from core.audio.backend import AudioManager
from core.lib.xrns import XRNS
from core.res.cli_messages import MSG_HEADER, MSG_HELP_MIN, MSG_SERVE
from core.io.logger import LoggerFactory

logger, lf = LoggerFactory(__name__)


class CLIApp(REPL):
    def __init__(self, debug=True, silent=False) -> None:
        super().__init__()
        self.debug = debug
        self.xrns = XRNS()
        if not silent:
            print(MSG_HEADER)
            logger.info(MSG_HELP_MIN)
        else:
            print(MSG_SERVE)
            print(MSG_HEADER.split('\n')[1])
        if self.debug:
            logger.info(lf('Debugging is on.'))

    def initialize(self):
        self.audio = AudioManager(
            init_delay=0.2, verbose=False, debug=self.debug)
        self.audio.initialize()
        self.audio.start()
        context = self.audio.context
        self.set_dir(context['path_snapshot'], context['path_xrns'])

    def loop(self):
        quit = False
        while not quit:
            res = input(
                f'b{self.audio.seq.bank:02d}p{self.audio.seq.pattern.id:02d}> ')
            res = res.strip()
            if res == '':
                res = prev_res
            else:
                prev_res = res
            if self.evaluate(res) == False:
                quit = True
        self.stop()

    def stop(self):
        self.audio.stop()
