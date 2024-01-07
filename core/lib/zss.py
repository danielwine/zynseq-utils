import shutil
import base64
from os.path import splitext, exists
from json import JSONDecoder, JSONEncoder
from core.config import create_backup, vertical_zoom, PATH_BASE, PATH_DATA
import logging

logger = logging.getLogger(__name__)


class SnapshotManager:
    def __init__(self):
        self.snapshot = {}

    def load_snapshot(self, file_path, load_sequence=True):
        self.fpath = file_path
        try:
            with open(file_path, "r") as fh:
                json = fh.read()
                logger.debug(f"Loading snapshot {file_path}")
                logger.debug(f"=> {json}")

        except Exception as e:
            logger.error("Can't load snapshot '%s': %s" % (file_path, e))
            return False

        try:
            snapshot = JSONDecoder().decode(json)
            self.snapshot = snapshot
            if "zynseq_riff_b64" in snapshot:
                b64_bytes = snapshot["zynseq_riff_b64"].encode("utf-8")
                binary_riff_data = base64.decodebytes(b64_bytes)
                if not load_sequence:
                    return True
            else:
                return False
            self.restore_riff_data(binary_riff_data)
            return True

        except Exception as e:
            logger.exception("Invalid snapshot: %s" % e)
            return False

    def create_snapshot_from_template(self, file_path=None):
        self.load_snapshot(PATH_BASE + '/res/base.zss', load_sequence=False)
        self.save_snapshot(file_path)

    def get_standard_path(file_name):
        return PATH_DATA + '/zss/' + file_name

    def save_snapshot(self, file_path=None):
        file_path = self.fpath if file_path is None else file_path
        if exists(file_path) and create_backup:
            shutil.copy2(file_path, splitext(file_path)[0] + '.bak')
        try:
            self.libseq.setVerticalZoom(vertical_zoom)
            riff_data = self.get_riff_data()
            self.snapshot["zynseq_riff_b64"] = base64.encodebytes(
                riff_data).decode("utf-8").replace('\n', '')

            with open(file_path, "w") as fh:
                data = JSONEncoder().encode(self.snapshot)
                fh.write(data)

        except Exception as e:
            logger.error("Can't write snapshot '%s': %s" % (file_path, e))
            return False
