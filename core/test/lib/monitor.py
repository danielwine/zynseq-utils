import time
# from core.lib.zynseq.zynseq import zynseq

# zyn = zynseq.zynseq()


"""JACK client that prints all received MIDI events."""

import jack
import binascii


def process(frames):
    for offset, data in port.incoming_midi_events():
        print('{0}: 0x{1}'.format(client.last_frame_time + offset,
                                  binascii.hexlify(data).decode()))

client = jack.Client('MIDI-Monitor')
port = client.midi_inports.register('input')
client.set_process_callback(process)
client.activate()

client.connect('zynseq:output', 'MIDI-Monitor:input')

with client:
    print('#' * 80)
    print('press Return to quit')
    print('#' * 80)
    input()
