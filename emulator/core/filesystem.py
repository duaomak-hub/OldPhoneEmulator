"""
Symbian File System emulation (E32 File Server)
Emulates drives C:, D:, E:, Z: etc
"""
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import time

@dataclass
class SymbianFile:
    name: str
    path: str
    size: int
    is_dir: bool
    modified: float
    attribs: int = 0

    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "is_dir": self.is_dir,
            "modified": self.modified,
            "attribs": self.attribs
        }

class SymbianFileSystem:
    """
    Symbian File Server emulation
    Drives:
    - Z: ROM (read-only)
    - C: Internal flash (user data)
    - D: RAM drive
    - E: Memory card
    - etc
    """
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create drive mappings
        self.drives: Dict[str, Path] = {
            "Z": self.base_path / "z_drive",  # ROM
            "C": self.base_path / "c_drive",  # Internal
            "D": self.base_path / "d_drive",  # RAM
            "E": self.base_path / "e_drive",  # MMC
        }

        for drive_path in self.drives.values():
            drive_path.mkdir(parents=True, exist_ok=True)
            # Create standard Symbian dirs
            (drive_path / "system" / "apps").mkdir(parents=True, exist_ok=True)
            (drive_path / "system" / "libs").mkdir(parents=True, exist_ok=True)
            (drive_path / "system" / "data").mkdir(parents=True, exist_ok=True)
            (drive_path / "resource").mkdir(parents=True, exist_ok=True)
            (drive_path / "private").mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, symbian_path: str) -> Optional[Path]:
        """
        Convert Symbian path like C:\\system\\apps\\App.app to host path
        """
        if not symbian_path:
            return None

        # Normalize
        path = symbian_path.strip()
        # Handle drive letter
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].upper()
            rest = path[2:].lstrip('\\/').replace('\\', '/')
            if drive in self.drives:
                return self.drives[drive] / rest
            else:
                # Unknown drive, map to C:
                return self.drives["C"] / rest
        # No drive - assume C:
        clean = path.lstrip('\\/').replace('\\', '/')
        return self.drives["C"] / clean

    def exists(self, symbian_path: str) -> bool:
        p = self._resolve_path(symbian_path)
        return p.exists() if p else False

    def is_dir(self, symbian_path: str) -> bool:
        p = self._resolve_path(symbian_path)
        return p.is_dir() if p else False

    def list_dir(self, symbian_path: str) -> List[SymbianFile]:
        p = self._resolve_path(symbian_path)
        if not p or not p.exists() or not p.is_dir():
            return []

        result = []
        try:
            for child in p.iterdir():
                try:
                    stat = child.stat()
                    result.append(SymbianFile(
                        name=child.name,
                        path=f"{symbian_path.rstrip(chr(92))}\\{child.name}" if symbian_path else child.name,
                        size=stat.st_size if child.is_file() else 0,
                        is_dir=child.is_dir(),
                        modified=stat.st_mtime
                    ))
                except:
                    continue
        except:
            pass
        return result

    def read_file(self, symbian_path: str) -> Optional[bytes]:
        p = self._resolve_path(symbian_path)
        if not p or not p.exists() or not p.is_file():
            return None
        try:
            return p.read_bytes()
        except:
            return None

    def write_file(self, symbian_path: str, data: bytes) -> bool:
        p = self._resolve_path(symbian_path)
        if not p:
            return False
        # Don't allow writing to Z: (ROM)
        if symbian_path.upper().startswith("Z:"):
            return False
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return True
        except Exception as e:
            print(f"[FS] Write failed {symbian_path}: {e}")
            return False

    def create_dir(self, symbian_path: str) -> bool:
        p = self._resolve_path(symbian_path)
        if not p:
            return False
        if symbian_path.upper().startswith("Z:"):
            return False
        try:
            p.mkdir(parents=True, exist_ok=True)
            return True
        except:
            return False

    def delete(self, symbian_path: str) -> bool:
        p = self._resolve_path(symbian_path)
        if not p or not p.exists():
            return False
        if symbian_path.upper().startswith("Z:"):
            return False
        try:
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            return True
        except:
            return False

    def get_drive_info(self) -> Dict[str, Dict]:
        info = {}
        for drive_letter, path in self.drives.items():
            try:
                total = 0
                used = 0
                for f in path.rglob("*"):
                    if f.is_file():
                        try:
                            used += f.stat().st_size
                        except:
                            pass
                # Simulate drive sizes
                sizes = {"Z": 64*1024*1024, "C": 128*1024*1024, "D": 32*1024*1024, "E": 1024*1024*1024}
                total = sizes.get(drive_letter, 128*1024*1024)
                info[drive_letter] = {
                    "path": str(path),
                    "total": total,
                    "used": used,
                    "free": total - used,
                    "type": "ROM" if drive_letter == "Z" else "Internal" if drive_letter == "C" else "RAM" if drive_letter == "D" else "MMC"
                }
            except Exception as e:
                info[drive_letter] = {"error": str(e)}
        return info

    def install_app(self, app_name: str, files: Dict[str, bytes], drive: str = "C") -> bool:
        """
        Install app files to symbian filesystem
        files: dict of symbian_path -> data
        """
        base = self.drives.get(drive, self.drives["C"])
        app_dir = base / "system" / "apps" / app_name
        app_dir.mkdir(parents=True, exist_ok=True)

        for sym_path, data in files.items():
            # sym_path is already relative or full
            if sym_path.startswith(("C:", "Z:", "E:")):
                target = self._resolve_path(sym_path)
            else:
                target = app_dir / sym_path.replace("\\", "/").lstrip("/")
            if target:
                try:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                except Exception as e:
                    print(f"[FS] Failed to install {sym_path}: {e}")
                    return False
        return True
