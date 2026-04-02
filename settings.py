from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout

class _Viewport(QWidget):
    def __init__(self, on_resize, parent=None):
        super().__init__(parent)
        self._on_resize = on_resize

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_resize(event.size())

class SettingsPanel(QFrame):
    _TABS = ["Behavior", "Looks", "Assistance"]

    def __init__(self, conf, on_change, parent=None):
        super().__init__(parent)
        self._conf = conf
        self._on_change = on_change
        self.setStyleSheet("QFrame { background: #3e4052; border-right: 1px solid #272933; }")
        self._current = 0
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold; padding: 14px 0 10px 12px;")
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

        self._setup_looks_page()

    def _on_viewport_resize(self, size):
        w, h = size.width(), size.height()
        self._slide.setGeometry(-self._current * w, 0, w * len(self._TABS), h)
        for i, page in enumerate(self._pages):
            page.setGeometry(i * w, 0, w, h)

    def _setup_looks_page(self):
        page = self._pages[1] #page 1 in settings
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        for label, attr in [
            ("Background", "bg_color"),
            ("Foreground", "fg_color"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")
            btn = QPushButton()
            btn.setFixedSize(32, 32) #will this cause problems?
            btn.setStyleSheet(f"background: {getattr(self._conf, attr)}; border: 1px solid #555555;")
            btn.clicked.connect(lambda _, a = attr, b = btn: self._pick_color(a, b))
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(btn)
            layout.addLayout(row)

        layout.addStretch()

    def _pick_color(self, attr, btn):
        initial = QColor(getattr(self._conf, attr))
        color = QColorDialog.getColor(initial, self, "Pick color")
        if not color.isValid():
            return
        setattr(self._conf, attr, color.name())
        btn.setStyleSheet(f"background: {color.name()}; border: 1px solid #555555;")
        self._conf.save()
        self._on_change()

    def _switch(self, idx):
        if idx == self._current:
            return
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
        self._current = idx
        w = self._viewport.width()
        self._anim.stop()
        self._anim.setStartValue(self._slide.pos())
        self._anim.setEndValue(QPoint(-idx * w, 0))
        self._anim.start()

    