
from jack import Port, MidiPort


def is_port(object):
    return True if isinstance(object, Port) or (
        isinstance(object, MidiPort)) else False
    
def format_port(port):
    if not is_port(port): return False
    suffix = ' (MIDI)' if port.__class__.__name__ == 'MidiPort' else ''
    return port.name + suffix
