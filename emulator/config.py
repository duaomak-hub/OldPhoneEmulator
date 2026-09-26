"""
Global configuration for OldPhoneEmulator
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROMS_DIR = BASE_DIR / "roms"
ASSETS_DIR = BASE_DIR / "assets"
CACHE_DIR = BASE_DIR / ".cache"

# Ensure dirs exist
ROMS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Emulator defaults
DEFAULT_DEVICE = "nokia_n95"
DEFAULT_RAM_MB = 64
DEFAULT_SCREEN_SCALE = 2

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    # Symbian / Nokia ROMs
    ".rom", ".bin", ".img", ".rofs", ".uda", ".core", ".md0",
    ".fpsx", ".vpl", ".dcp", ".mcusw", ".ppm",
    # App packages
    ".sis", ".sisx", ".jar", ".jad", ".app", ".n-gage", ".ngage",
    # Generic executables
    ".exe", ".dll", ".elf", ".out", ".so",
    # Disk images
    ".iso", ".vhd", ".vhdx", ".qcow", ".qcow2", ".vmdk", ".raw", ".fat", ".dmg",
    # Archives that may contain ROMs
    ".zip", ".7z", ".rar", ".tar", ".gz"
}

# MIME / magic mapping
MAGIC_SIGNATURES = {
    b"MZ": "pe_exe",
    b"\x7fELF": "elf",
    b"\x53\x49\x53\x20": "sis_old",  # SIS
    b"PK\x03\x04": "zip",  # SISX and JAR are ZIP
    b"\x43\x44\x30\x30\x31": "iso",
    b"conectix": "vhd",
    b"QFI\xfb": "qcow",
    b"KDMV": "vmdk",
}

# Symbian OS versions
SYMBIAN_VERSIONS = [
    "S60 1st Edition (Symbian OS 6.1)",
    "S60 2nd Edition (Symbian OS 7.0s)",
    "S60 2nd Edition FP3 (Symbian OS 8.1a)",
    "S60 3rd Edition (Symbian OS 9.1)",
    "S60 3rd Edition FP1 (Symbian OS 9.2)",
    "S60 3rd Edition FP2 (Symbian OS 9.3)",
    "S60 5th Edition (Symbian OS 9.4)",
    "Symbian^3 (Symbian OS 9.5)",
    "Symbian Anna",
    "Symbian Belle",
    "Nokia Series 30",
    "Nokia Series 40",
    "Nokia Asha Platform"
]
