import sys
import signal
from turtle import isvisible
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, QEvent
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QKeySequence, QPainter, QShortcut                                                                                                         
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QWidget  

                                                                                                                                                                        
from config import Conf                                                                                                                                                 
import config
from emulator import TerminalEmulator                                                                                                                                   
from pty import PtyProcess  
from settings import SettingsPanel                                                                                                                                            
                                                                                                                                                                        
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
    "#0a0a0a", "#ff2020", "#00dd00", "#ffaa00",
    "#3399ff", "#dd44ff", "#00dddd", "#eeeeee",                                                                                                                          
    "#555555", "#ff5555", "#55ff55", "#ffff55",                                                                                                                          
    "#5588ff", "#ff55ff", "#55ffff", "#ffffff",                                                                                                                        
]

_PYTE_NAMED = { 
    "black":          0, "red":            1, "green":        2, "brown":        3,
    "blue":           4, "magenta":        5, "cyan":         6, "white":        7,                                                                                      
    "brightblack":    8, "brightred":      9, "brightgreen": 10, "brightbrown": 11,
    "brightblue":    12, "brightmagenta": 13, "brightcyan":  14, "brightwhite": 15,                                                                                      
} 

def _pyte_color(value):
    if value == "default" or value is None:
        return None
    if isinstance(value, str):
        if value in _PYTE_NAMED:
            return QColor(_PYTE_ANSI[_PYTE_NAMED[value]])
        if len(value) == 6:
            return QColor("#" + value)
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

        self._llm_modal = LlmModal(self)

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
        p.fillRect(self.rect(), QColor(self._conf.bg_color))

        screen = self._emu._screen
        cur_row, cur_col = self._emu._screen.cursor.y, self._emu._screen.cursor.x

        for row in range(self._rows):
            line = screen.buffer[row]
            y = int(row * self._cell_h)
            for col in range(self._cols):
                char = line[col]
                x = int(col * self._cell_w)
                ch = char.data

                fg = _pyte_color(char.fg) or QColor(self._conf.fg_color)
                bg = _pyte_color(char.bg)

                if char.reverse:
                    fg, bg = (bg or QColor(self._conf.bg_color)), (fg or QColor('#ffffff'))

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

                if char.underscore and ch and ch.strip():
                    p.setPen(fg)
                    p.drawLine(x, y + int(self._cell_h) - 2, x + int(self._cell_w), y + int(self._cell_h) - 2)  

                if char.strikethrough and ch and ch.strip():
                    p.setPen(fg)
                    p.drawLine(x, y + int(self._cell_h // 2), x + int(self._cell_w), y + int(self._cell_h // 2))

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

        if key == Qt.Key.Key_Escape and self._llm_modal.isVisible():
            self._llm_modal.dismiss()
            return

        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            self._pty.write(b'\x03')
            self._pty.send_signal_to_fg(signal.SIGINT)
            return

        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_K:
            if self._llm_modal.isVisible():
                self._llm_modal.dismiss()
            else:
                cx = int(self._emu._screen.cursor.x * self._cell_w)
                cy = int(self._emu._screen.cursor.y * self._cell_h)
                self._llm_modal.open(cx, cy, self.width())
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

class LlmModal(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: #3e4052; border: 1px solid #272933; border-radius: 6px; }")
        self.setFixedHeight(40)
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Get help with a command...")
        self._input.setStyleSheet("QLineEdit { background: transparent; color: #cdd6f4; border: none; font-size: 13px; }")
        layout.addWidget(self._input)

    def open(self, cursor_x, cursor_y, parent_w):
        w = min(250, parent_w - 20)
        x = max(10, min(cursor_x, parent_w - w - 10))
        y = max(10, cursor_y - self.height() - 4)
        self.setGeometry(x, y, w, self.height())
        self._input.clear()
        self.show()
        self._input.setFocus()

    def dismiss(self):
        self.hide()
        if self.parent():
            self.parent().setFocus()

class MainWindow(QMainWindow):
    _SIDEBAR_W = 250

    def __init__(self, conf):                                                                                                                                                
        super().__init__()                                                                                                                                                 
        self._sidebar_open = False
        self._conf = conf                                                                                                                                                    
    
        central = QWidget()                                                                                                                                                  
        self.setCentralWidget(central)
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)                                                                                                                                                    
    
        self._sidebar = SettingsPanel(conf, on_change=self._on_settings_change)                                                                                              
        self._sidebar.setMaximumWidth(0)
        row.addWidget(self._sidebar)

        self._term = TerminalWidget(conf)                                                                                                                                    
        row.addWidget(self._term, 1)
                                                                                                                                                                            
        self._anim = QPropertyAnimation(self._sidebar, b"maximumWidth")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._sidebar.setMinimumWidth)                                                                                                       
    
        shortcut = QShortcut(QKeySequence("Ctrl+E"), self)                                                                                                                   
        shortcut.activated.connect(self._toggle_sidebar)


    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        self._anim.stop()
        self._anim.setStartValue(self._sidebar.maximumWidth())
        self._anim.setEndValue(self._SIDEBAR_W if self._sidebar_open else 0)
        self._anim.start()
    
    def _on_settings_change(self):
        self._term.update()

    def start(self):
        self._term.start()
        self._term.setFocus()

def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    app = QApplication(sys.argv)
    conf = Conf.load()
    w = MainWindow(conf)
    w.resize(800, 500)
    w.show()
    w.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()