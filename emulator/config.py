"""
Global configuration for OldPhoneEmulator
"""
import os
from pathlib import Path

def _get_base_dir():
    # Handle zipapp / pyz case where __file__ is inside zip
    try:
        base = Path(__file__).parent.parent
        # Check if base is inside a zip file (contains .pyz or .zip in path)
        if ".pyz" in str(base) or ".zip" in str(base):
            # Use current working directory or home
            cwd_base = Path.cwd()
            # If cwd is dist, use parent
            if cwd_base.name == "dist":
                cwd_base = cwd_base.parent
            return cwd_base
        # Check if writable
        if not os.access(base, os.W_OK):
            return Path.cwd()
        return base
    except Exception:
        return Path.cwd()

BASE_DIR = _get_base_dir()
ROMS_DIR = BASE_DIR / "roms"
ASSETS_DIR = BASE_DIR / "assets"
CACHE_DIR = BASE_DIR / ".cache"

# Ensure dirs exist (ignore errors for zipapp)
try:
    ROMS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
except Exception:
    # Fallback to home directory
    try:
        home_base = Path.home() / ".oldphoneemulator"
        home_base.mkdir(exist_ok=True)
        ROMS_DIR = home_base / "roms"
        ASSETS_DIR = home_base / "assets"
        CACHE_DIR = home_base / ".cache"
        ROMS_DIR.mkdir(exist_ok=True)
        ASSETS_DIR.mkdir(exist_ok=True)
        CACHE_DIR.mkdir(exist_ok=True)
        BASE_DIR = home_base
    except Exception:
        pass

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
