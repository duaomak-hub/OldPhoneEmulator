"""
Disk image handling for Windows/Linux disks
Supports ISO, VHD, QCOW, IMG, FAT, etc.
"""
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
import struct

class DiskType(Enum):
    UNKNOWN = "unknown"
    ISO = "iso"
    VHD = "vhd"
    VHDX = "vhdx"
    QCOW = "qcow"
    QCOW2 = "qcow2"
    VMDK = "vmdk"
    RAW = "raw"
    FAT12 = "fat12"
    FAT16 = "fat16"
    FAT32 = "fat32"
    NTFS = "ntfs"
    EXT4 = "ext4"

@dataclass
class Partition:
    index: int
    type: str
    start_lba: int
    size_sectors: int
    bootable: bool
    fs_type: str

@dataclass
class DiskInfo:
    path: Path
    disk_type: DiskType
    size: int
    sector_size: int
    partitions: List[Partition]
    bootable: bool
    fs_type: str
    label: str

    def to_dict(self):
        return {
            "path": str(self.path),
            "type": self.disk_type.value,
            "size": self.size,
            "sector_size": self.sector_size,
            "partitions": len(self.partitions),
            "bootable": self.bootable,
            "fs": self.fs_type,
            "label": self.label
        }

class DiskImage:
    """
    Disk image parser and mounter
    Supports MBR, GPT, FAT, ISO9660 detection
    """

    @staticmethod
    def detect_type(data: bytes, path: Path) -> DiskType:
        ext = path.suffix.lower()
        if ext == ".iso":
            return DiskType.ISO
        if ext in [".vhd", ".avhd"]:
            return DiskType.VHD
        if ext == ".vhdx":
            return DiskType.VHDX
        if ext in [".qcow", ".qcow2"]:
            return DiskType.QCOW2
        if ext == ".vmdk":
            return DiskType.VMDK

        if len(data) < 512:
            return DiskType.UNKNOWN

        # Check MBR signature
        if data[510:512] == b'\x55\xAA':
            # Check FAT boot sector
            if data[0:3] == b'\xEB\x3C\x90' or data[0:3] == b'\xEB\x58\x90':
                # FAT
                fs_type = data[54:62].decode('ascii', errors='ignore').strip()
                if 'FAT12' in fs_type:
                    return DiskType.FAT12
                if 'FAT16' in fs_type:
                    return DiskType.FAT16
                if 'FAT32' in fs_type or data[82:90].decode('ascii', errors='ignore').strip().startswith('FAT32'):
                    return DiskType.FAT32
            return DiskType.RAW

        # ISO
        if len(data) >= 0x9000 and (data[0x8001:0x8006] == b'CD001' or data[0x8801:0x8806] == b'CD001'):
            return DiskType.ISO

        # QCOW
        if data[:4] == b'QFI\xfb':
            return DiskType.QCOW2

        # VHD footer check (last 512 bytes)
        if len(data) >= 512:
            footer = data[-512:]
            if b'conectix' in footer.lower():
                return DiskType.VHD

        return DiskType.RAW

    @staticmethod
    def parse_mbr(data: bytes) -> List[Partition]:
        partitions = []
        if len(data) < 512 or data[510:512] != b'\x55\xAA':
            return partitions

        for i in range(4):
            offset = 446 + i*16
            if offset+16 > len(data):
                break
            entry = data[offset:offset+16]
            if len(entry) < 16:
                continue
            bootable = entry[0] == 0x80
            part_type = entry[4]
            if part_type == 0:
                continue  # Empty
            start_lba = struct.unpack("<I", entry[8:12])[0]
            size_sectors = struct.unpack("<I", entry[12:16])[0]

            # Map type to FS
            fs_map = {
                0x01: "FAT12", 0x04: "FAT16", 0x06: "FAT16", 0x0B: "FAT32",
                0x0C: "FAT32", 0x07: "NTFS", 0x83: "EXT", 0x82: "SWAP",
                0x0F: "EXTENDED", 0x05: "EXTENDED"
            }
            fs_type = fs_map.get(part_type, f"UNKNOWN(0x{part_type:02X})")
            type_name = f"0x{part_type:02X}"

            partitions.append(Partition(
                index=i,
                type=type_name,
                start_lba=start_lba,
                size_sectors=size_sectors,
                bootable=bootable,
                fs_type=fs_type
            ))
        return partitions

    @staticmethod
    def parse(data: bytes, path: Path) -> DiskInfo:
        disk_type = DiskImage.detect_type(data, path)
        size = len(data)
        sector_size = 512
        partitions = []
        bootable = False
        fs_type = "UNKNOWN"
        label = ""

        try:
            if len(data) >= 512 and data[510:512] == b'\x55\xAA':
                bootable = True
                partitions = DiskImage.parse_mbr(data)

            # Try to detect FS from boot sector
            if len(data) >= 512:
                # FAT label at offset 43 for FAT12/16, 71 for FAT32
                try:
                    label_fat16 = data[43:54].decode('ascii', errors='ignore').strip()
                    if label_fat16 and label_fat16 != "NO NAME":
                        label = label_fat16
                except:
                    pass
                try:
                    if len(data) >= 90:
                        label_fat32 = data[71:82].decode('ascii', errors='ignore').strip()
                        if label_fat32 and label_fat32 != "NO NAME":
                            label = label_fat32
                except:
                    pass

                # NTFS
                if data[3:11] == b'NTFS    ':
                    fs_type = "NTFS"
                    try:
                        label = data[0x50:0x70].decode('utf-16le', errors='ignore').strip('\x00').strip()
                    except:
                        pass

                # EXT superblock at 1024
                if len(data) >= 2048:
                    ext_magic = struct.unpack("<H", data[1024+56:1024+58])[0] if len(data) >= 1024+58 else 0
                    if ext_magic == 0xEF53:
                        fs_type = "EXT4"
                        try:
                            label = data[1024+120:1024+136].decode('ascii', errors='ignore').strip('\x00').strip()
                        except:
                            pass

            # ISO volume label
            if disk_type == DiskType.ISO and len(data) >= 0x8000+72:
                try:
                    pvd = data[0x8000:0x8800]
                    if len(pvd) >= 72:
                        label = pvd[40:72].decode('ascii', errors='ignore').strip()
                        fs_type = "ISO9660"
                except:
                    pass

            if not fs_type or fs_type == "UNKNOWN":
                if partitions:
                    fs_type = partitions[0].fs_type
                else:
                    fs_type = disk_type.value.upper()

        except Exception as e:
            print(f"[Disk] Parse error: {e}")

        return DiskInfo(
            path=path,
            disk_type=disk_type,
            size=size,
            sector_size=sector_size,
            partitions=partitions,
            bootable=bootable,
            fs_type=fs_type,
            label=label or path.stem
        )

    @staticmethod
    def mount(disk_info: DiskInfo, mount_point: Path) -> bool:
        """
        Simulate mounting disk image
        For now just creates mount point and extracts basic info
        Real mounting would need fuse or similar
        """
        try:
            mount_point.mkdir(parents=True, exist_ok=True)
            # Write info file
            info_file = mount_point / ".disk_info"
            info_file.write_text(f"""
Disk: {disk_info.path}
Type: {disk_info.disk_type.value}
Size: {disk_info.size}
FS: {disk_info.fs_type}
Label: {disk_info.label}
Bootable: {disk_info.bootable}
Partitions: {len(disk_info.partitions)}
            """.strip())
            return True
        except Exception as e:
            print(f"[Disk] Mount failed: {e}")
            return False
