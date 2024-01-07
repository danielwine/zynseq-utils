from os import listdir, system, getlogin
from abc import ABC, abstractmethod
from os.path import exists,  isfile, join, splitext
from psutil import net_if_addrs
from subprocess import Popen, PIPE
from core.io.logger import LoggerFactory
from .utils import *

logger, lf = LoggerFactory(__name__) 


class OSManager():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            if is_linux():
                cls._instance = OSManagerLinux()
            if is_windows():
                cls._instance = OSManagerWindows()
        return cls._instance


class OSManagerBase(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def is_embedded(self):
        pass

    @abstractmethod
    def is_running(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def reboot(self):
        pass

    def get_files(self, path, ext, starts_with=False):
        if not path or not ext:
            return False
        files = []
        if not exists(path):
            return []
        for f in listdir(path):
            if isfile(join(path, f)) and splitext(f)[1] == '.' + ext:
                if starts_with and f.startswith(starts_with) \
                        or not starts_with:
                    files.append(f)
        files.sort()
        return files

    def execute(self, name, params=[]):
        return Popen([name, *params], stdin=PIPE, stdout=PIPE)

    def execute_pipe(self, app, params=[]):
        proc = Popen([app, params], stdout=PIPE)
        ret, err = proc.communicate()
        return ret.decode('utf-8').strip(), err


class OSManagerLinux(OSManagerBase):
    @property
    def is_embedded(self):
        arch, err = self.execute_pipe('uname', '-m')
        return True if (arch == 'armv7l' or arch == 'aarch64') else False

    def is_running(self, process_name):
        ret, err = self.execute_pipe('pgrep', process_name)
        code = ret.split('\n')[0]
        return True if code and code > 0 else False, err
    
    def get_process_id(self, name):
        return self.execute_pipe('pgrep', name)

    def get_service_status(self, service_name):
        ret, err = self.execute_pipe('systemctl', f'status {service_name}')
        data = ret.split('\n')
        return data, err

    def get_file(self, name):
        if exists(name):
            with open(name, 'r') as fl:
                return fl.read()
        return False
    
    def get_folders_with_data(self, path):
        folders = []
        for f in listdir(path):
            if not isfile(f):
                if len(listdir(join(path, f))) > 0:
                    folders.append(f)
        return folders

    def shutdown(self):
        system('sudo shutdown now')

    def reboot(self):
        system('sudo reboot now')

    def play_audio(self, name):
        proc = Popen(['aplay', name], stdout=PIPE)

    def run_script(self, name):
        system(f'bash {name}')

    @property
    def local_ip_address(self):
        for if_name, if_addresses in net_if_addrs().items():
            for address in if_addresses:
                if if_name.startswith('ku'):
                    if str(address.family) == 'AddressFamily.AF_INET':
                        return address.address
        return None

    def get_process_id(self, name):
        return self.execute_pipe('pgrep', name)

    def kill(self, pid):
        if isinstance(pid, int):
            pid = str(pid)
        if isinstance(pid, str):
            return self.execute_pipe('kill', pid)
        elif type(pid) is list:
            for item in pid:
                if item:
                    self.execute_pipe('kill', item)


class OSManagerWindows(OSManagerBase):
    @property
    def is_embedded(self):
        return False
    

os = OSManager()
