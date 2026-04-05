from dataclasses import dataclass
from PySide6.QtCore import QSettings

_ORG = "t-emu"
_APP = "t-emu"

@dataclass
class Conf: 
    font_family: str = "monospace"
    font_size: int = 14 
    shell: str = ""
    bg_color: str = "#101014"
    fg_color: str = "#d3d7cf"
    
    @classmethod
    def load(cls) -> "Conf":
        s = QSettings(_ORG, _APP)
        c = cls()
        c.font_family = s.value("font_family", c.font_family)
        c.font_size = int(s.value("font_size", c.font_size))
        c.shell = s.value("shell", c.shell)
        c.bg_color = s.value("bg_color", c.bg_color)
        c.fg_color = s.value("fg_color", c.fg_color)
        c.current_model = s.value("current_model", c.current_model)
        c.current_instructions_path = s.value("current_instructions_path", c.current_instructions_path)

        return c

    def save(self):
        s = QSettings(_ORG, _APP)
        s.setValue("font_family", self.font_family)
        s.setValue("font_size", self.font_size)
        s.setValue("shell", self.shell)
        s.setValue("bg_color", self.bg_color)
        s.setValue("fg_color", self.fg_color)
        s.setValue("current_model", self.current_model)
        s.setValue("current_instructions_path", self.current_instructions_path)
