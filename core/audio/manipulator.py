
class Manipulator:
    def __init__(self, libseq) -> None:
        self.libseq = libseq

    def gen(self, par):
        """generate a monotone rhythm"""
        self.libseq.addNote(0, 45, 80, 1)
        self.libseq.addNote(8, 48, 80, 1)

    def mov(self, db, ds):
        """copy current pattern to destination"""
        # db, ds = self._decode(par)
        if not db:
            return False
        # print(db, ds)
        dp = self.libseq.getPatternAt(db, ds, 0, 0)
        # print(self.libseq.getPatternIndex(), dp)
        self.libseq.copyPattern(self.libseq.getPatternIndex(), dp)
        return True

    def shl(self, val):
        """shift pattern content left by x"""

    def shr(self, val):
        """shift pattern content right by x"""

    def rol(self, val):
        """rotate pattern content left by x"""

    def ror(self, val):
        """rotate pattern content right by x"""
