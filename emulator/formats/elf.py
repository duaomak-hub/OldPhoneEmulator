"""
ELF parser for Linux binaries support
"""
import struct
from dataclasses import dataclass
from typing import List

@dataclass
class ElfSection:
    name: str
    type: int
    flags: int
    addr: int
    offset: int
    size: int

@dataclass
class ElfProgram:
    type: int
    offset: int
    vaddr: int
    filesz: int
    memsz: int
    flags: int

@dataclass
class ElfInfo:
    is_64bit: bool
    is_little: bool
    arch: str
    entry: int
    sections: List[ElfSection]
    programs: List[ElfProgram]
    is_symbian_elf: bool
    raw_data: bytes

    def to_dict(self):
        return {
            "arch": self.arch,
            "bits": 64 if self.is_64bit else 32,
            "entry": f"0x{self.entry:X}",
            "sections": len(self.sections),
            "programs": len(self.programs),
            "symbian": self.is_symbian_elf
        }

class ElfParser:
    ARCH_MAP = {
        0x02: "SPARC",
        0x03: "x86",
        0x08: "MIPS",
        0x14: "PowerPC",
        0x28: "ARM",
        0x2A: "SuperH",
        0x32: "IA-64",
        0x3E: "x86-64",
        0xB7: "AArch64",
        0xF3: "RISC-V"
    }

    @staticmethod
    def is_elf(data: bytes) -> bool:
        return data[:4] == b'\x7fELF'

    @staticmethod
    def parse(data: bytes) -> ElfInfo:
        if len(data) < 52:
            raise ValueError("Too small for ELF")
        if data[:4] != b'\x7fELF':
            raise ValueError("Not ELF")

        is_64 = data[4] == 2
        is_little = data[5] == 1
        endian = "<" if is_little else ">"

        if is_64:
            if len(data) < 64:
                raise ValueError("Too small for ELF64")
            e_type, e_machine = struct.unpack(endian+"HH", data[16:20])
            e_entry = struct.unpack(endian+"Q", data[24:32])[0]
            e_phoff = struct.unpack(endian+"Q", data[32:40])[0]
            e_shoff = struct.unpack(endian+"Q", data[40:48])[0]
            e_phentsize, e_phnum = struct.unpack(endian+"HH", data[54:58])
            e_shentsize, e_shnum = struct.unpack(endian+"HH", data[58:62])
        else:
            e_type, e_machine = struct.unpack(endian+"HH", data[16:20])
            e_entry = struct.unpack(endian+"I", data[24:28])[0]
            e_phoff = struct.unpack(endian+"I", data[28:32])[0]
            e_shoff = struct.unpack(endian+"I", data[32:36])[0]
            e_phentsize, e_phnum = struct.unpack(endian+"HH", data[42:46])
            e_shentsize, e_shnum = struct.unpack(endian+"HH", data[46:50])

        arch = ElfParser.ARCH_MAP.get(e_machine, f"UNKNOWN(0x{e_machine:X})")

        programs = []
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            if off + e_phentsize > len(data):
                break
            if is_64:
                p_type, p_flags = struct.unpack(endian+"II", data[off:off+8])
                p_offset = struct.unpack(endian+"Q", data[off+8:off+16])[0]
                p_vaddr = struct.unpack(endian+"Q", data[off+16:off+24])[0]
                p_filesz = struct.unpack(endian+"Q", data[off+32:off+40])[0]
                p_memsz = struct.unpack(endian+"Q", data[off+40:off+48])[0]
            else:
                p_type = struct.unpack(endian+"I", data[off:off+4])[0]
                p_offset = struct.unpack(endian+"I", data[off+4:off+8])[0]
                p_vaddr = struct.unpack(endian+"I", data[off+8:off+12])[0]
                p_filesz = struct.unpack(endian+"I", data[off+16:off+20])[0]
                p_memsz = struct.unpack(endian+"I", data[off+20:off+24])[0]
                p_flags = struct.unpack(endian+"I", data[off+24:off+28])[0]
            programs.append(ElfProgram(p_type, p_offset, p_vaddr, p_filesz, p_memsz, p_flags))

        sections = []
        # Simplified - not parsing section names without strtab
        for i in range(min(e_shnum, 100)):  # limit
            off = e_shoff + i * e_shentsize
            if off + e_shentsize > len(data):
                break
            if is_64:
                sh_type = struct.unpack(endian+"I", data[off+4:off+8])[0]
                sh_flags = struct.unpack(endian+"Q", data[off+8:off+16])[0]
                sh_addr = struct.unpack(endian+"Q", data[off+16:off+24])[0]
                sh_offset = struct.unpack(endian+"Q", data[off+24:off+32])[0]
                sh_size = struct.unpack(endian+"Q", data[off+32:off+40])[0]
            else:
                sh_type = struct.unpack(endian+"I", data[off+4:off+8])[0]
                sh_flags = struct.unpack(endian+"I", data[off+8:off+12])[0]
                sh_addr = struct.unpack(endian+"I", data[off+12:off+16])[0]
                sh_offset = struct.unpack(endian+"I", data[off+16:off+20])[0]
                sh_size = struct.unpack(endian+"I", data[off+20:off+24])[0]
            sections.append(ElfSection(f"sec_{i}", sh_type, sh_flags, sh_addr, sh_offset, sh_size))

        is_symbian = b"Symbian" in data or b"EPOC" in data or b"E32" in data[:1000]

        return ElfInfo(
            is_64bit=is_64,
            is_little=is_little,
            arch=arch,
            entry=e_entry,
            sections=sections,
            programs=programs,
            is_symbian_elf=is_symbian,
            raw_data=data
        )
