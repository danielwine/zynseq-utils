import time
from math import sqrt
from os.path import dirname, realpath
from logging import DEBUG, INFO
from core.config import (
    auto_bank, minimum_rows, maximum_rows,
    trigger_channel, trigger_start_note, PATH_ZSS)
from core.io.utils import trim_extension
from core.io.logger import LoggerFactory
from core.lib.tracker import Note, TrackerPattern
from core.lib.zss import SnapshotManager
from core.lib.zynseq.zynseq.zynseq import zynseq
from core.audio.generator import Generator

basepath = dirname(realpath(__file__))
logger, lf = LoggerFactory(__name__)


class Sequencer(zynseq, SnapshotManager):
    def __init__(self, path_lib = None):
        super().__init__(path=path_lib)
        self.filepath = ""
        self.file = ""

    def initialize(self, scan=True, debug=False):
        logger.setLevel(DEBUG if debug else INFO)
        self.pattern = PatternManager(self.libseq)
        if scan:
            self.get_statistics()
        self.pattern.select(self.libseq.getPatternAt(1, 0, 0, 0))

    def import_project(self, file_name, tracker_project):
        self.tracker = tracker_project
        info = self.tracker.info
        self.load('')
        self.libseq.setTempo(int(info['bpm']))
        self.file = file_name

        bank = 1
        self.select_bank(bank)
        self._import_groups(bank)
        self.get_statistics()

    def _get_tracker_sequences(self):
        return len([phrase for group in self.tracker.get_groups()
                    for phrase in group.phrases if
                    not group.name.startswith('*')])

    def _expand_bank(self, bank, sequences):
        current_sequences = self.libseq.getSequencesInBank(bank)
        new_sequences = current_sequences
        sqrts = sqrt(sequences)
        if sequences > current_sequences:
            rows = int(sqrts) + 1
            rows = rows if rows <= maximum_rows else maximum_rows
            rows = rows if rows >= minimum_rows else minimum_rows
            new_sequences = rows * rows
            self.libseq.setSequencesInBank(bank, new_sequences)
        print(new_sequences, sqrts, int(sqrts), sequences, current_sequences)
        return new_sequences

    def _import_sequence(
            self, bank, sequence, name, channel, phrase_obj, transpose):
        self.set_sequence_name(bank, sequence, name)
        notes = phrase_obj.pattern.get_sequencer_stream()
        pattern_nr = self.libseq.getPattern(bank, sequence, 0, 0)
        self.pattern.select(pattern_nr)
        self.pattern.expand(phrase_obj.line_nr)
        self.pattern.add_notes(notes, transpose)
        self.libseq.setChannel(bank, sequence, 0, channel)
        self.libseq.setGroup(bank, sequence, channel)
        if transpose:
            self.libseq.setTriggerNote(
                bank, sequence, trigger_start_note + sequence)

    def _import_groups(self, bank):
        sequences = self._get_tracker_sequences()
        sequence_nr = 0
        sequences_in_bank = self._expand_bank(bank, sequences)
        for group_nr, group in enumerate(self.tracker.get_groups()):
            if group.name.startswith('*'):
                self.libseq.setTriggerChannel(trigger_channel)
                for phrase_nr in range(16):
                    note = trigger_start_note + int(phrase_nr)
                    name = f'{group.name} {Note.get_string(note)}'
                    self._import_sequence(
                        auto_bank, phrase_nr, name, group_nr,
                        group.phrases[0], phrase_nr)
            else:
                for phrase_nr, phrase in enumerate(group.phrases):
                    print(sequence_nr, sequences_in_bank)
                    if sequence_nr + 1 > sequences_in_bank:
                        bank += 1
                        sequences = sequences - sequence_nr + 1
                        sequences_in_bank = self._expand_bank(
                            bank, sequences)
                        sequence_nr = 0
                    name = f'{group.name} {phrase_nr}'
                    self._import_sequence(
                        bank, sequence_nr, name, group_nr, phrase, 0)
                    sequence_nr += 1

    def get_info_all(self):
        return {
            'sequences': self.get_props_of_sequences(),
            'pattern_info': self.pattern.info,
            'pattern': self.pattern.notes
        }

    def get_statistics(self):
        ls = self.libseq
        self.bpm = ls.getTempo()
        self.bpb = ls.getBeatsPerBar()
        self.banks = {}
        self.patterns = {}
        for bnum in range(1, 255):
            seqs = ls.getSequencesInBank(bnum)
            if seqs > 0:
                self.banks[bnum] = False
                for snum in range(seqs):
                    if ls.getPattern(bnum, snum, 0, 0) >= 0:
                        self.banks[bnum] = True
                        for tnum in range(ls.getTracksInSequence(bnum, snum)):
                            pids = self.get_pids_in_track(bnum, snum, tnum)
                            for pid, isEmpty in pids.items():
                                self.patterns[pid] = isEmpty

    def get_pids_in_track(self, bnum, snum, tnum):
        ''' iterates over the track and collects pattern indices '''
        location = 0
        patterns = {}
        pattern_cnt = 0
        total_patterns = self.libseq.getPatternsInTrack(bnum, snum, tnum)
        while pattern_cnt != total_patterns:
            ret = self.libseq.getPattern(bnum, snum, tnum, location)
            if ret != '-1':
                self.libseq.selectPattern(ret)
                pattern_cnt += 1
                patterns[ret] = True if self.libseq.getLastStep() > \
                    -1 else False
            location += 1
        return patterns

    def get_value(self, expression, default):
        if hasattr(self, expression):
            return getattr(self, expression)
        else:
            return default

    @property
    def pattern_count(self):
        return len(
            {key: value for key, value in self.patterns.items() if value})

    @property
    def statistics(self):
        return {
            'file': None if not self.file else self.file,
            'BPM': self.get_value('bpm', 120.0),
            'BPB': self.get_value('bpb', 4),
            'banks': len(self.get_value('banks', {})),
            'patterns': self.get_value('pattern_count', 0)
        }

    def list_banks(self):
        return self.banks

    @property
    def pattern_info(self):
        return self.pattern.info

    def get_props_of_sequences(self):
        seqs = {}
        if not hasattr(self, 'libseq'):
            return
        for el in range(self.libseq.getSequencesInBank(self.bank)):
            seqs[el] = self.get_props_of_sequence(el)
        return seqs

    def get_props_of_sequence(self, seq_num):
        return {
            'name': self.get_sequence_name(self.bank, seq_num),
            'group': self.libseq.getGroup(self.bank, int(seq_num)),
            'trigger': self.libseq.getTriggerNote(self.bank, seq_num)
        }

    @property
    def sequence_names(self):
        return {key: value['name']
                for key, value in self.get_props_of_sequences().items()}

    def select_pattern(self, pattern):
        return self.pattern.select(pattern)

    def list_patterns(self):
        return self.patterns

    def get_notes_in_pattern(self):
        return self.pattern.notes
    
    def play_note(self, note, channel, delay):
        self.libseq.playNote(note, 110, channel, 200)
        time.sleep(delay)

    def test_midi(self, print_fn=print):
        for channel in range(0, 4):
            print_fn(f'Testing channnel #{channel + 1}')
            self.play_note(62, channel, 0.2)
            self.play_note(69, channel, 0.2)
            self.play_note(74, channel, 0.4)
        print_fn(f'Testing drum channnel #10')
        self.play_note(40, 9, 0.2)
        self.play_note(45, 9, 0.2)

    def load_file(self, path, filename, **args):
        self.file = filename.split(".")[0]
        self.extension = filename.split(".")[1]
        self.filepath = path + "/" + filename
        return self.load_snapshot(self.filepath, **args)

    def save_file(self, file_path=None):
        file_path = self.filepath if file_path is None else file_path
        if file_path == '':
            file_path = f'{PATH_ZSS}/{trim_extension(self.file)}.zss'
        if not hasattr(self, 'snapshot'):
            self.create_snapshot_from_template(file_path)
        else:
            self.save_snapshot(file_path=file_path)

    def start(self):
        pass

    def stop(self):
        self.libseq.setPlayState(0, 0)
        self.libseq.setPlayState(1, 0)


