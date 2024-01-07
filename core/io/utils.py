import platform
info = platform.uname()
sys = info.system.lower()


def is_linux():
    return 'linux' in sys

def is_windows():
    return 'windows' in sys

def is_android():
    return 'android' in sys

def trim_extension(file_name):
    for ext in ['.xrns', '.zss']:
        if file_name.endswith(ext):
            file_name = file_name[:0-len(ext)]
    return file_name
