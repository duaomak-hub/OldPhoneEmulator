"""
JAR / JAD parser for Java ME (J2ME) MIDlets - common on Nokia phones
"""
import zipfile
import io
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path

@dataclass
class JarEntry:
    name: str
    size: int
    data: bytes

@dataclass
class JarPackage:
    name: str
    vendor: str
    version: str
    midlet_name: str
    midlet_class: str
    files: List[JarEntry]
    manifest: Dict[str, str]
    raw_data: bytes

    def to_dict(self):
        return {
            "name": self.name,
            "midlet": self.midlet_name,
            "class": self.midlet_class,
            "vendor": self.vendor,
            "version": self.version,
            "files": len(self.files),
            "manifest": self.manifest
        }

class JarParser:
    @staticmethod
    def is_jar(data: bytes) -> bool:
        if data[:2] != b'PK':
            return False
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            names = [n.lower() for n in z.namelist()]
            return any('meta-inf' in n for n in names) or any(n.endswith('.class') for n in names)
        except:
            return False

    @staticmethod
    def parse(data: bytes, filename: str = "unknown.jar") -> JarPackage:
        files = []
        manifest = {}
        name = Path(filename).stem
        vendor = "Unknown"
        version = "1.0"
        midlet_name = name
        midlet_class = ""

        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            for info in z.infolist():
                if info.is_dir():
                    continue
                fdata = z.read(info.filename)
                files.append(JarEntry(info.filename, len(fdata), fdata))

                if info.filename.upper() == "META-INF/MANIFEST.MF":
                    try:
                        txt = fdata.decode('utf-8', errors='ignore')
                        for line in txt.splitlines():
                            if ':' in line:
                                k, v = line.split(':', 1)
                                k = k.strip()
                                v = v.strip()
                                manifest[k] = v
                                lk = k.lower()
                                if 'midlet-name' in lk:
                                    midlet_name = v
                                    name = v
                                elif 'midlet-vendor' in lk:
                                    vendor = v
                                elif 'midlet-version' in lk:
                                    version = v
                                elif lk.startswith('midlet-1'):
                                    # MIDlet-1: Name, Icon, Class
                                    parts = v.split(',')
                                    if len(parts) >= 3:
                                        midlet_name = parts[0].strip()
                                        midlet_class = parts[2].strip()
                    except:
                        pass
        except Exception as e:
            # Fallback
            pass

        return JarPackage(
            name=name,
            vendor=vendor,
            version=version,
            midlet_name=midlet_name,
            midlet_class=midlet_class,
            files=files,
            manifest=manifest,
            raw_data=data
        )
