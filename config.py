from dataclasses import dataclass

@dataclass
class Conf: #this stuff i'll try to make configurable in-app later
    font_family: str = "monospace"
    font_size: int = 14 
    shell: str = ""