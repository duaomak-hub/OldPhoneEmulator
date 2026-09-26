"""
ISO / Disk image parser for Windows/Linux disks
"""
import struct
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class IsoFile:
    name: str
    size: int
    is_dir: bool
    lba: int

@dataclass
class IsoInfo:
    system_id: str
    volume_id: str
    volume_size: int
    files: List[IsoFile]
    bootable: bool
    raw_data: bytes

    def to_dict(self):
        return {
            "system": self.system_id,
            "volume": self.volume_id,
            "size": self.volume_size,
            "files": len(self.files),
            "bootable": self.bootable
        }

class IsoParser:
    @staticmethod
    def is_iso(data: bytes) -> bool:
        if len(data) < 0x9000:
            return False
        # ISO9660 has "CD001" at 0x8001, 0x8801, 0x9001
        return data[0x8001:0x8006] == b'CD001' or data[0x8801:0x8806] == b'CD001'

    @staticmethod
    def parse(data: bytes) -> IsoInfo:
        if len(data) < 0x9000:
            raise ValueError("Too small for ISO")

        # Primary Volume Descriptor at 0x8000
        pvd = data[0x8000:0x8800]
        if len(pvd) < 2048:
            raise ValueError("Invalid PVD")

        system_id = pvd[8:40].decode('ascii', errors='ignore').strip()
        volume_id = pvd[40:72].decode('ascii', errors='ignore').strip()
        volume_size = struct.unpack("<I", pvd[80:84])[0] if len(pvd) >= 84 else 0

        # Bootable check - boot record at 0x8000? Actually boot catalog
        bootable = False
        try:
            # Look for boot descriptor
            for sector in [0x8000, 0x8800, 0x9000]:
                if sector+2048 <= len(data):
                    desc = data[sector:sector+2048]
                    if desc[0] == 0 and desc[1:6] == b'CD001' and desc[6] == 1:
                        # Boot record
                        if b'EL TORITO' in desc:
                            bootable = True
        except:
            pass

        files = []
        try:
            # Root directory entry at offset 156 in PVD
            # Simplified file listing - parse root dir
            root_lba = struct.unpack("<I", pvd[158:162])[0] if len(pvd) >= 162 else 0
            root_size = struct.unpack("<I", pvd[166:170])[0] if len(pvd) >= 170 else 0

            if root_lba and root_size and root_lba*2048 + root_size <= len(data):
                root_data = data[root_lba*2048: root_lba*2048 + root_size]
                offset = 0
                while offset < len(root_data):
                    if offset+1 >= len(root_data):
                        break
                    dr_len = root_data[offset]
                    if dr_len == 0:
                        break
                    if offset + dr_len > len(root_data):
                        break
                    # Parse directory record
                    try:
                        file_flags = root_data[offset+25] if offset+25 < len(root_data) else 0
                        file_lba = struct.unpack("<I", root_data[offset+2:offset+6])[0] if offset+6 <= len(root_data) else 0
                        file_size = struct.unpack("<I", root_data[offset+10:offset+14])[0] if offset+14 <= len(root_data) else 0
                        file_id_len = root_data[offset+32] if offset+32 < len(root_data) else 0
                        if offset+33+file_id_len <= len(root_data):
                            file_id = root_data[offset+33:offset+33+file_id_len]
                            # Skip . and ..
                            if file_id not in [b'\x00', b'\x01']:
                                name = file_id.decode('ascii', errors='ignore').split(';')[0]
                                files.append(IsoFile(
                                    name=name,
                                    size=file_size,
                                    is_dir=(file_flags & 2) != 0,
                                    lba=file_lba
                                ))
                    except:
                        pass
                    offset += dr_len
        except Exception as e:
            # Fallback
            pass

        return IsoInfo(
            system_id=system_id,
            volume_id=volume_id,
            volume_size=volume_size,
            files=files,
            bootable=bootable,
            raw_data=data
        )
