"""
Memory subsystem for Symbian emulator
Implements Symbian OS memory map with ROM, RAM, IO regions
"""
from dataclasses import dataclass
from typing import Dict, Optional, List
import struct

class MemoryAccessError(Exception):
    pass

@dataclass
class MemoryRegion:
    name: str
    base: int
    size: int
    readable: bool = True
    writable: bool = True
    executable: bool = False
    is_rom: bool = False
    data: bytearray = None

    def __post_init__(self):
        if self.data is None:
            self.data = bytearray(self.size)
        elif len(self.data) < self.size:
            self.data = bytearray(self.data) + bytearray(self.size - len(self.data))

    def contains(self, addr: int) -> bool:
        return self.base <= addr < self.base + self.size

    def offset(self, addr: int) -> int:
        return addr - self.base

class Memory:
    """
    Symbian OS memory map
    Typical layout:
    0x00000000 - ROM (boot)
    0x30000000 - RAM (user)
    0x40000000 - ROM (main)
    0x50000000 - IO / Hardware registers
    0x70000000 - Shared heap
    0x80000000 - Kernel
    """
    def __init__(self, ram_size: int = 64 * 1024 * 1024):
        self.ram_size = ram_size
        self.regions: List[MemoryRegion] = []
        self._init_default_map()

    def _init_default_map(self):
        # Boot ROM - 4MB
        self.add_region(MemoryRegion(
            name="BOOT_ROM",
            base=0x00000000,
            size=4 * 1024 * 1024,
            readable=True,
            writable=False,
            executable=True,
            is_rom=True
        ))
        # User RAM
        self.add_region(MemoryRegion(
            name="RAM",
            base=0x30000000,
            size=self.ram_size,
            readable=True,
            writable=True,
            executable=True
        ))
        # Main ROM - 64MB (Symbian ROM)
        self.add_region(MemoryRegion(
            name="MAIN_ROM",
            base=0x40000000,
            size=64 * 1024 * 1024,
            readable=True,
            writable=False,
            executable=True,
            is_rom=True
        ))
        # IO Region
        self.add_region(MemoryRegion(
            name="IO",
            base=0x50000000,
            size=16 * 1024 * 1024,
            readable=True,
            writable=True,
            executable=False
        ))
        # Video RAM
        self.add_region(MemoryRegion(
            name="VRAM",
            base=0x60000000,
            size=4 * 1024 * 1024,
            readable=True,
            writable=True,
            executable=False
        ))
        # Kernel
        self.add_region(MemoryRegion(
            name="KERNEL",
            base=0x80000000,
            size=16 * 1024 * 1024,
            readable=True,
            writable=True,
            executable=True
        ))

    def add_region(self, region: MemoryRegion):
        self.regions.append(region)
        self.regions.sort(key=lambda r: r.base)

    def find_region(self, addr: int) -> Optional[MemoryRegion]:
        for r in self.regions:
            if r.contains(addr):
                return r
        return None

    def load_rom(self, data: bytes, base: int = 0x40000000, name: str = "MAIN_ROM"):
        region = self.find_region(base)
        if region is None:
            region = MemoryRegion(name=name, base=base, size=len(data), readable=True, writable=False, executable=True, is_rom=True, data=bytearray(data))
            self.add_region(region)
        else:
            # Overwrite existing
            size = min(len(data), region.size)
            region.data[:size] = data[:size]
            if len(data) > region.size:
                # Expand if needed
                region.data.extend(data[region.size:])
                region.size = len(region.data)

    def read(self, addr: int, size: int) -> bytes:
        region = self.find_region(addr)
        if region is None:
            raise MemoryAccessError(f"Read from unmapped address 0x{addr:08X}")
        if not region.readable:
            raise MemoryAccessError(f"Read from non-readable region {region.name} at 0x{addr:08X}")
        if addr + size > region.base + region.size:
            # Cross-region read - handle as multiple reads
            result = bytearray()
            remaining = size
            cur_addr = addr
            while remaining > 0:
                r = self.find_region(cur_addr)
                if r is None:
                    raise MemoryAccessError(f"Read crosses unmapped at 0x{cur_addr:08X}")
                avail = r.base + r.size - cur_addr
                chunk = min(avail, remaining)
                off = r.offset(cur_addr)
                result.extend(r.data[off:off+chunk])
                cur_addr += chunk
                remaining -= chunk
            return bytes(result)
        off = region.offset(addr)
        return bytes(region.data[off:off+size])

    def write(self, addr: int, data: bytes):
        region = self.find_region(addr)
        if region is None:
            raise MemoryAccessError(f"Write to unmapped address 0x{addr:08X}")
        if not region.writable:
            raise MemoryAccessError(f"Write to read-only region {region.name} at 0x{addr:08X}")
        if region.is_rom:
            raise MemoryAccessError(f"Write to ROM region {region.name}")
        off = region.offset(addr)
        region.data[off:off+len(data)] = data

    def read_u8(self, addr: int) -> int:
        return self.read(addr, 1)[0]

    def read_u16(self, addr: int) -> int:
        return struct.unpack("<H", self.read(addr, 2))[0]

    def read_u32(self, addr: int) -> int:
        return struct.unpack("<I", self.read(addr, 4))[0]

    def write_u32(self, addr: int, value: int):
        self.write(addr, struct.pack("<I", value))

    def read_cstring(self, addr: int, max_len: int = 256) -> str:
        result = bytearray()
        for i in range(max_len):
            b = self.read_u8(addr + i)
            if b == 0:
                break
            result.append(b)
        try:
            return result.decode('utf-8', errors='replace')
        except:
            return result.decode('latin1', errors='replace')

    def dump(self, addr: int, size: int = 256) -> str:
        data = self.read(addr, size)
        lines = []
        for i in range(0, size, 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{addr+i:08X}: {hex_part:<48} |{ascii_part}|")
        return "\n".join(lines)

    def get_usage(self) -> Dict:
        return {
            r.name: {
                "base": f"0x{r.base:08X}",
                "size": r.size,
                "used": len([b for b in r.data if b != 0]),
                "type": "ROM" if r.is_rom else "RAM" if r.writable else "IO"
            } for r in self.regions
        }
