"""
PE (Portable Executable) parser for Windows .EXE support
Allows emulator to load and analyze Windows executables for compatibility layer
"""
import struct
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class PeSection:
    name: str
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_ptr: int
    characteristics: int
    data: bytes

@dataclass
class PeImport:
    dll: str
    functions: List[str]

@dataclass
class PeInfo:
    is_64bit: bool
    entry_point: int
    image_base: int
    sections: List[PeSection]
    imports: List[PeImport]
    is_dotnet: bool
    is_symbian_exe: bool  # Some Symbian tools are PE
    machine: str
    subsystem: str
    raw_data: bytes

    def to_dict(self):
        return {
            "arch": "x64" if self.is_64bit else "x86",
            "machine": self.machine,
            "entry_point": f"0x{self.entry_point:X}",
            "image_base": f"0x{self.image_base:X}",
            "sections": len(self.sections),
            "imports": [i.dll for i in self.imports],
            "dotnet": self.is_dotnet,
            "symbian_exe": self.is_symbian_exe,
            "subsystem": self.subsystem
        }

class PeParser:
    MACHINE_TYPES = {
        0x014c: "I386",
        0x0200: "IA64",
        0x8664: "AMD64",
        0x01c0: "ARM",
        0x01c4: "ARMV7",
        0xAA64: "ARM64",
        0x0EBC: "EBC"
    }

    SUBSYSTEMS = {
        0: "UNKNOWN",
        1: "NATIVE",
        2: "WINDOWS_GUI",
        3: "WINDOWS_CUI",
        5: "OS2_CUI",
        7: "POSIX_CUI",
        9: "WINDOWS_CE_GUI",
        10: "EFI_APPLICATION"
    }

    @staticmethod
    def is_pe(data: bytes) -> bool:
        return data[:2] == b'MZ'

    @staticmethod
    def parse(data: bytes) -> PeInfo:
        if len(data) < 0x40:
            raise ValueError("Too small for PE")

        if data[:2] != b'MZ':
            raise ValueError("Not a PE file")

        # e_lfanew at 0x3C
        e_lfanew = struct.unpack("<I", data[0x3C:0x40])[0]
        if e_lfanew + 6 > len(data):
            raise ValueError("Invalid e_lfanew")

        if data[e_lfanew:e_lfanew+4] != b'PE\x00\x00':
            raise ValueError("Invalid PE signature")

        coff_offset = e_lfanew + 4
        machine = struct.unpack("<H", data[coff_offset:coff_offset+2])[0]
        num_sections = struct.unpack("<H", data[coff_offset+2:coff_offset+4])[0]
        opt_header_size = struct.unpack("<H", data[coff_offset+16:coff_offset+18])[0]

        opt_offset = coff_offset + 20
        magic = struct.unpack("<H", data[opt_offset:opt_offset+2])[0]
        is_64 = magic == 0x20b

        if is_64:
            entry_point = struct.unpack("<I", data[opt_offset+16:opt_offset+20])[0]
            image_base = struct.unpack("<Q", data[opt_offset+24:opt_offset+32])[0]
            subsystem = struct.unpack("<H", data[opt_offset+68:opt_offset+70])[0]
            data_dir_offset = opt_offset + 112
        else:
            entry_point = struct.unpack("<I", data[opt_offset+16:opt_offset+20])[0]
            image_base = struct.unpack("<I", data[opt_offset+28:opt_offset+32])[0]
            subsystem = struct.unpack("<H", data[opt_offset+68:opt_offset+70])[0]
            data_dir_offset = opt_offset + 96

        sections = []
        section_offset = opt_offset + opt_header_size
        for i in range(num_sections):
            off = section_offset + i*40
            if off+40 > len(data):
                break
            name = data[off:off+8].rstrip(b'\x00').decode('ascii', errors='ignore')
            v_size = struct.unpack("<I", data[off+8:off+12])[0]
            v_addr = struct.unpack("<I", data[off+12:off+16])[0]
            raw_size = struct.unpack("<I", data[off+16:off+20])[0]
            raw_ptr = struct.unpack("<I", data[off+20:off+24])[0]
            chars = struct.unpack("<I", data[off+36:off+40])[0]
            sec_data = b""
            if raw_ptr and raw_size and raw_ptr + raw_size <= len(data):
                sec_data = data[raw_ptr:raw_ptr+raw_size]
            sections.append(PeSection(name, v_size, v_addr, raw_size, raw_ptr, chars, sec_data))

        # Check for .NET (has metadata)
        is_dotnet = any(s.name == ".text" and b"mscoree" in data.lower() for s in sections) or b"_CorExeMain" in data

        # Check if it's Symbian-related (EPOC)
        is_symbian = b"EPOC" in data or b"Symbian" in data or b"E32" in data

        # Parse imports (simplified)
        imports = []
        try:
            # Import table is data directory 1
            if data_dir_offset + 16 <= len(data):
                import_rva = struct.unpack("<I", data[data_dir_offset+8:data_dir_offset+12])[0]
                import_size = struct.unpack("<I", data[data_dir_offset+12:data_dir_offset+16])[0]
                # For simplicity, just search for DLL names in data
                # Real parser would follow RVAs
                lower = data.lower()
                for dll in [b"kernel32.dll", b"user32.dll", b"ntdll.dll", b"msvcrt.dll", b"euser.dll", b"efsrv.dll"]:
                    if dll in lower:
                        imports.append(PeImport(dll.decode(), []))
        except:
            pass

        return PeInfo(
            is_64bit=is_64,
            entry_point=entry_point,
            image_base=image_base,
            sections=sections,
            imports=imports,
            is_dotnet=is_dotnet,
            is_symbian_exe=is_symbian,
            machine=PeParser.MACHINE_TYPES.get(machine, f"UNKNOWN(0x{machine:X})"),
            subsystem=PeParser.SUBSYSTEMS.get(subsystem, f"UNKNOWN({subsystem})"),
            raw_data=data
        )
