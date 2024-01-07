
class Generator:
    def __init__(self, libseq) -> None:
        self.libseq = libseq

    def generate(self):
        self.libseq.addNote(0, 45, 80, 1)
        self.libseq.addNote(8, 48, 80, 1)
