from os.path import dirname, abspath

# General settings

debug_mode = False         # debug messages are hidden when turned off
autorun_jack = True        # should start jack if it's not already running

# Constants

VERSION = '0.0.1'          # version number of the performer app

# Sequencer (conversion) settings

create_backup = True       # whether to make a local backup of a zss
vertical_zoom  = 16        # default vertical zoom for saving snapshots
minimum_rows = 5           # minimum number of rows / columns per bank
maximum_rows = 5           # maximum number of rows / columns per bank
auto_bank = 10             # destination bank of auto transposed phrases
trigger_channel = 15       # global trigger channel for sequences
trigger_start_note = 24    # start note for auto transposed sequences  

# Paths

PATH_BASE = dirname(abspath(__file__))
PATH_DATA = '/'.join(PATH_BASE.split('/')[:-1]) + '/data'
PATH_LIB = PATH_BASE + '/lib/zynseq/zynseq/'
PATH_ZSS = PATH_DATA + '/zss'
PATH_XRNS = PATH_DATA + '/xrns'
PATH_PROJECTS = PATH_DATA + '/projects'

PATH_SAMPLES = '/zynthian/zynthian-data/soundfonts/'
PATH_SAMPLES_MY = '/zynthian/zynthian-my-data/soundfonts/'

# Audio auto start configuration

JACK_CONFIG = '-P 70 -t 2000 -s -d alsa -d hw:0,0 ' \
              '-r 48000 -p 256 -n 2 -X seq'

# Zynthian configuration /for bridge/

SFTP_HOST = "zynthian.local"
SFTP_USER = "root"
SFTP_PASSWORD = "raspberry"
SFTP_DEFAULT_SNAPSHOT = '003'
