import time
import json
from core.io.logger import LoggerFactory
from core.config import PATH_LIB
from core.audio.backend import AudioManager
from core.audio.generator import Generator
logger, lf = LoggerFactory(__name__)

CONFIG_ROOT = PATH_LIB + "/.."
SOURCE_BANK = 1
DEST_BANK = 10


class ZynBase:
    def __init__(self, debug=False, silent=False) -> None:
        super().__init__()
        self.debug = debug

    def initialize(self):
        self.audio = AudioManager(
            init_delay=0.2, verbose=False, debug=self.debug)
        self.audio.initialize()
        self.audio.start()
        self.audio.seq.transport_start('client')    # custom
        self.generator = Generator(self.audio.seq.libseq)

    def populate_pattern(self, bank_num, seq_num): 
        seq = self.audio.seq
        pattern_num = seq.libseq.getPatternAt(bank_num, seq_num, 0, 0)
        seq.libseq.selectPattern(pattern_num)
        self.generator.generate()
    
    def get_info_bank(self, bank_num):
        self.audio.seq.select_bank(bank_num)
        print('current bank ', self.audio.seq.bank)
        print(self.audio.seq.get_props_of_sequences())

    def get_info(self):
        # CUSTOM DEPS
        seq = self.audio.seq
        print('\nstatistics')
        self.audio.seq.get_statistics()
        print(self.audio.seq.statistics)
        self.get_info_bank(SOURCE_BANK)
        # seq.libseq.selectPattern(100)
        self.get_info_bank(DEST_BANK)
        print('selected pattern ', self.audio.seq.libseq.getPatternIndex())
        print(seq.pattern.info)
        print(seq.pattern.notes)

    def play(self):
        logger.info(f'playing {SOURCE_BANK}, 0')
        self.audio.seq.libseq.togglePlayState(SOURCE_BANK, 0)


class ZynPhraseConverter:
    def __init__(self, debug=False, silent=False) -> None:
        self.debug = debug
        self.base = ZynBase(debug=debug, silent=silent)

    def initialize(self):
        self.base.initialize()
        self.seq = self.base.audio.seq
        self.load_scales_data()
        self.scale = self.seq.libseq.getScale()
        # self.set_scale(self.scale)
        self.set_scale(0)
        self.base.populate_pattern(1, 0)
        self.base.get_info()
        self.base.play()

    def set_scale(self, scale=0):
        if scale > 0:
            self.seq.libseq.setScale(scale)
            self.scale = scale
        self.scale_degrees = self.scales[self.scale]['scale']

    def load_scales_data(self):
        data = []
        try:
            with open(CONFIG_ROOT + "/scales.json") as json_file:
                data = json.load(json_file)
        except:
            logger.warning("Unable to open scales.json")
        res = []
        for scale in data:
            res.append(scale['name'])
        self.scales = data
        return res

    def transpose_midi_notes(
        self, notes, interval, key_tonic):
        sd = self.scale_degrees
        # Transpose each MIDI note based on the key-aware logic
        transposed_notes = [(note + interval - key_tonic) % 12 + key_tonic for note in notes]

        # Ensure the transposed notes stay within the key scale
        return [note + (sd.index(note % 12) - sd.index(
            key_tonic % 12)) for note in transposed_notes]

    def convert(self):
        pass

    def test(self):
        original_notes = [60, 64, 65, 67]  # MIDI notes for C major chord
        original_tonic = 60  # MIDI note for C
        self.seq.libseq.playNote(60, 80, 3, 10000)
        self.seq.libseq.setScale(1)
        print("Original Notes:", original_notes)
        for x in range(0, 12):
            if x == 4:
                self.seq.libseq.playNote(56, 80, 3, 10000)
            transposed_notes = self.transpose_midi_notes(
                original_notes, x, original_tonic)
            print("Transposed Notes:", transposed_notes)
            for note in transposed_notes:
                self.seq.libseq.playNote(note, 80, 2, 1)
                time.sleep(0.2)
        
    def stop(self):
        self.base.audio.stop()


zyn = ZynPhraseConverter()
zyn.initialize()
zyn.test()

try:
    time.sleep(8000)
except KeyboardInterrupt:
    zyn.stop()
