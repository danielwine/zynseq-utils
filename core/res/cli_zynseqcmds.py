
pcmds = {
    'lb': 'list_banks',
    'ls': 'sequence_names',
    'lp': 'list_patterns',
    'sb': 'select_bank i',
    'sp': 'select_pattern i',
    'pi': 'pattern_info',
    'pp': 'get_notes_in_pattern',
    'toggle': 'transport_toggle'
}

lcmds = {
    'im': 'isModified',
    'ed': 'enableDebug b',
    # Direct MIDI interface
    'pn': 'playNote i i i i',
    'gtc': 'getTriggerChannel',
    'gtn': 'getTriggerNote i i',
    # Pattern management
    'cp': 'createPattern',
    'gpt': 'getPatternsInTrack i i i',
    'gp': 'getPattern i i i i',
    'gs': 'getSteps',
    'sbp': 'setBeatsInPattern i',
    'ssbp': 'setStepsPerBeat i',
    'an': 'addNote i i i i',
    'rn': 'removeNote i i',
    # Sequence management
    'ie': 'isEmpty i i',
    'ap': 'addPattern i i i i i',
    'gsn': 'getSequenceName i i',
    'gts': 'getTracksInSequence i i',
    'ssb': 'setSequencesInBank i i',
    'gg': 'getGroup i i',
    'sg': 'setGroup i i i',
    'gc': 'getChannel i i i',
    'sc': 'setChannel i i i i',
    'tps': 'togglePlayState i i',
    # Bank management
    'gsb': 'getSequencesInBank i',
    't': 'getTempo',
    'tgps': 'transportGetPlayStatus',
}

menu = {
    'F1': 'Terminal',
    'F2': 'Sequences',
    'F3': 'Pattern',
    'F4': 'Instruments',
    'F9': 'Help',
    'F10': 'Exit'
}
