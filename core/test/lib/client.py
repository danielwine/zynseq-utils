import time
from core.lib.zynseq.zynseq import zynseq

zyn = zynseq.zynseq()


while True:
    zyn.libseq.playNote(62, 110, 1, 200)
    zyn.libseq.playNote(69, 110, 1, 200)
    zyn.libseq.playNote(74, 110, 1, 200)
    time.sleep(4)
