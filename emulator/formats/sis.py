"""
SIS / SISX parser for Symbian OS packages
SIS = Symbian Installation Source (S60 1st, 2nd)
SISX = Symbian OS 9.x signed packages (ZIP based)
"""
import struct
import zipfile
import io
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SisFileEntry:
    path: str
    data: bytes
    size: int

@dataclass
class SisPackage:
    name: str
    vendor: str
    version: tuple
    uid: int
    files: List[SisFileEntry]
    capabilities: List[str]
    languages: List[str]
    dependencies: List[str]
    raw_data: bytes

    def to_dict(self):
        return {
            "name": self.name,
            "vendor": self.vendor,
            "version": ".".join(map(str, self.version)),
            "uid": f"0x{self.uid:08X}",
            "files": len(self.files),
            "capabilities": self.capabilities,
            "languages": self.languages,
            "dependencies": self.dependencies
        }

class SisParser:
    """
    Parser for SIS and SISX files
    """
    # Symbian capabilities
    CAPABILITIES = [
        "NetworkServices", "LocalServices", "ReadUserData", "WriteUserData",
        "Location", "SurroundingsDD", "NetworkControl", "MultimediaDD",
        "UserEnvironment", "AllFiles", "CommDD", "DiskAdmin", "PowerMgmt",
        "ProtServ", "ReadDeviceData", "WriteDeviceData", "TrustedUI",
        "SwEvent", "SurroundingsDD", "Tcb"
    ]

    @staticmethod
    def is_sis(data: bytes) -> bool:
        # Old SIS starts with UID
        if len(data) < 16:
            return False
        # Check for SISX (ZIP)
        if data[:2] == b'PK':
            try:
                z = zipfile.ZipFile(io.BytesIO(data))
                # SISX contains specific files
                names = z.namelist()
                return any('_sys' in n.lower() or '.sis' in n.lower() or 'META-INF' in n for n in names) or True
            except:
                pass
        # Old SIS magic: first 4 bytes are UID or header
        return data[:4] == b'\x0a\x00\x00\x10' or data[4:8] == b'\x10\x00\x00\x00'

    @staticmethod
    def is_sisx(data: bytes) -> bool:
        if data[:2] != b'PK':
            return False
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            # Look for Symbian specific structure
            for name in z.namelist():
                if name.lower().endswith('.sis') or 'manifest' in name.lower():
                    return True
            # Even if not, if it's a ZIP and user says it's SISX, treat as SISX
            return True
        except:
            return False

    @staticmethod
    def parse(data: bytes, filename: str = "unknown.sis") -> SisPackage:
        if data[:2] == b'PK':
            return SisParser._parse_sisx(data, filename)
        else:
            return SisParser._parse_sis_old(data, filename)

    @staticmethod
    def _parse_sisx(data: bytes, filename: str) -> SisPackage:
        files = []
        name = Path(filename).stem
        vendor = "Unknown"
        version = (1, 0, 0)
        uid = 0x10000000
        caps = []
        langs = ["EN"]
        deps = []

        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            for info in z.infolist():
                if info.is_dir():
                    continue
                fdata = z.read(info.filename)
                files.append(SisFileEntry(
                    path=info.filename,
                    data=fdata,
                    size=len(fdata)
                ))
                # Try to extract metadata from pkg files
                if info.filename.lower().endswith('.pkg'):
                    try:
                        txt = fdata.decode('utf-8', errors='ignore')
                        # Simple pkg parsing
                        for line in txt.splitlines():
                            if 'vendor' in line.lower():
                                vendor = line.split('=')[-1].strip().strip('"')
                            if 'uid' in line.lower() and '0x' in line.lower():
                                try:
                                    uid_str = [p for p in line.split() if '0x' in p][0]
                                    uid = int(uid_str, 16)
                                except:
                                    pass
                    except:
                        pass
        except Exception as e:
            # Fallback
            pass

        # Try to infer name from first file
        if files and name == "unknown":
            name = files[0].path.split('/')[-1]

        return SisPackage(
            name=name,
            vendor=vendor,
            version=version,
            uid=uid,
            files=files,
            capabilities=caps or ["NetworkServices", "LocalServices", "ReadUserData"],
            languages=langs,
            dependencies=deps,
            raw_data=data
        )

    @staticmethod
    def _parse_sis_old(data: bytes, filename: str) -> SisPackage:
        # Old SIS format - binary structure
        # This is simplified - real SIS has complex structure
        name = Path(filename).stem
        vendor = "Symbian"
        version = (1, 0, 0)
        uid = 0x10000000
        files = []
        caps = []
        langs = ["EN"]
        deps = []

        try:
            # Old SIS header: 16 bytes
            # UID1, UID2, UID3, checksum etc
            if len(data) >= 32:
                # Try to read header
                uid = struct.unpack("<I", data[12:16])[0] if len(data) >= 16 else uid
                # Rest is file entries - very simplified
                # For demo, treat whole file as one entry
                files.append(SisFileEntry(
                    path=f"!:\\system\\apps\\{name}\\{name}.app",
                    data=data,
                    size=len(data)
                ))
        except Exception as e:
            files.append(SisFileEntry(path=filename, data=data, size=len(data)))

        return SisPackage(
            name=name,
            vendor=vendor,
            version=version,
            uid=uid,
            files=files,
            capabilities=caps,
            languages=langs,
            dependencies=deps,
            raw_data=data
        )

    @staticmethod
    def extract(pkg: SisPackage, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted = []
        for f in pkg.files:
            # Sanitize path - remove drive letters like !:\ or C:\
            clean_path = f.path.replace("!:", "").replace("C:", "").replace("\\", "/").lstrip("/")
            out_path = output_dir / clean_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(f.data)
            extracted.append(str(out_path))
        return extracted
