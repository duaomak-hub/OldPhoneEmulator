"""
Symbian OS versions and capabilities
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class PlatformSecurity(Enum):
    NONE = "none"  # Pre-9.x
    CAPABILITIES = "capabilities"  # 9.x+
    PLATSEC = "platsec"

@dataclass
class SymbianVersion:
    id: str
    name: str
    version: str
    year: int
    kernel: str
    ui: str
    security: PlatformSecurity
    api_level: int
    features: List[str]
    devices: List[str]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "year": self.year,
            "kernel": self.kernel,
            "ui": self.ui,
            "security": self.security.value,
            "api": self.api_level,
            "features": self.features,
            "devices": self.devices
        }

VERSIONS = [
    SymbianVersion(
        id="s60v1",
        name="S60 1st Edition",
        version="6.1",
        year=2002,
        kernel="EKA1",
        ui="S60 1st",
        security=PlatformSecurity.NONE,
        api_level=6,
        features=["C++", "Java MIDP 1.0", "Bluetooth", "MMC"],
        devices=["7650", "3650", "3660", "N-Gage"]
    ),
    SymbianVersion(
        id="s60v2",
        name="S60 2nd Edition",
        version="7.0s",
        year=2003,
        kernel="EKA1",
        ui="S60 2nd",
        security=PlatformSecurity.NONE,
        api_level=7,
        features=["C++", "Java MIDP 2.0", "Bluetooth", "Camera", "RealOne Player"],
        devices=["6600", "7610", "6670", "6260"]
    ),
    SymbianVersion(
        id="s60v2_fp3",
        name="S60 2nd Edition FP3",
        version="8.1a",
        year=2005,
        kernel="EKA2",
        ui="S60 2nd FP3",
        security=PlatformSecurity.NONE,
        api_level=8,
        features=["EKA2 kernel", "Real-time", "3G", "2MP Camera"],
        devices=["N70", "N90", "N72"]
    ),
    SymbianVersion(
        id="s60v3",
        name="S60 3rd Edition",
        version="9.1",
        year=2005,
        kernel="EKA2",
        ui="S60 3rd",
        security=PlatformSecurity.CAPABILITIES,
        api_level=9,
        features=["Platform Security", "Signed apps", "3G", "WiFi", "Open C"],
        devices=["N73", "N80", "N91", "E60", "E70"]
    ),
    SymbianVersion(
        id="s60v3_fp1",
        name="S60 3rd Edition FP1",
        version="9.2",
        year=2007,
        kernel="EKA2",
        ui="S60 3rd FP1",
        security=PlatformSecurity.CAPABILITIES,
        api_level=9,
        features=["Dual slide", "GPS", "5MP", "N95", "HSDPA"],
        devices=["N95", "N95 8GB", "N82", "E90", "6110 Navigator"]
    ),
    SymbianVersion(
        id="s60v3_fp2",
        name="S60 3rd Edition FP2",
        version="9.3",
        year=2008,
        kernel="EKA2",
        ui="S60 3rd FP2",
        security=PlatformSecurity.CAPABILITIES,
        api_level=9,
        features=["FP2", "Better browser", "FP2 SDK"],
        devices=["N96", "N78", "6220 Classic"]
    ),
    SymbianVersion(
        id="s60v5",
        name="S60 5th Edition",
        version="9.4",
        year=2008,
        kernel="EKA2",
        ui="S60 5th",
        security=PlatformSecurity.CAPABILITIES,
        api_level=9,
        features=["Touch", "Resistive", "Kinetic scrolling", "5800"],
        devices=["5800 XpressMusic", "N97", "N97 mini", "5530", "5230"]
    ),
    SymbianVersion(
        id="symbian3",
        name="Symbian^3",
        version="9.5",
        year=2010,
        kernel="EKA2",
        ui="Symbian^3",
        security=PlatformSecurity.PLATSEC,
        api_level=10,
        features=["HDMI", "Multi-touch", "Qt", "Homescreen widgets", "12MP"],
        devices=["N8", "C7", "C6-01", "E7"]
    ),
    SymbianVersion(
        id="anna",
        name="Symbian Anna",
        version="9.5 Anna",
        year=2011,
        kernel="EKA2",
        ui="Anna",
        security=PlatformSecurity.PLATSEC,
        api_level=10,
        features=["Portrait QWERTY", "New browser", "Maps", "Anna icons"],
        devices=["X7", "E6"]
    ),
    SymbianVersion(
        id="belle",
        name="Symbian Belle",
        version="9.5 Belle",
        year=2011,
        kernel="EKA2",
        ui="Belle",
        security=PlatformSecurity.PLATSEC,
        api_level=10,
        features=["6 homescreens", "NFC", "New UI", "Belle"],
        devices=["701", "700", "603", "808 PureView"]
    ),
]

_registry = {v.id: v for v in VERSIONS}

def get_version(version_id: str) -> SymbianVersion:
    return _registry.get(version_id)

def list_versions() -> List[SymbianVersion]:
    return VERSIONS

def get_by_symbian_string(s: str) -> SymbianVersion:
    s_lower = s.lower()
    for v in VERSIONS:
        if v.version in s_lower or v.name.lower() in s_lower:
            return v
    return VERSIONS[4]  # Default to S60v3 FP1 (N95 era)
