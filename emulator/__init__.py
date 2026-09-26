"""
OldPhoneEmulator - A cross-platform Symbian OS / Nokia OS Emulator
Supports ROMs, SIS/SISX, JAR, Windows EXE, Linux ELF, and disk images.
"""
__version__ = "1.0.0"
__author__ = "OldPhoneEmulator Team"

from .core.rom_loader import RomLoader, RomImage, RomType
from .devices.nokia_profiles import DeviceRegistry
from .core.memory import Memory
from .core.cpu_arm import ARMv5CPU

__all__ = ["RomLoader", "RomImage", "RomType", "DeviceRegistry", "Memory", "ARMv5CPU"]
