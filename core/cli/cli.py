from .repl import REPL
from core.config import PATH_XRNS, PATH_SAMPLES
from core.audio.backend import AudioManager
from core.lib.xrns import XRNS
from core.res.cli_messages import MSG_HEADER, MSG_SERVE
from core.io.logger import LoggerFactory

logger, lf = LoggerFactory(__name__)


class CLIApp(REPL):
    def __init__(self, debug=True, silent=False) -> None:
        super().__init__()
        self.debug = debug
        self.xrns = XRNS()
        if not silent:
            print(MSG_HEADER)
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
        self.set_dir(PATH_SAMPLES, PATH_XRNS)

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
            if not self.evaluate(res):
                quit = True
        self.stop()

    def stop(self):
        self.audio.stop()