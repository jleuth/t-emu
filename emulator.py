import pyte

class _Screen(pyte.Screen):
    def report_device_status(self, *args, **kwargs): #we're ignoring it for now
        pass

class TerminalEmulator:
    def __init__(self, rows=24, cols=80):
        self._screen = _Screen(cols, rows)
        self._stream = pyte.Stream(self._screen)

    def feed(self, data: bytes):
        text = data.decode("utf-8", errors="replace")
        self._stream.feed(text)

    def resize(self, rows, cols):
        self._screen.resize(rows, cols)