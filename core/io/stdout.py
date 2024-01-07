import os


class StdOut:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(StdOut, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.muted = False

    def mute(self):
        if self.muted:
            return
        self.null_fds = [
            os.open(os.devnull, os.O_RDWR) for x in range(2)]
        self.save_fds = [os.dup(1), os.dup(2)]

        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)
        self.muted = True

    def unmute(self):
        if not self.muted:
            return
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
        self.muted = False


stdout = StdOut()