class PatternManager(Generator):
    def __init__(self, libseq) -> None:
        super().__init__(libseq)
        self.id = 0
        self.tonic = 0

    def select(self, pattern):
        pattern = int(pattern)
        self.id = pattern
        self.libseq.selectPattern(pattern)

    def import_pattern(self, pattern):
        if not isinstance(pattern, TrackerPattern):
            return False
        stream = pattern.get_sequencer_stream()
        self.notes = stream

    @property
    def info(self):
        ls = self.libseq
        return {
            'steps': ls.getSteps(),
            'beats': ls.getBeatsInPattern(),
            'spb': ls.getStepsPerBeat(),
            'cps': ls.getClocksPerStep(),
            'length': ls. getPatternLength(ls.getPatternIndex()),
            'inprest': ls.getInputRest(),
            'scale': ls.getScale(),
            'tonic': ls.getTonic(),
            'modified': ls.isPatternModified(),
            'refnote': ls.getRefNote(),
            'laststep': ls.getLastStep(),
            'playhead': ls.getPatternPlayhead()
        }

    @property
    def notes(self):
        notes = []
        for step in range(self.libseq.getSteps()):
            isStepEmpty = True
            for note in range(0, 127):
                vel = self.libseq.getNoteVelocity(step, note)
                if vel:
                    notes.append([step, note, vel, self.libseq
                                  .getNoteDuration(step, note)])
                    isStepEmpty = False
            if isStepEmpty:
                notes.append([step])
        return notes

    @notes.setter
    def notes(self, note_list):
        self.add_notes(note_list, transpose=0)

    def add_notes(self, note_list, transpose):
        for index in range(len(note_list)):
            if transpose == 0:
                self.libseq.addNote(*note_list[index])
            else:
                note = note_list[index]
                shift = self.get_shift_value(note[1], transpose, self.tonic)
                self.libseq.addNote(
                    note[0], note[1] + shift, note[2], note[3])

    def expand(self, line_nr):
        if self.libseq.getSteps() < line_nr:
            multiplier = int(line_nr / self.libseq.getSteps())
            self.libseq.setBeatsInPattern(
                self.libseq.getBeatsInPattern() * multiplier)

    def get_shift_value(self, midi_note, transpose, tonic):
        # TODO: the smart transpose functionality has yet to be implemented.
        return transpose
