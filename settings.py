from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout

class _Viewport(QWidget):
    def __init__(self, on_resize, parent=None):
        super().__init__(parent)
        self._on_resize = on_resize

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_resize(event.size())

class SettingsPanel(QFrame):
    _TABS = ["Behavior", "Looks", "Assistance"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: #3e4052; border-right: 1px solid #272933; }")
        self._current = 0
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold; padding: 14px 0 10px 0;")
        root.addWidget(title)

        tab_bar = QWidget()
        tab_bar.setStyleSheet("background: transparent;")
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(8, 0, 8, 8)
        tab_row.setSpacing(4)
        self._tab_btns = []
        for i, name in enumerate(self._TABS):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda _, idx=i: self._switch(idx))
            btn.setStyleSheet("""                                                                                                                                        
                QPushButton {
                    background: transparent; color: #a6adc8;                                                                                                             
                    border: none; border-radius: 4px;
                    padding: 4px 6px; font-size: 11px;
                }                                                                                                                                                        
                QPushButton:checked { background: #494d64; color: #cdd6f4; }
                QPushButton:hover:!checked { color: #cdd6f4; }                                                                                                           
            """)
            tab_row.addWidget(btn)
            self._tab_btns.append(btn)
        root.addWidget(tab_bar)

        self._viewport = _Viewport(self._on_viewport_resize)
        self._viewport.setStyleSheet("background: transparent;")
        root.addWidget(self._viewport, 1)

        self._slide = QWidget(self._viewport)
        self._pages = [QWidget(self._slide) for _ in self._TABS]

        self._anim = QPropertyAnimation(self._slide, b"pos")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _on_viewport_resize(self, size):
        w, h = size.width(), size.height()
        self._slide.setGeometry(-self._current * w, 0, w * len(self._TABS), h)
        for i, page in enumerate(self._pages):
            page.setGeometry(i * w, 0, w, h)

    def _switch(self, idx):
        if idx == self._current:
            return
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
        self._current = idx
        w = set._viewport.width()
        self._anim.stop()
        self._anim.setStartValue(self._slide.pos())
        self._anim.setEndValue(QPoint(-idx * w, 0))
        self._anim.start()