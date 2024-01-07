
class Note:
    NOTES = ["C", "C#", "D", "D#", "E",
             "F", "F#", "G", "G#", "A", "A#", "B"]
    OFFNOTE = 'OFF'
    EMPTY = '---'

    def __init__(self, midi_note=0, velocity=0, duration=0) -> None:
        self.midi = midi_note
        self.velocity = velocity
        self.duration = duration

    def __repr__(self) -> str:
        return f'[{Note.get_string(self.midi)}, ' \
            f'{self.velocity}, {self.duration}]'

    @property
    def values(self):
        return [self.midi, self.velocity, self.duration]

    @classmethod
    def get_string(cls, code):
        code = int(code)
        if code == -1:
            return cls.OFFNOTE
        if code < 12:
            return cls.EMPTY
        code = code
        octave = int(code / 12)
        note = Note.NOTES[code % 12]
        sep = '-' if not note.endswith('#') else ''
        return f'{note}{sep}{octave}'

    @classmethod
    def get_midi(cls, note):
        if note == cls.OFFNOTE:
            return -1
        octave = note[-1]
        note = note[:-1].strip('-')
        code = int(octave) * 12 + Note.NOTES.index(note)
        return code


class TrackerPattern:
    def __init__(self, line_number=0, notes=[]) -> None:
        self._notes = {}
        self.line_number = line_number
        self.duration_measure = 1
        if line_number > 0 and notes:
            self.add_notes(notes)
            self.calculate_durations()

    def __repr__(self) -> str:
        return []

    def add_notes(self, notes):
        self._notes = {}
        polyphony = self.get_polyphony_level(notes)
        for step in range(self.line_number):
            self._notes[step] = [None] * polyphony
            if step in notes:
                for num, note in enumerate(notes[step]):
                    self._notes[step][num] = note

    @property
    def notes(self):
        return self._notes

    def get_polyphony_level(self, notes):
        return max([len(notes) for step, notes in notes.items()])

    def get_note(self, line, col):
        return self._notes[line, col]

    def set_note(self, line, col, note):
        self._notes[line, col] = note

    def calculate_durations(self):
        polyphony = len(self._notes[0])
        for column in range(polyphony):
            last_step = 0
            last_note = Note()
            for step in range(self.line_number):
                cell = self._notes[step][column]
                if cell:
                    last_note.duration = step - last_step
                    last_note = cell
                    last_step = step
            last_note.duration = step - last_step + 1

    def calculate_duration_for(self, line, col):
        note = self.get_note(line, col)
        for step in range(line + 1, self.line_number):
            cell = self._notes[step][col]
            if cell:
                note.duration = step - line

    def get_sequencer_stream(self):
        lines = []
        for step in range(self.line_number):
            if any(self._notes[step]):
                for note in self._notes[step]:
                    if note is not None and note.midi != -1:
                        l = [step, note.midi,
                             note.velocity,
                             note.duration / self.duration_measure]
                        lines.append(l)
        return lines


class TrackerPhrase:
    def __init__(self, **kwargs) -> None:
        self.name = kwargs['name']
        self.preset = kwargs['preset']
        self.lpb = kwargs['lpb']
        self.line_nr = int(kwargs['#lines'])
        self._notes = []
        self.add_notes(kwargs['notes'])

    def add_notes(self, notes):
        self._notes = TrackerPattern(self.line_nr, notes)

    @property
    def pattern(self):
        return self._notes

    @property
    def notes(self):
        return self._notes.notes


class TrackerGroup:
    def __init__(self, name, phrases) -> None:
        self.name = name
        self.phrases = []
        self.add_phrases(phrases)

    def add_phrases(self, phrases):
        for phrase in phrases:
            self.phrases.append(TrackerPhrase(**phrase))


class TrackerProject:
    def __init__(self, info={}, groups=[]) -> None:
        self.info = info
        if type(groups) is not list:
            raise TypeError
        self._groups = []
        self.add_info(info)
        self.add_groups(groups)

    def add_info(self, info):
        self.info = info

    def add_groups(self, groups):
        for group in groups:
            self._groups.append(TrackerGroup(**group))

    def get_groups(self):
        return self._groups

    def get_group(self, number):
        return self._groups[number]

    def get_total_phrases(self):
        return len([phrase for group in self._groups
                    for phrase in group.phrases])

    def get_transposable_phrases(self):
        return len([group for group in self._groups
                    if group.name.startswith('*')])
