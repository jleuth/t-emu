import sys
import signal
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter                                                                                                         
from PySide6.QtWidgets import QApplication, QWidget  

                                                                                                                                                                        
from config import Conf                                                                                                                                                 
from emulator import TerminalEmulator                                                                                                                                   
from pty import PtyProcess                                                                                                                                              
                                                                                                                                                                        
KEY_MAP = {                                                                                                                                                              
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
    Qt.Key.Key_F1:  b"\x1bOP",                                                                                                                                               
    Qt.Key.Key_F2:  b"\x1bOQ",                                                                                                                                               
    Qt.Key.Key_F3:  b"\x1bOR",                                                                                                                                               
    Qt.Key.Key_F4:  b"\x1bOS",                                                                                                                                               
    Qt.Key.Key_F5:  b"\x1b[15~",                                                                                                                                             
    Qt.Key.Key_F6:  b"\x1b[17~",                                                                                                                                             
    Qt.Key.Key_F7:  b"\x1b[18~",                                                                                                                                             
    Qt.Key.Key_F8:  b"\x1b[19~",                                                                                                                                             
    Qt.Key.Key_F9:  b"\x1b[20~",                                                                                                                                             
    Qt.Key.Key_F10: b"\x1b[21~",                                                                                                                                             
    Qt.Key.Key_F11: b"\x1b[23~",                                                                                                                                             
    Qt.Key.Key_F12: b"\x1b[24~",      
                                                                                                                              
}    

CTRL_ARROW_MAP = {
    Qt.Key.Key_Up:    b"\x1b[1;5A",
    Qt.Key.Key_Down:  b"\x1b[1;5B",                                                                                                                                      
    Qt.Key.Key_Right: b"\x1b[1;5C",                                                                                                                                      
    Qt.Key.Key_Left:  b"\x1b[1;5D",  
}

ARROW_KEYS = {                                                                                                                                                           
    Qt.Key.Key_Up:    (b"\x1b[A", b"\x1bOA"),                                                                                                                            
    Qt.Key.Key_Down:  (b"\x1b[B", b"\x1bOB"),                                                                                                                            
    Qt.Key.Key_Right: (b"\x1b[C", b"\x1bOC"),                                                                                                                            
    Qt.Key.Key_Left:  (b"\x1b[D", b"\x1bOD"),                                                                                                                            
}

_PYTE_ANSI = [                                                                                                                                                           
    "#000000", "#cc0000", "#4e9a06", "#c4a000",                                                                                                                          
    "#3465a4", "#75507b", "#06989a", "#d3d7cf",                                                                                                                          
    "#555753", "#ef2929", "#8ae234", "#fce94f",                                                                                                                          
    "#729fcf", "#ad7fa8", "#34e2e2", "#eeeeec",                                                                                                                          
]

def _pyte_color(value):
    if value == "default" or value is None:
        return None
    if isinstance(value, int):
        if value < 16:
            return QColor(_PYTE_ANSI[value])
        if value < 232:
            v = value - 16
            b = v % 6
            g = (v // 6) % 6
            r = v // 36
            return QColor(r * 51, g * 51, b * 51)

        s = (value - 232) * 10 + 8
        return QColor(s, s, s)
    if isinstance(value, str):
        if value.startswith('#') or len(value) > 0:
            return QColor(value) if QColor(value).isValid() else None
    return None

class TerminalWidget(QWidget):
    def __init__(self, conf=None, parent=None):
        super().__init__(parent)
        self._conf = conf or Conf()

        self._font = QFont(self._conf.font_family)
        self._font.setPixelSize(self._conf.font_size)
        self._font.setFixedPitch(True)
        self._font_bold = QFont(self._font)
        self._font_italic = QFont(self._font)
        self._font_bold_italic = QFont(self._font)

        self._font_bold.setBold(True)
        self._font_italic.setItalic(True)
        self._font_bold_italic.setBold(True)
        self._font_bold_italic.setItalic(True)

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
                ch = char.data

                fg = _pyte_color(char.fg) or QColor('#b6f5f1')
                bg = _pyte_color(char.bg)

                if char.reverse:
                    fg, bg = (bg or QColor(16, 16, 20)), (fg or QColor('#ffffff'))

                if bg: p.fillRect(x, y, int((col + 1) * self._cell_w) - x, int((row + 1) * self._cell_h) - y, bg)

                if ch and ch != "":
                    if char.bold and char.italics:
                        p.setFont(self._font_bold_italic)
                    elif char.bold:
                        p.setFont(self._font_bold)
                    elif char.italics:
                        p.setFont(self._font_italic)
                    else:
                        p.setFont(self._font)
                    p.setPen(fg)
                    p.drawText(x, y + int(self._baseline), ch)

                if char.underscore:
                    p.setPen(fg)
                    p.drawLine(x, y, + int(self._cell_h) - 2, x + int(self._cell_w, y + int(self._cell_h)) -2)

                if char.strikethrough:
                    p.setPen(fg)
                    p.drawLine(x, y, + int(self._cell_h // 2), x + int(self._cell_w), y + int(self._cell_h // 2))

        if self._cursor_visible and not self._emu._screen.cursor.hidden:
            cx = int(cur_col * self._cell_w)
            cy = int(cur_row * self._cell_h)
            p.fillRect(cx, cy, max(2, int(self._cell_w)), int(self._cell_h), QColor(97, 175, 239, 180))

        p.end()

    def event(self, event):
        if event.type() == event.Type.KeyPress:
            self.keyPressEvent(event)
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        app_cursor = "DECCKM" in self._emu._screen.mode  

        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            self._pty.write(b'\x03')
            self._pty.send_signal_to_fg(signal.SIGINT)
            return

        if mods & Qt.KeyboardModifier.ControlModifier and key in CTRL_ARROW_MAP:
            self._pty.write(CTRL_ARROW_MAP[key])
            return

        if key in ARROW_KEYS:
            normal, app = ARROW_KEYS[key]
            self._pty.write(app if app_cursor else normal)
            return

        if key in KEY_MAP:
            self._pty.write(KEY_MAP[key])
            return

        if mods & Qt.KeyboardModifier.ControlModifier:
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                self._pty.write(bytes([key - Qt.Key.Key_A + 1]))
                return

        if mods & Qt.KeyboardModifier.AltModifier:
            text = event.text()
            if text:
                self._pty.write(b"\x1b" + text.encode("utf-8"))
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
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    app = QApplication(sys.argv)
    w = TerminalWidget()
    w.resize(800, 500)
    w.show()
    w.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()