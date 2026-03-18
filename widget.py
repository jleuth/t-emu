import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter                                                                                                         
from PySide6.QtWidgets import QApplication, QWidget  

                                                                                                                                                                        
from config import Conf                                                                                                                                                 
from emulator import TerminalEmulator                                                                                                                                   
from pty import PtyProcess                                                                                                                                              
                                                                                                                                                                        
KEY_MAP = {                                                                                                                                                              
    Qt.Key.Key_Up: b"\x1b[A",                                                                                                                                            
    Qt.Key.Key_Down: b"\x1b[B",                                                                                                                                          
    Qt.Key.Key_Right: b"\x1b[C",                                                                                                                                         
    Qt.Key.Key_Left: b"\x1b[D",                                                                                                                                          
    Qt.Key.Key_Backspace: b"\x7f",                                                                                                                                       
    Qt.Key.Key_Tab: b"\t",                                                                                                                                               
    Qt.Key.Key_Return: b"\r",                                                                                                                                            
    Qt.Key.Key_Enter: b"\r",                                                                                                                                             
    Qt.Key.Key_Escape: b"\x1b",                                                                                                                                          
    Qt.Key.Key_Delete: b"\x1b[3~",                                                                                                                                       
    Qt.Key.Key_Home: b"\x1b[H",                                                                                                                                          
    Qt.Key.Key_End: b"\x1b[F",                                                                                                                                           
    Qt.Key.Key_PageUp: b"\x1b[5~",
    Qt.Key.Key_PageDown: b"\x1b[6~",                                                                                                                                     
}                                 

class TerminalWidget(QWidget):
    def __init__(self, conf=None, parent=None):
        super().__init__(parent)
        self._conf = conf or Conf()

        self._font = QFont(self._conf.font_family)
        self._font.setPixelSize(self._conf.font_size)
        self._font.setFixedPitch(True)

        fm = QFontMetricsF(self._font)
        self._cell_w = fm.horizontalAdvance("M")
        self._cell_h = fm.height() + 2
        self._baseline = fm.ascent() + 1
        self._rows = 24
        self._cols = 80

        self._emu = TerminalEmulator(self._rows, self._cols)
        self._pty = PtyProcess(self)
        self._pty.output_ready.connect(self._on_output)
        self._pty.finished.connect(self.close)

        self._cursor_visible = True
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._blink)
        self._cursor_timer.start(530)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(200, 100)

    def start(self):
        self._recalc_grid()
        self._pty.start(self._conf.shell, rows=self._rows, cols=self._cols)

    def _recalc_grid(self):
        cols = max(2, int(self.width() / self._cell_w))
        rows = max(1, int(self.height() / self._cell_h))
        if cols != self._cols or rows != self._rows:
            self._cols = cols
            self._rows = rows
            self._emu.resize(rows, cols)
            if self._pty._proc is not None and self._pty._proc.poll() is None:
                self._pty.resize(rows, cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalc_grid()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setFont(self._font)
        p.fillRect(self.rect(), QColor(16, 16, 20))

        screen = self._emu._screen
        cur_row, cur_col = self._emu._screen.cursor.y, self._emu._screen.cursor.x

        for row in range(self._rows):
            line = screen.buffer[row]
            y = int(row * self._cell_h)
            for col in range(self._cols):
                char = line[col]
                x = int(col * self._cell_w)
                fg = QColor("#b5f5f1")
                ch = char.data
                if ch and ch != "":
                    p.setPen(fg)
                    p.drawText(x, y + int(self._baseline), ch)

        if self._cursor_visible:
            cx = int(cur_col * self._cell_w)
            cy = int(cur_row * self._cell_h)
            p.fillRect(cx, cy, max(2, int(self._cell_w)), int(self._cell_h), QColor(97, 175, 239, 180))

        p.end()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        if key in KEY_MAP:
            self._pty.write(KEY_MAP[key])
            return

        if mods & Qt.KeyboardModifier.ControlModifier:
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                self._pty.write(bytes([key - Qt.Key.Key_A + 1]))
                return

        text = event.text()
        if text:
            self._pty.write(text.encode("utf-8"))

    def _blink(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    def _on_output(self, data):
        self._emu.feed(data)
        self._cursor_visible = True
        self.update()

def main():
    app = QApplication(sys.argv)
    w = TerminalWidget()
    w.resize(800, 500)
    w.show()
    w.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()