
class Manipulator:
    def __init__(self, libseq) -> None:
        self.libseq = libseq

    def _decode(self, hexdat):
        return int(hexdat[0], 16), int(hexdat[1], 16) 

    def _decode_pair(self, hexdat1, hexdat2):
        return self._decode(hexdat1), self._decode(hexdat2)

    def gen(self, par):
        """generate a monotone rhythm"""
        self.libseq.addNote(0, 45, 80, 1)
        self.libseq.addNote(8, 48, 80, 1)

    def mov(self, dst):
        """copy current pattern to destination"""
        db, ds = self._decode(dst)
        dt = self.libseq.getPatternAt(db, ds, 0, 0)
        # self.libseq.copyPattern(uint32_t source, uint32_t destination)

    def shl(self, off):
        """shift pattern content left by x"""

    def shr(self, off):
        """shift pattern content right by x"""

    def rol(self, off):
        """rotate pattern content left by x"""

    def ror(self, off):
        """rotate pattern content right by x"""
