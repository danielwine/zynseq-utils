import sys
import time
import argparse
import traceback
import pysftp
import paramiko
import logging
from os import listdir
from os.path import basename, splitext
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import core.config as config
from core.io.stdout import StdOut
from core.io.files import get_context, trim_extension
from core.io.logger import SimpleColorFormatter
from core.cli.colors import Col
from core.lib.xrns import XRNS
from core.audio.sequencer import Sequencer

logger = logging.getLogger(__name__)
logger.propagate = False
ch = logging.StreamHandler()
ch.setFormatter(SimpleColorFormatter())
logger.addHandler(ch)
logger.setLevel(logging.INFO)
debug = False


class Connection(pysftp.Connection):
    def __init__(self):
        super().__init__(host=config.SFTP_HOST, username=config.SFTP_USER,
                         password=config.SFTP_PASSWORD)

    def upload(self, src_path, dest_path, snapshot_folder):
        folder = config.PATH_ZSS_REMOTE + snapshot_folder
        if not self.exists(folder):
            logger.info(f"Specified snapshot folder '{snapshot_folder}' " +
                        f"does not exist. Creating.")
            self.mkdir(folder)
        try:
            self.put(src_path, dest_path, preserve_mtime=True)
        except FileNotFoundError:
            logger.error(f'Bad target "{dest_path}"')
            return False
        logger.warning(
            f'ZSS uploaded to snapshot folder {snapshot_folder}.')

    def get_remote_file(self, src_path, dest_path):
        if self.exists(src_path):
            self.get(src_path, dest_path)
            return True
        else:
            return False


class WatchDog:
    def __init__(self):
        self.observer = Observer()

    def run(self, callback):
        event_handler = FileChangeHandler(callback)
        self.observer.schedule(
            event_handler, config.PATH_XRNS, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Watchdog stopped.")

        self.observer.join()


class FileChangeHandler(FileSystemEventHandler):

    def __init__(self, callback) -> None:
        self.callback = callback

    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            if event.src_path.endswith('.xrns.tmp'):
                name = splitext(basename(event.src_path))[0]
                current_time = datetime.now().strftime("%H:%M:%S")
                logger.info(f'Project {name} was modified at {current_time}')
                time.sleep(1.5)
                self.callback(name, config.SFTP_DEFAULT_SNAPSHOT)


class App:
    def __init__(self) -> None:
        self.context = get_context()
        self.connected = False
        self.stdout = StdOut()
        self.stdout.mute()
        self.seq = Sequencer()
        self.stdout.unmute()
        self.xrns = XRNS()

    def parse_args(self, args=None):
        parser = argparse.ArgumentParser()
        print('Renoise-Zynthian 🎵 bridge by danielwine')
        logger.info('zynseq library (c) by Brian Walton')
        print()
        parser.add_argument('filename', type=str, nargs='?')
        parser.add_argument('--list', action='store_true',
                            help='Lists projects in standard library')
        parser.add_argument('--upload', dest='upload_path', metavar="PATH",
                            type=str,
                            help='Specify remote snapshot subfolder')
        parser.add_argument('--debug', action='store_true',
                            help='Switch debug mode on (unhides stdout)')
        if len(sys.argv) == 1:
            return False
        return parser.parse_args(args)

    def list_files(self):
        logger.info('Available projects in standard path: ')
        files = [file for file in listdir(config.PATH_XRNS) if
                 file.endswith('.xrns')]
        files.sort()
        for file in files:
            logger.info(' ', file)

    def connect(self):
        success = False
        reconnect_delay = 5
        while not success:
            try:
                err = f'Your zynthian cannot be reached at {config.SFTP_HOST}'
                self.conn = Connection()
                success = True
            except pysftp.exceptions.ConnectionException:
                logger.error(f'Timeout. {err}')
            except paramiko.ssh_exception.SSHException:
                logger.error(f'No route to host. {err}')
            if not success:
                time.sleep(reconnect_delay)
                logger.info(f'Reconnecting in {reconnect_delay} seconds.')
        print()
        logger.warning(f'Connection to zynthian established.')
        self.connected = True

    def disconnect(self):
        self.conn.close()
        self.connected = False
        logger.info('Disconnected from zynthian.')

    def load(self, file):
        try:
            self.xrns.load(file)
        except FileNotFoundError:
            try:
                self.xrns.load(file, standard_path=False)
            except FileNotFoundError:
                self.leave(file)

        if not debug:
            self.stdout.mute()
        self.seq.initialize(self.context['path_lib'], scan=False, debug=debug)
        try:
            self.seq.import_project(file, self.xrns.project)
        except Exception as e:
            self.stdout.unmute()
            logger.critical('Unable to import project. An error occured.')
            print(traceback.format_exception_only(e)[0], end='')
            exit()
        self.stdout.unmute()

    def update(self, local_path, remote_path, snapshot_folder=''):
        success = False
        while not success:
            if self.conn.get_remote_file(remote_path, local_path):
                logger.info(f'Project found on server. Updating...')
                self.seq.load_snapshot(local_path, load_sequence=False)
            self.seq.save_file(file_path=local_path)
            try:
                self.conn.upload(local_path, remote_path, snapshot_folder)
                success = True
            except OSError:
                logger.error('Connection lost.')
                self.connect()

    def print_statistics(self):
        name = ' ' + self.xrns.source.project_name if self.p_args else ''
        logger.info(f'Project{name} converted.')
        project = self.xrns.project
        logger.info(f'  total groups: {len(project.get_groups())}')
        logger.info(f'  total sequences: {project.get_total_phrases()}')
        logger.info(f'  transposed sequences: ' +
                    f'{project.get_transposable_phrases() * 16}')

    def leave(self, filename):
        logger.error(f'Missing file: {filename}')
        self.list_files()
        exit()

    def process(self, filename, upload_path):
        self.load(filename)
        self.print_statistics()

        local_path = self.xrns.get_original_path() + '.zss'
        remote_path = f'{config.PATH_ZSS_REMOTE}{upload_path}'
        remote_path += f'/{trim_extension(local_path.split("/")[-1])}.zss'

        self.seq.save_file(file_path=local_path)
        if upload_path is not None:
            if not self.connected:
                self.connect()
            self.update(local_path, remote_path,
                        snapshot_folder=upload_path)

    def run(self):
        global debug
        self.p_args = self.parse_args()
        if self.p_args and self.p_args.debug:
            logger.setLevel(logging.DEBUG)
            debug = True
        if not self.p_args or (not self.p_args.filename and self.p_args.debug):
            print(f'{Col.CYAN}Type -h to see argument options.')
            print(f'No arguments specified. Entering watch mode.')
            self.connect()
            print(f'Watching for changes in {config.PATH_XRNS}...')
            watch = WatchDog()
            watch.run(self.process)
        else:
            self.process(self.p_args.filename, self.p_args.upload_path)
        self.disconnect()


if __name__ == '__main__':
    app = App()
    app.run()
