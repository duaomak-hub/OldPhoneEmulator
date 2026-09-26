"""
Nokia device profiles - iconic phones
"""
from typing import Dict, List, Optional
from .base import NokiaDevice, DeviceFamily, InputType, ScreenSpec, HardwareSpec, KeypadLayout

# Define iconic Nokia devices
DEVICES = [
    NokiaDevice(
        id="nokia_3310",
        name="Nokia 3310",
        family=DeviceFamily.S30,
        year=2000,
        symbian_version="Nokia OS (S30)",
        screen=ScreenSpec(width=84, height=48, bpp=1, touch=False),
        hardware=HardwareSpec(cpu="MAD2WD1", cpu_mhz=13, ram_mb=1, rom_mb=4, has_camera=False),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="The indestructible legend. 84x48 monochrome, 900mAh, Snake II",
        colors=["Dark Blue", "Grey"]
    ),
    NokiaDevice(
        id="nokia_1100",
        name="Nokia 1100",
        family=DeviceFamily.S30,
        year=2003,
        symbian_version="Nokia OS (S30)",
        screen=ScreenSpec(width=96, height=65, bpp=1),
        hardware=HardwareSpec(cpu="DCT4", cpu_mhz=16, ram_mb=1, rom_mb=4),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="Best-selling phone ever - 250M units. Torch light!",
        colors=["Black"]
    ),
    NokiaDevice(
        id="nokia_6600",
        name="Nokia 6600",
        family=DeviceFamily.S60,
        year=2003,
        symbian_version="S60 2nd Edition (Symbian OS 7.0s)",
        screen=ScreenSpec(width=176, height=208, bpp=16),
        hardware=HardwareSpec(cpu="ARM9", cpu_mhz=104, ram_mb=6, rom_mb=32, has_bt=True, has_camera=True, camera_mp=0.3),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="First S60 with VGA camera, the smartphone that started it all",
        colors=["Black"]
    ),
    NokiaDevice(
        id="nokia_7610",
        name="Nokia 7610",
        family=DeviceFamily.S60,
        year=2004,
        symbian_version="S60 2nd Edition (Symbian OS 7.0s)",
        screen=ScreenSpec(width=176, height=208, bpp=16),
        hardware=HardwareSpec(cpu="ARM9", cpu_mhz=123, ram_mb=8, rom_mb=32, has_bt=True, has_camera=True, camera_mp=1.0),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="Fashion phone with 1MP camera and unique keypad",
        colors=["White"]
    ),
    NokiaDevice(
        id="nokia_n70",
        name="Nokia N70",
        family=DeviceFamily.S60,
        year=2005,
        symbian_version="S60 2nd Edition FP3 (Symbian OS 8.1a)",
        screen=ScreenSpec(width=176, height=208, bpp=18),
        hardware=HardwareSpec(cpu="ARM9", cpu_mhz=220, ram_mb=22, rom_mb=64, has_bt=True, has_camera=True, camera_mp=2.0),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="First Nseries, 2MP camera, 3G",
        colors=["Silver"]
    ),
    NokiaDevice(
        id="nokia_n95",
        name="Nokia N95",
        family=DeviceFamily.S60,
        year=2007,
        symbian_version="S60 3rd Edition FP1 (Symbian OS 9.2)",
        screen=ScreenSpec(width=240, height=320, bpp=24),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=332, ram_mb=64, rom_mb=256, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=5.0),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="The ultimate multimedia computer - 5MP Carl Zeiss, GPS, WiFi, dual slide",
        colors=["Silver", "Black", "Gold"]
    ),
    NokiaDevice(
        id="nokia_n95_8gb",
        name="Nokia N95 8GB",
        family=DeviceFamily.S60,
        year=2007,
        symbian_version="S60 3rd Edition FP1 (Symbian OS 9.2)",
        screen=ScreenSpec(width=240, height=320, bpp=24),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=332, ram_mb=128, rom_mb=8192, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=5.0),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="N95 with 8GB internal memory, larger screen",
        colors=["Black"]
    ),
    NokiaDevice(
        id="nokia_e90",
        name="Nokia E90 Communicator",
        family=DeviceFamily.S60,
        year=2007,
        symbian_version="S60 3rd Edition FP1 (Symbian OS 9.2)",
        screen=ScreenSpec(width=800, height=352, bpp=24),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=332, ram_mb=128, rom_mb=256, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=3.2),
        keypad=KeypadLayout(type=InputType.QWERTY, has_qwerty=True),
        iconic=True,
        description="The communicator - 800x352 internal screen + external 240x320, full QWERTY",
        colors=["Mocha"]
    ),
    NokiaDevice(
        id="nokia_5800",
        name="Nokia 5800 XpressMusic",
        family=DeviceFamily.S60,
        year=2008,
        symbian_version="S60 5th Edition (Symbian OS 9.4)",
        screen=ScreenSpec(width=360, height=640, bpp=24, touch=True),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=434, ram_mb=128, rom_mb=256, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=3.2),
        keypad=KeypadLayout(type=InputType.TOUCH, has_dpad=False, has_numpad=False),
        iconic=True,
        description="First S60 touch, resistive touch, stylus, Comes With Music",
        colors=["Black", "Red", "Blue"]
    ),
    NokiaDevice(
        id="nokia_n8",
        name="Nokia N8",
        family=DeviceFamily.S60,
        year=2010,
        symbian_version="Symbian^3 (Symbian OS 9.5)",
        screen=ScreenSpec(width=360, height=640, bpp=24, touch=True),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=680, ram_mb=256, rom_mb=512, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=12.0),
        keypad=KeypadLayout(type=InputType.TOUCH, has_dpad=False, has_numpad=False),
        iconic=True,
        description="12MP camera with Xenon flash, HDMI, Symbian^3",
        colors=["Dark Grey", "Silver White", "Green", "Blue", "Orange"]
    ),
    NokiaDevice(
        id="nokia_808",
        name="Nokia 808 PureView",
        family=DeviceFamily.S60,
        year=2012,
        symbian_version="Symbian Belle FP1",
        screen=ScreenSpec(width=360, height=640, bpp=24, touch=True),
        hardware=HardwareSpec(cpu="ARM11", cpu_mhz=1300, ram_mb=512, rom_mb=1024, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=41.0),
        keypad=KeypadLayout(type=InputType.TOUCH, has_dpad=False, has_numpad=False),
        iconic=True,
        description="41MP PureView camera, last Symbian flagship",
        colors=["Black", "White", "Red"]
    ),
    NokiaDevice(
        id="nokia_3210",
        name="Nokia 3210",
        family=DeviceFamily.S30,
        year=1999,
        symbian_version="Nokia OS (S30)",
        screen=ScreenSpec(width=84, height=48, bpp=1),
        hardware=HardwareSpec(cpu="MAD2", cpu_mhz=13, ram_mb=1, rom_mb=2),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=True,
        description="First internal antenna, 160M sold, Snake",
        colors=["Grey"]
    ),
    NokiaDevice(
        id="nokia_3650",
        name="Nokia 3650",
        family=DeviceFamily.S60,
        year=2003,
        symbian_version="S60 1st Edition (Symbian OS 6.1)",
        screen=ScreenSpec(width=176, height=208, bpp=12),
        hardware=HardwareSpec(cpu="ARM9", cpu_mhz=104, ram_mb=4, rom_mb=16, has_bt=True, has_camera=True, camera_mp=0.3),
        keypad=KeypadLayout(type=InputType.KEYPAD),
        iconic=False,
        description="First US S60 phone, circular keypad",
        colors=["Yellow"]
    ),
    NokiaDevice(
        id="nokia_n900",
        name="Nokia N900",
        family=DeviceFamily.S60,
        year=2009,
        symbian_version="Maemo 5 (Linux)",
        screen=ScreenSpec(width=800, height=480, bpp=24, touch=True),
        hardware=HardwareSpec(cpu="Cortex-A8", cpu_mhz=600, ram_mb=256, rom_mb=32768, has_wifi=True, has_bt=True, has_gps=True, has_camera=True, camera_mp=5.0),
        keypad=KeypadLayout(type=InputType.QWERTY, has_qwerty=True),
        iconic=True,
        description="Maemo Linux, slide QWERTY, Firefox, last Maemo",
        colors=["Black"]
    ),
]

class DeviceRegistry:
    def __init__(self):
        self.devices: Dict[str, NokiaDevice] = {d.id: d for d in DEVICES}

    def get(self, device_id: str) -> Optional[NokiaDevice]:
        return self.devices.get(device_id)

    def list_all(self) -> List[NokiaDevice]:
        return list(self.devices.values())

    def list_iconic(self) -> List[NokiaDevice]:
        return [d for d in self.devices.values() if d.iconic]

    def list_by_family(self, family: DeviceFamily) -> List[NokiaDevice]:
        return [d for d in self.devices.values() if d.family == family]

    def search(self, query: str) -> List[NokiaDevice]:
        q = query.lower()
        return [d for d in self.devices.values() if q in d.name.lower() or q in d.id.lower() or q in d.description.lower()]

    def to_dict_list(self) -> List[Dict]:
        return [d.to_dict() for d in self.devices.values()]

# Global registry
_registry = DeviceRegistry()

def get_device(device_id: str) -> Optional[NokiaDevice]:
    return _registry.get(device_id)

def list_devices() -> List[NokiaDevice]:
    return _registry.list_all()

def list_iconic() -> List[NokiaDevice]:
    return _registry.list_iconic()
