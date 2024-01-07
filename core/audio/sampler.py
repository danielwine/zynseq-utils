# ******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Engine (zynthian_engine_linuxsampler)
#
# zynthian_engine implementation for Linux Sampler
#
# Copyright (C) 2015-2016 Fernando Moyano <jofemodo@zynthian.org>
#
# ******************************************************************************
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
# ******************************************************************************

import os
import re
import glob
import socket
import shutil
from time import sleep
from subprocess import check_output
from collections import OrderedDict
from core.config import PATH_SAMPLES, PATH_SAMPLES_MY
from core.io.logger import LoggerFactory

logger, lf = LoggerFactory(__name__)


class zyngine_lscp_error(Exception):
    pass


class zyngine_lscp_warning(Exception):
    pass

# ------------------------------------------------------------------------------
# Linuxsampler Engine Class
# ------------------------------------------------------------------------------


class LinuxSampler:

    # ---------------------------------------------------------------------------
    # Controllers
    # ---------------------------------------------------------------------------

    # LS Hardcoded MIDI Controllers
    _ctrls = [
        ['modulation wheel', 1, 0],
        ['volume', 7, 96],
        ['pan', 10, 64],
        ['expression', 11, 127],

        ['sustain', 64, 'off', ['off', 'on']],
        ['sostenuto', 66, 'off', ['off', 'on']],
        ['legato', 68, 'off', ['off', 'on']],
        ['breath', 2, 127],

        ['portamento on/off', 65, 'off', ['off', 'on']],
        ['portamento time-coarse', 5, 0],
        ['portamento time-fine', 37, 0],

        # ['expr. pedal', 4, 127],
        ['filter cutoff', 74, 64],
        ['filter resonance', 71, 64],
        ['env. attack', 73, 64],
        ['env. release', 72, 64]
    ]

    # ---------------------------------------------------------------------------
    # Config variables
    # ---------------------------------------------------------------------------

    lscp_port = 8888
    lscp_v1_6_supported = False

    bank_dirs = [
        ('SFZ', PATH_SAMPLES + "/soundfonts/sfz"),
        ('GIG', PATH_SAMPLES + "/soundfonts/gig"),
        ('MySFZ', PATH_SAMPLES_MY + "/soundfonts/sfz"),
        ('MyGIG', PATH_SAMPLES_MY + "/soundfonts/gig"),
    ]

    # ---------------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------------

    def __init__(self):
        self.jackname = "LinuxSampler"

        self.sock = None
        self.command = "linuxsampler --lscp-port {}".format(self.lscp_port)
        self.command_prompt = "\nLinuxSampler initialization completed."

        self.ls_chans = {}

        self.lscp_connect()
        self.lscp_get_version()
        self.reset()

    def reset(self):
        self.ls_chans = {}
        self.ls_init()

    # ---------------------------------------------------------------------------
    # Subproccess Management & IPC
    # ---------------------------------------------------------------------------

    def lscp_connect(self):
        logger.info(lf("  connecting linuxsampler server..."))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.settimeout(1)
        i = 0
        while i < 20:
            try:
                self.sock.connect(("127.0.0.1", self.lscp_port))
                break
            except:
                sleep(0.25)
                i += 1
        return self.sock

    def lscp_get_version(self):
        sv_info = self.lscp_send_multi("GET SERVER INFO")
        if 'PROTOCOL_VERSION' in sv_info:
            match = re.match(r"(?P<major>\d+)\.(?P<minor>\d+).*",
                             sv_info['PROTOCOL_VERSION'])
            if match:
                version_major = int(match['major'])
                version_minor = int(match['minor'])
                if version_major > 1 or (version_major == 1 and version_minor >= 6):
                    self.lscp_v1_6_supported = True

    def lscp_send(self, command):
        command = command+"\r\n"
        try:
            self.sock.send(command.encode())
        except Exception as err:
            logger.error(lf("FAILED lscp_send: %s" % err))

    def lscp_get_result_index(self, result):
        parts = result.split('[')
        if len(parts) > 1:
            parts = parts[1].split(']')
            return int(parts[0])

    def lscp_send_single(self, command):
        logger.debug(lf("LSCP SEND => %s" % command))
        command = command + "\r\n"
        try:
            self.sock.send(command.encode())
            line = self.sock.recv(4096)
        except Exception as err:
            logger.error(lf("FAILED lscp_send_single(%s): %s" % (command, err)))
            return None
        line = line.decode()
        # logger.debug(lf("LSCP RECEIVE => %s" % line))
        if line[0:2] == "OK":
            result = self.lscp_get_result_index(line)
            return result
        elif line[0:3] == "ERR":
            parts = line.split(':')
            raise zyngine_lscp_error(
                "{} ({} {})".format(parts[2], parts[0], parts[1]))
        elif line[0:3] == "WRN":
            parts = line.split(':')
            raise zyngine_lscp_warning(
                "{} ({} {})".format(parts[2], parts[0], parts[1]))

    def lscp_send_multi(self, command):
        # logger.debug(lf("LSCP SEND => %s" % command))
        command = command + "\r\n"
        try:
            self.sock.send(command.encode())
            result = self.sock.recv(4096)
        except Exception as err:
            logger.error(lf("FAILED lscp_send_multi(%s): %s" % (command, err)))
            return None
        lines = result.decode().split("\r\n")
        result = OrderedDict()
        for line in lines:
            # logger.debug(lf("LSCP RECEIVE => %s" % line))
            if line[0:2] == "OK":
                result = self.lscp_get_result_index(line)
            elif line[0:3] == "ERR":
                parts = line.split(':')
                self.stop_loading()
                raise zyngine_lscp_error(
                    "{} ({} {})".format(parts[2], parts[0], parts[1]))
            elif line[0:3] == "WRN":
                parts = line.split(':')
                self.stop_loading()
                raise zyngine_lscp_warning(
                    "{} ({} {})".format(parts[2], parts[0], parts[1]))
            elif len(line) > 3:
                parts = line.split(':')
                result[parts[0]] = parts[1]
        return result

    # ---------------------------------------------------------------------------
    # MIDI Channel Management
    # ---------------------------------------------------------------------------

    def set_midi_chan(self, layer):
        if layer.ls_chan_info:
            ls_chan_id = layer.ls_chan_info['chan_id']
            try:
                self.lscp_send_single("SET CHANNEL MIDI_INPUT_CHANNEL {} {}".format(
                    ls_chan_id, layer.get_midi_chan()))
            except zyngine_lscp_error as err:
                logger.error(lf(err))
            except zyngine_lscp_warning as warn:
                logger.warning(lf(warn))

    # ---------------------------------------------------------------------------
    # Bank Management
    # ---------------------------------------------------------------------------

    def get_bank_list(self, layer=None):
        return self.get_dirlist(self.bank_dirs)

    def set_bank(self, layer, bank):
        return True

    # ---------------------------------------------------------------------------
    # Preset Management
    # ---------------------------------------------------------------------------

    @staticmethod
    def _get_preset_list(bank):
        logger.info(lf("Getting Preset List for %s" % bank[2]))
        i = 0
        preset_list = []
        preset_dpath = bank[0]
        if os.path.isdir(preset_dpath):
            exclude_sfz = re.compile(r"[MOPRSTV][1-9]?l?\.sfz")
            cmd = "find '"+preset_dpath+"' -maxdepth 3 -type f -name '*.sfz'"
            output = check_output(cmd, shell=True).decode('utf8')
            cmd = "find '"+preset_dpath+"' -maxdepth 2 -type f -name '*.gig'"
            output = output+"\n"+check_output(cmd, shell=True).decode('utf8')
            lines = output.split('\n')
            for f in lines:
                if f:
                    filehead, filetail = os.path.split(f)
                    if not exclude_sfz.fullmatch(filetail):
                        filename, filext = os.path.splitext(f)
                        filename = filename[len(preset_dpath)+1:]
                        title = filename.replace('_', ' ')
                        engine = filext[1:].lower()
                        preset_list.append(
                            [f, i, title, engine, "{}{}".format(filename, filext)])
                        i = i+1
        return preset_list

    def get_preset_list(self, bank):
        return self._get_preset_list(bank)

    def set_preset(self, layer, preset, preload=False):
        if self.ls_set_preset(layer, preset[3], preset[0]):
            layer.send_ctrl_midi_cc()
            return True
        else:
            return False

    def cmp_presets(self, preset1, preset2):
        try:
            if preset1[0] == preset2[0] and preset1[3] == preset2[3]:
                return True
            else:
                return False
        except:
            return False

    # ---------------------------------------------------------------------------
    # Specific functions
    # ---------------------------------------------------------------------------

    def ls_init(self):
        try:
            self.lscp_send_single("RESET")

            self.ls_audio_device_id = self.lscp_send_single(
                "CREATE AUDIO_OUTPUT_DEVICE JACK ACTIVE='true' CHANNELS='2' NAME='{}'".format(self.jackname))

            self.ls_midi_device_id = self.lscp_send_single(
                "CREATE MIDI_INPUT_DEVICE JACK ACTIVE='true' NAME='LinuxSampler' PORTS='1'")

            self.lscp_send_single("SET VOLUME 0.45")

        except zyngine_lscp_error as err:
            logger.error(lf(err))
        except zyngine_lscp_warning as warn:
            logger.warning(lf(warn))

    def ls_add_channel(self, layer):
        ls_chan_id = self.lscp_send_single("ADD CHANNEL")
        if ls_chan_id >= 0:
            try:
                self.lscp_send_single("SET CHANNEL AUDIO_OUTPUT_DEVICE {} {}".format(
                    ls_chan_id, self.ls_audio_device_id))
                # self.lscp_send_single("SET CHANNEL VOLUME %d 1" % ls_chan_id)

                if self.lscp_v1_6_supported:
                    self.lscp_send_single("ADD CHANNEL MIDI_INPUT {} {} 0".format(
                        ls_chan_id, self.ls_midi_device_id))
                else:
                    self.lscp_send_single("SET CHANNEL MIDI_INPUT_DEVICE {} {}".format(
                        ls_chan_id, self.ls_midi_device_id))
                    self.lscp_send_single(
                        "SET CHANNEL MIDI_INPUT_PORT {} {}".format(ls_chan_id, 0))
                    self.lscp_send_single(
                        "SET CHANNEL MIDI_INPUT_CHANNEL {} {}".format(ls_chan_id, ls_chan_id))

                # SET CHANNEL MIDI_INPUT_CHANNEL 0 0

            except zyngine_lscp_error as err:
                logger.error(lf(err))
            except zyngine_lscp_warning as warn:
                logger.warning(lf(warn))

            # Save chan info in layer
            layer.ls_chan_info = {
                'chan_id': ls_chan_id,
                'ls_engine': None,
            }

    def ls_set_preset(self, layer, ls_engine, fpath):
        res = False
        if layer.ls_chan_info:
            ls_chan_id = layer.ls_chan_info['chan_id']

            # Load engine and set output channels if needed
            if ls_engine != layer.ls_chan_info['ls_engine']:
                try:
                    self.lscp_send_single(
                        "LOAD ENGINE {} {}".format(ls_engine, ls_chan_id))
                    layer.ls_chan_info['ls_engine'] = ls_engine

                    self.lscp_send_single(
                        "SET CHANNEL AUDIO_OUTPUT_CHANNEL {} 0 0".format(ls_chan_id))
                    self.lscp_send_single(
                        "SET CHANNEL AUDIO_OUTPUT_CHANNEL {} 1 1".format(ls_chan_id))

                except zyngine_lscp_error as err:
                    logger.error(lf(err))
                except zyngine_lscp_warning as warn:
                    logger.warning(lf(warn))

            # Load instument
            try:
                self.sock.settimeout(10)
                self.lscp_send_single(
                    "LOAD INSTRUMENT '{}' 0 {}".format(fpath, ls_chan_id))
                res = True
            except zyngine_lscp_error as err:
                logger.error(lf(err))
            except zyngine_lscp_warning as warn:
                res = True
                logger.warning(lf(warn))

            self.sock.settimeout(1)

        return res

    def ls_unset_channel(self, layer):
        if layer.ls_chan_info:
            chan_id = layer.ls_chan_info['chan_id']
            try:
                self.lscp_send_single("RESET CHANNEL {}".format(chan_id))
                # Remove sampler channel
                if self.lscp_v1_6_supported:
                    self.lscp_send_single(
                        "REMOVE CHANNEL MIDI_INPUT {}".format(chan_id))
                    self.lscp_send_single("REMOVE CHANNEL {}".format(chan_id))
            except zyngine_lscp_error as err:
                logger.error(lf(err))
            except zyngine_lscp_warning as warn:
                logger.warning(lf(warn))

            layer.ls_chan_info = None

    # ---------------------------------------------------------------------------
    # API methods
    # ---------------------------------------------------------------------------

    @classmethod
    def zynapi_get_banks(cls):
        bank_dirs = [
            ('SFZ', PATH_SAMPLES_MY + "/soundfonts/sfz"),
            ('GIG', PATH_SAMPLES_MY + "/soundfonts/gig")
        ]
        banks = []
        for b in cls.get_dirlist(cls.bank_dirs, False):
            banks.append({
                'text': b[2],
                'name': b[4],
                'fullpath': b[0],
                'raw': b,
                'readonly': False
            })
        return banks

    @classmethod
    def zynapi_get_presets(cls, bank):
        presets = []
        for p in cls._get_preset_list(bank['raw']):
            head, tail = os.path.split(p[2])
            presets.append({
                'text': p[4],
                'name': tail,
                'fullpath': p[0],
                'raw': p,
                'readonly': False
            })
        return presets

    @classmethod
    def zynapi_new_bank(cls, bank_name):
        if bank_name.lower().startswith("gig/"):
            bank_type = "gig"
            bank_name = bank_name[4:]
        elif bank_name.lower().startswith("sfz/"):
            bank_type = "sfz"
            bank_name = bank_name[4:]
        else:
            bank_type = "sfz"
        os.mkdir(PATH_SAMPLES_MY +
                 "/soundfonts/{}/{}".format(bank_type, bank_name))

    @classmethod
    def zynapi_rename_bank(cls, bank_path, new_bank_name):
        head, tail = os.path.split(bank_path)
        new_bank_path = head + "/" + new_bank_name
        os.rename(bank_path, new_bank_path)

    @classmethod
    def zynapi_remove_bank(cls, bank_path):
        shutil.rmtree(bank_path)

    @classmethod
    def zynapi_rename_preset(cls, preset_path, new_preset_name):
        head, tail = os.path.split(preset_path)
        fname, ext = os.path.splitext(tail)
        new_preset_path = head + "/" + new_preset_name + ext
        os.rename(preset_path, new_preset_path)

    @classmethod
    def zynapi_remove_preset(cls, preset_path):
        os.remove(preset_path)
        # TODO => If last preset in SFZ dir, delete it too!

    @classmethod
    def zynapi_download(cls, fullpath):
        fname, ext = os.path.splitext(fullpath)
        if ext and ext[0] == '.':
            head, tail = os.path.split(fullpath)
            return head
        else:
            return fullpath

    @classmethod
    def zynapi_install(cls, dpath, bank_path):
        # TODO: Test that bank_path fits preset type (sfz/gig)

        fname, ext = os.path.splitext(dpath)
        if os.path.isdir(dpath):
            # Locate sfz files and move all them to first level directory
            try:
                cmd = "find \"{}\" -type f -iname *.sfz".format(dpath)
                sfz_files = check_output(
                    cmd, shell=True).decode("utf-8").split("\n")
                # Find the "shallower" SFZ file
                shallower_sfz_file = sfz_files[0]
                for f in sfz_files:
                    if f and (f.count('/') < shallower_sfz_file.count('/')):
                        shallower_sfz_file = f
                head, tail = os.path.split(shallower_sfz_file)
                # Move SFZ stuff to the top level
                if head and head != dpath:
                    for f in glob.glob(head + "/*"):
                        shutil.move(f, dpath)
                    shutil.rmtree(head)
            except:
                raise Exception("Directory doesn't contain any SFZ file")

            # Move directory to destiny bank
            if "/sfz/" in bank_path:
                shutil.move(dpath, bank_path)
            else:
                raise Exception("Destiny is not a SFZ bank!")

        elif ext.lower() == '.gig':

            # Move directory to destiny bank
            if "/gig/" in bank_path:
                shutil.move(dpath, bank_path)
            else:
                raise Exception("Destiny is not a GIG bank!")

        else:
            raise Exception("File doesn't look like a SFZ or GIG soundfont")

    @classmethod
    def zynapi_get_formats(cls):
        return "gig,zip,tgz,tar.gz,tar.bz2"

    @classmethod
    def zynapi_martifact_formats(cls):
        return "sfz,gig"
