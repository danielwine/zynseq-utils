import os
from os.path import dirname, realpath, exists,  isfile, join, splitext 
from core.config import PATH_ZSS, PATH_XRNS
from core.io.os import OSManager

def guess_engine():
    ret, err = OSManager().get_process_id('renoise')
    return 'renoise' if ret else 'linuxsampler'

def get_files(path, ext, starts_with=False):
    if not path or not ext:
        return False
    files = []
    if not exists(path):
        return files
    for f in os.listdir(path):
        if isfile(join(path, f)) and splitext(f)[1] == '.' + ext:
            if starts_with and f.startswith(starts_with) \
                    or not starts_with:
                files.append(f)
    files.sort()
    return files

def get_first_file(path, ext, starts_with):
    files = get_files(path, ext, starts_with)
    return files[0] if files else ''


def trim_extension(file_name):
    for ext in ['.xrns', '.zss']:
        if file_name.endswith(ext):
            file_name = file_name[:0-len(ext)]
    return file_name

def get_context():
    zynthian_root = os.environ.get('ZYNTHIAN_DIR') or ''
    zynthian_path = zynthian_root + '/zynthian-ui/zynlibs/zynseq'
    build_path = '/build/libzynseq.so'
    env = os.environ.get('ZYNSEQ_PATH')
    local_path = env if env else dirname(realpath(__name__))
    zynthian_full_path = zynthian_path + build_path
    local_full_path = local_path + '/core/lib/zynseq/zynseq' + build_path
    if exists(zynthian_full_path):
        print('exists')
        return {
            'zynthian': True,
            'path_lib': zynthian_path,
            'path_snapshot': zynthian_root
            + '/zynthian-my-data/snapshots/000',
            'path_xrns': '',
            'audio': 'zynmidirouter'
        }
    if exists(local_full_path):
        return {
            'zynthian': False,
            'path_lib': local_path,
            'path_snapshot': PATH_ZSS,
            'path_xrns': PATH_XRNS,
            'audio': guess_engine()
        }
