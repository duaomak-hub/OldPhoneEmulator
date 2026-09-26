"""
Base device class for Nokia phones
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

class DeviceFamily(Enum):
    S30 = "Series 30"
    S40 = "Series 40"
    S60 = "Series 60"
    S80 = "Series 80"
    S90 = "Series 90"
    ASHA = "Asha"

class InputType(Enum):
    KEYPAD = "keypad"
    QWERTY = "qwerty"
    TOUCH = "touch"
    TOUCH_QWERTY = "touch_qwerty"

@dataclass
class ScreenSpec:
    width: int
    height: int
    bpp: int = 16
    touch: bool = False
    orientation: str = "portrait"

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

@dataclass
class HardwareSpec:
    cpu: str
    cpu_mhz: int
    ram_mb: int
    rom_mb: int
    gpu: str = "Unknown"
    has_wifi: bool = False
    has_bt: bool = False
    has_gps: bool = False
    has_camera: bool = False
    camera_mp: float = 0.0

@dataclass
class KeypadLayout:
    type: InputType
    has_dpad: bool = True
    has_softkeys: bool = True
    has_numpad: bool = True
    has_qwerty: bool = False
    keys: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.keys:
            if self.type == InputType.KEYPAD:
                self.keys = ["soft_left", "soft_right", "call", "end", "dpad_up", "dpad_down", "dpad_left", "dpad_right", "dpad_center",
                             "1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
            elif self.type == InputType.QWERTY:
                self.keys = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p",
                             "a", "s", "d", "f", "g", "h", "j", "k", "l",
                             "z", "x", "c", "v", "b", "n", "m", "space", "sym", "shift"]

@dataclass
class NokiaDevice:
    id: str
    name: str
    family: DeviceFamily
    year: int
    symbian_version: str
    screen: ScreenSpec
    hardware: HardwareSpec
    keypad: KeypadLayout
    iconic: bool = False
    description: str = ""
    colors: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "family": self.family.value,
            "year": self.year,
            "symbian": self.symbian_version,
            "screen": {
                "width": self.screen.width,
                "height": self.screen.height,
                "resolution": self.screen.resolution,
                "bpp": self.screen.bpp,
                "touch": self.screen.touch
            },
            "hardware": {
                "cpu": self.hardware.cpu,
                "mhz": self.hardware.cpu_mhz,
                "ram": self.hardware.ram_mb,
                "rom": self.hardware.rom_mb,
                "wifi": self.hardware.has_wifi,
                "bt": self.hardware.has_bt,
                "gps": self.hardware.has_gps,
                "camera": self.hardware.camera_mp
            },
            "keypad": {
                "type": self.keypad.type.value,
                "keys": self.keypad.keys
            },
            "iconic": self.iconic,
            "description": self.description,
            "colors": self.colors
        }
