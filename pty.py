from dataclasses import dataclass
import os, pty, signal, struct, fcntl, termios, subprocess
from PySide6.QtCore import QObject, QSocketNotifier, Signal

class PtyProcess(QObject):
    output_ready = Signal(bytes) #when shell writes
    finished = Signal(int) #when shell exits

    def start(self, shell="", rows=24, cols=80):
        shell = shell or os.environ.get("SHELL", "/bin/bash")
        self._master_fd, slave_fd = pty.openpty()

        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)

        env = os.environ.copy()
        env["TERM"] = "xterm-256color" #tell programs what terminal type we are

        self._proc = subprocess.Popen(
            [shell, "-l"],
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            preexec_fn=os.setsid, #not exactly sure what this does but it makes ctrl+c work
            env=env, close_fds=True,
        )
        os.close(slave_fd)

    def write(self, data: bytes):
        os.write(self._master_fd, data)

    def resize(self, rows, cols):
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)

    def _read(self):
        try:
            data = os.read(self._master_fd, 65536)
            if data:
                self.output_ready.emit(data)
        except OSError:
            self._cleanup()

    def terminate(self):
        if self._proc:
            os.killpg(os.getpgid(self._proc.pid), signal.SIGHUP)
            self.finished.emit(0)