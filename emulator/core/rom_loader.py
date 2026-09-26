"""
ROM Loader - Supports any kind of ROM, Symbian, Nokia, Windows, Linux
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib
import struct
import zipfile
import io

from ..formats.sis import SisParser
from ..formats.exe_pe import PeParser
from ..formats.elf import ElfParser
from ..formats.jar import JarParser
from ..formats.iso import IsoParser

class RomType(Enum):
    UNKNOWN = "unknown"
    # Symbian ROMs
    SYMBIAN_ROFS = "symbian_rofs"  # Read Only File System
    SYMBIAN_ROFS2 = "symbian_rofs2"
    SYMBIAN_ROFS3 = "symbian_rofs3"
    SYMBIAN_UDA = "symbian_uda"  # User Data Area
    SYMBIAN_CORE = "symbian_core"
    SYMBIAN_ROM = "symbian_rom"  # Full ROM image
    # Nokia specific
    NOKIA_MCU = "nokia_mcu"  # MCU Software
    NOKIA_PPM = "nokia_ppm"  # Post Programmable Memory (language pack)
    NOKIA_CNT = "nokia_cnt"  # Content
    NOKIA_FPSX = "nokia_fpsx"  # Flash file
    NOKIA_DCP = "nokia_dcp"
    # Packages
    SIS = "sis"
    SISX = "sisx"
    JAR = "jar"
    JAD = "jad"
    # Executables
    PE_EXE = "pe_exe"
    ELF = "elf"
    # Disk images
    ISO = "iso"
    VHD = "vhd"
    QCOW = "qcow"
    IMG = "img"
    # Archives
    ZIP = "zip"

@dataclass
class RomImage:
    path: Path
    rom_type: RomType
    size: int
    md5: str
    sha1: str
    entry_point: int = 0x40000000
    load_address: int = 0x40000000
    metadata: Dict = field(default_factory=dict)
    raw_data: bytes = field(default_factory=bytes, repr=False)
    parsed: Optional[object] = None  # Parsed object (SIS, PE, etc)

    def to_dict(self):
        return {
            "path": str(self.path),
            "type": self.rom_type.value,
            "size": self.size,
            "md5": self.md5,
            "sha1": self.sha1,
            "entry_point": f"0x{self.entry_point:X}",
            "load_address": f"0x{self.load_address:X}",
            "metadata": self.metadata
        }

class RomLoader:
    """
    Universal ROM loader that supports any kind of ROM
    - Symbian OS ROMs (ROFS, UDA, CORE)
    - Nokia flash files (MCU, PPM, FPSX)
    - App packages (SIS, SISX, JAR)
    - Windows EXE (PE)
    - Linux ELF
    - Disk images (ISO, VHD, QCOW, IMG)
    """

    # Known Symbian ROM signatures
    ROM_SIGNATURES = {
        b"ROFS": RomType.SYMBIAN_ROFS,
        b"Rofs": RomType.SYMBIAN_ROFS,
        b"Symbian": RomType.SYMBIAN_ROM,
        b"EPOC": RomType.SYMBIAN_ROM,
        b"E32": RomType.SYMBIAN_ROM,
    }

    @staticmethod
    def detect_type(data: bytes, path: Path) -> RomType:
        ext = path.suffix.lower()

        # Extension based first
        ext_map = {
            ".rofs": RomType.SYMBIAN_ROFS,
            ".rofs2": RomType.SYMBIAN_ROFS2,
            ".rofs3": RomType.SYMBIAN_ROFS3,
            ".uda": RomType.SYMBIAN_UDA,
            ".core": RomType.SYMBIAN_CORE,
            ".rom": RomType.SYMBIAN_ROM,
            ".bin": RomType.SYMBIAN_ROM,
            ".fpsx": RomType.NOKIA_FPSX,
            ".mcu": RomType.NOKIA_MCU,
            ".mcusw": RomType.NOKIA_MCU,
            ".ppm": RomType.NOKIA_PPM,
            ".cnt": RomType.NOKIA_CNT,
            ".dcp": RomType.NOKIA_DCP,
            ".vpl": RomType.NOKIA_DCP,
            ".sis": RomType.SIS,
            ".sisx": RomType.SISX,
            ".jar": RomType.JAR,
            ".jad": RomType.JAD,
            ".exe": RomType.PE_EXE,
            ".dll": RomType.PE_EXE,
            ".elf": RomType.ELF,
            ".out": RomType.ELF,
            ".iso": RomType.ISO,
            ".vhd": RomType.VHD,
            ".vhdx": RomType.VHD,
            ".qcow": RomType.QCOW,
            ".qcow2": RomType.QCOW,
            ".img": RomType.IMG,
            ".zip": RomType.ZIP,
        }

        # Magic detection overrides extension
        if len(data) >= 4:
            if data[:2] == b'MZ':
                return RomType.PE_EXE
            if data[:4] == b'\x7fELF':
                return RomType.ELF
            if data[:2] == b'PK':
                # Could be SISX, JAR, ZIP
                if ext in [".sisx", ".sis"]:
                    return RomType.SISX
                if ext == ".jar":
                    return RomType.JAR
                # Try to detect inside
                try:
                    z = zipfile.ZipFile(io.BytesIO(data))
                    names = [n.lower() for n in z.namelist()]
                    if any('meta-inf' in n and n.endswith('.mf') for n in names):
                        # Check for MIDlet
                        if any('.class' in n for n in names):
                            return RomType.JAR
                        return RomType.SISX
                except:
                    pass
                return RomType.ZIP
            # ISO
            if len(data) >= 0x9000 and (data[0x8001:0x8006] == b'CD001' or data[0x8801:0x8806] == b'CD001'):
                return RomType.ISO
            # QCOW
            if data[:4] == b'QFI\xfb':
                return RomType.QCOW
            # VHD
            if len(data) >= 512 and data[-512:].find(b'conectix') != -1:
                return RomType.VHD

            # Symbian ROM magic
            for sig, rtype in RomLoader.ROM_SIGNATURES.items():
                if sig in data[:1024]:
                    return rtype

        # Fallback to extension
        if ext in ext_map:
            return ext_map[ext]

        # Check for Nokia FPSX (XML-like header)
        if data[:100].strip().startswith(b'<?xml') and b'flash' in data[:1000].lower():
            return RomType.NOKIA_FPSX

        # Default: if .bin/.img and large, treat as ROM
        if ext in [".bin", ".img", ".raw"]:
            if len(data) > 1024*1024:  # >1MB likely ROM
                return RomType.SYMBIAN_ROM
            return RomType.IMG

        return RomType.UNKNOWN

    @staticmethod
    def load(path: Path) -> RomImage:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"ROM not found: {path}")

        data = path.read_bytes()
        rom_type = RomLoader.detect_type(data, path)

        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()

        metadata = {}
        parsed = None
        entry_point = 0x40000000
        load_address = 0x40000000

        try:
            if rom_type in [RomType.SIS, RomType.SISX]:
                parsed = SisParser.parse(data, path.name)
                metadata = parsed.to_dict()
                entry_point = 0x30000000
                load_address = 0x30000000
            elif rom_type == RomType.JAR:
                parsed = JarParser.parse(data, path.name)
                metadata = parsed.to_dict()
                entry_point = 0x30000000
            elif rom_type == RomType.PE_EXE:
                parsed = PeParser.parse(data)
                metadata = parsed.to_dict()
                entry_point = parsed.image_base + parsed.entry_point
                load_address = parsed.image_base
            elif rom_type == RomType.ELF:
                parsed = ElfParser.parse(data)
                metadata = parsed.to_dict()
                entry_point = parsed.entry
                load_address = parsed.entry & ~0xFFF
            elif rom_type == RomType.ISO:
                parsed = IsoParser.parse(data)
                metadata = parsed.to_dict()
            elif rom_type in [RomType.SYMBIAN_ROM, RomType.SYMBIAN_ROFS, RomType.NOKIA_MCU]:
                # Try to find entry point from ROM header
                # Symbian ROM header: first 0x100 bytes contains info
                if len(data) >= 0x100:
                    # Look for EPOC header
                    try:
                        # ROM header structure is complex - simplified
                        # Usually entry point is at offset 0x20 or similar
                        if len(data) >= 0x24:
                            ep = struct.unpack("<I", data[0x20:0x24])[0]
                            if 0x40000000 <= ep < 0x50000000:
                                entry_point = ep
                    except:
                        pass
                metadata = {
                    "rom_size": len(data),
                    "is_symbian": True,
                    "detected_strings": RomLoader._extract_strings(data[:4096])
                }
        except Exception as e:
            metadata["parse_error"] = str(e)
            # Still return ROM, just with error

        return RomImage(
            path=path,
            rom_type=rom_type,
            size=len(data),
            md5=md5,
            sha1=sha1,
            entry_point=entry_point,
            load_address=load_address,
            metadata=metadata,
            raw_data=data,
            parsed=parsed
        )

    @staticmethod
    def _extract_strings(data: bytes, min_len: int = 4) -> List[str]:
        strings = []
        cur = bytearray()
        for b in data:
            if 32 <= b < 127:
                cur.append(b)
            else:
                if len(cur) >= min_len:
                    try:
                        strings.append(cur.decode('ascii'))
                    except:
                        pass
                cur = bytearray()
        if len(cur) >= min_len:
            try:
                strings.append(cur.decode('ascii'))
            except:
                pass
        return strings[:20]  # Limit

    @staticmethod
    def load_directory(dir_path: Path) -> List[RomImage]:
        dir_path = Path(dir_path)
        roms = []
        for file in dir_path.iterdir():
            if file.is_file():
                # Skip hidden and small files
                if file.name.startswith('.'):
                    continue
                if file.stat().st_size < 100:
                    continue
                try:
                    rom = RomLoader.load(file)
                    roms.append(rom)
                except Exception as e:
                    print(f"[RomLoader] Failed to load {file}: {e}")
        return roms

    @staticmethod
    def get_supported_extensions() -> List[str]:
        return [".rom", ".bin", ".img", ".rofs", ".uda", ".core", ".md0",
                ".fpsx", ".vpl", ".dcp", ".mcusw", ".ppm",
                ".sis", ".sisx", ".jar", ".jad",
                ".exe", ".dll", ".elf",
                ".iso", ".vhd", ".qcow", ".zip"]
