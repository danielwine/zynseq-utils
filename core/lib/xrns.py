from os.path import isfile, isdir, exists, abspath, relpath, join, splitext
from os import walk, mkdir
import zipfile
import xml.etree.ElementTree as ET
from core.config import PATH_XRNS, PATH_PROJECTS
from core.model.xrns import PROPS
from core.lib.tracker import Note, TrackerProject
from core.io.utils import trim_extension


class XRNSFile:
    ''' Class for XRNS file read & write operations '''

    def __init__(self) -> None:
        self.error = False
        self.source_path = ''
        self.project_path = ''
        self.sample_paths = []

    def get_path(self, file_name, standard_path=True):
        self.source_path = PATH_XRNS + '/' + \
            file_name if standard_path else file_name
        self.project_name = splitext(file_name)[0].split('/')[-1]
        self.project_path = PATH_PROJECTS + '/' + self.project_name

    def load(self, file_name, standard_path=True):
        self.get_path(file_name, standard_path)
        if not exists(PATH_PROJECTS):
            mkdir(PATH_PROJECTS)
        if not exists(self.project_path):
            mkdir(self.project_path)
        full_name = self.source_path
        if isfile(full_name):
            with zipfile.ZipFile(full_name, 'r') as zip_ref:
                zip_ref.extractall(self.project_path)
        else:
            raise FileNotFoundError('Missing XRNS: ' + self.source_path)
        files = ['/Song.xml', '/Instrument.xml']
        for file_name in files:
            fpath = self.project_path + file_name
            if isfile(fpath):
                return ET.parse(fpath)
        spath = self.project_path + '/SampleData'
        if isdir(spath):
            for item in walk(spath):
                self.sample_paths.append(item)

    def save(self, file_name, tree):
        if not isinstance(tree, ET.ElementTree):
            return False
        tree.write(self.project_path + '/Song.xml')
        zipdat = zipfile.ZipFile(
            self.source_path, 'w', zipfile.ZIP_DEFLATED)
        self._zipall(zipdat, self.project_path)

    def _zipall(self, zipdat, folder):
        ''' compress project to a zip file. not thoroughly tested yet. '''
        folder = abspath(folder)
        for foldername, subfolders, filenames in walk(folder):
            if foldername == folder:
                archive_folder_name = ''
            else:
                archive_folder_name = relpath(foldername, folder)
                zipdat.write(foldername, arcname=archive_folder_name)
            for filename in filenames:
                zipdat.write(
                    join(foldername, filename),
                    arcname=join(archive_folder_name, filename))
        zipdat.close()


class Properties:
    def __init__(self, data, props):
        if isinstance(data, ET.Element):
            self.data = {item.tag: item.text for item in data}
            self.props = props
            self.values = {}
            self.get_all()

    def get_all(self):
        for name, acronym in self.props.items():
            if name in self.data:
                self.values[acronym] = self.data[name]


class XRNS:
    ''' Class to extract / inject relevant data from / to an XRNS file '''

    def __init__(self) -> None:
        super().__init__()
        self.source = XRNSFile()
        self.tree = ET.ElementTree()
        self.global_info = {}

    def load(self, filename, standard_path=True):
        self.project = TrackerProject()
        self.tree = self.source.load(filename, standard_path)
        self.root = self.tree.getroot()
        self.get_data()
        if self.tree is None:
            return False
        return True

    def get_original_path(self):
        return trim_extension(self.source.source_path)

    def get_data(self):
        try:
            self.get_global_info()
            phrases = self.get_phrases()
        except KeyError as e:
            raise KeyError(f'Invalid XRNS format. {e}')
        self.project.add_info(self.global_info.values)
        self.project.add_groups(phrases)

    def get_global_info(self):
        if self.root.tag == 'RenoiseSong':
            self.global_info = Properties(
                self.root.find('GlobalSongData'),
                PROPS['global'])

    def parse_phrase(self, phrase):

        def add_note(notecolumn):
            note = Note()
            if len(notecolumn) == 0:
                # note.midi = None
                cnotes.append(None)
                return
            else:
                noteItem = notecolumn.find('Note')
                if noteItem is not None:
                    note.midi = Note.get_midi(noteItem.text)
                    vel = notecolumn.find('Volume')
                    note.velocity = int(
                        vel.text, 16) if vel is not None else 80
                    cnotes.append(note)

        try:
            notes = {}
            for lines in phrase.iter('Lines'):
                for line in lines.iter('Line'):
                    step = line.attrib['index']
                    for idx, column in enumerate(line.iter('NoteColumns')):
                        cnotes = []
                        for notecolumn in line.iter('NoteColumn'):
                            add_note(notecolumn)
                    notes[int(step)] = cnotes
        except AttributeError as e:
            raise AttributeError(f'Invalid XRNS format. {e}')
        return notes

    def parse_phrase_generator(self, base):
        phrases_in_instrument = []
        for phrases in base.findall('PhraseGenerator'):
            for phrase in phrases.iter('Phrase'):
                phrase_info = Properties(
                    phrase, PROPS['phrase']
                )
                notes = self.parse_phrase(phrase)
                # print([note.midi for note in notes.values()])
                phrases_in_instrument.append({
                    **phrase_info.values,
                    'notes': notes})
        return phrases_in_instrument

    def get_phrases(self):
        if self.root.tag == 'RenoiseInstrument':
            self.parse_phrase_generator(self.root)
            return
        for instruments in self.root.iter('Instruments'):
            phrases = []
            for instrument in instruments.iter('Instrument'):
                try:
                    instrument_name = instrument.find('Name').text
                except:
                    instrument_name = ''
                if instrument_name:
                    phrases.append({
                        'name': instrument_name,
                        'phrases':
                            self.parse_phrase_generator(instrument)
                    })
        return phrases
