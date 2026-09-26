"""
App runtime for Symbian - handles SIS, JAR, native apps
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import time

class AppType(Enum):
    NATIVE_SYMBIAN = "native_symbian"  # .app, E32Image
    SIS = "sis"
    SISX = "sisx"
    JAVA_MIDLET = "java_midlet"  # JAR
    N_GAGE = "n_gage"
    FLASH_LITE = "flash_lite"
    WIDGET = "widget"  # WRT widget
    PE_EXE = "pe_exe"  # Windows compat
    ELF = "elf"  # Linux compat

class AppState(Enum):
    INSTALLED = "installed"
    RUNNING = "running"
    PAUSED = "paused"
    BACKGROUND = "background"
    CLOSED = "closed"

@dataclass
class SymbianApp:
    uid: int
    name: str
    vendor: str
    version: str
    app_type: AppType
    executable: str
    icon_path: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    state: AppState = AppState.INSTALLED
    install_path: str = ""
    data_size: int = 0
    installed_at: float = field(default_factory=time.time)
    last_run: Optional[float] = None
    run_count: int = 0

    def to_dict(self):
        return {
            "uid": f"0x{self.uid:08X}",
            "name": self.name,
            "vendor": self.vendor,
            "version": self.version,
            "type": self.app_type.value,
            "exe": self.executable,
            "state": self.state.value,
            "path": self.install_path,
            "size": self.data_size,
            "caps": self.capabilities,
            "installed": self.installed_at,
            "runs": self.run_count
        }

class AppRuntime:
    """
    Manages installed apps and their lifecycle
    """
    def __init__(self, filesystem):
        self.fs = filesystem
        self.apps: Dict[int, SymbianApp] = {}
        self.running: Dict[int, SymbianApp] = {}
        self.next_uid = 0x10000001

        # Preinstall some iconic apps
        self._install_default_apps()

    def _install_default_apps(self):
        defaults = [
            SymbianApp(uid=0x10005901, name="Phone", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Phone.app", capabilities=["NetworkServices"]),
            SymbianApp(uid=0x100058F3, name="Contacts", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="CntApp.app", capabilities=["ReadUserData", "WriteUserData"]),
            SymbianApp(uid=0x100058F4, name="Messages", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="MceApp.app", capabilities=["NetworkServices", "ReadUserData"]),
            SymbianApp(uid=0x10005A22, name="Gallery", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Gallery.app", capabilities=["ReadUserData"]),
            SymbianApp(uid=0x10005A32, name="Camera", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="CameraApp.app", capabilities=["MultimediaDD", "WriteUserData"]),
            SymbianApp(uid=0x101F4CD2, name="Web", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Browser.app", capabilities=["NetworkServices"]),
            SymbianApp(uid=0x10005907, name="Calendar", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Calendar.app", capabilities=["ReadUserData", "WriteUserData"]),
            SymbianApp(uid=0x100058EC, name="Clock", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="ClockApp.app", capabilities=[]),
            SymbianApp(uid=0x101F4CCE, name="File Manager", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="FileManager.app", capabilities=["AllFiles"]),
            SymbianApp(uid=0x100058F5, name="Log", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="LogsApp.app", capabilities=["ReadUserData"]),
            SymbianApp(uid=0x10003A5B, name="Snake", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Snake.app", capabilities=[]),
            SymbianApp(uid=0x10003A5A, name="Bounce", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Bounce.app", capabilities=[]),
            SymbianApp(uid=0x10005A3E, name="Music Player", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="MusicPlayer.app", capabilities=["ReadUserData", "MultimediaDD"]),
            SymbianApp(uid=0x101F857A, name="App Manager", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="AppMngr.app", capabilities=["AllFiles", "DiskAdmin"]),
            SymbianApp(uid=0x102072C3, name="Maps", vendor="Nokia", version="1.0", app_type=AppType.NATIVE_SYMBIAN, executable="Maps.app", capabilities=["Location", "NetworkServices"]),
        ]
        for app in defaults:
            self.apps[app.uid] = app

    def install_sis(self, sis_package) -> SymbianApp:
        uid = sis_package.uid if hasattr(sis_package, 'uid') else self.next_uid
        if uid < 0x10000000:
            uid = self.next_uid
            self.next_uid += 1

        app = SymbianApp(
            uid=uid,
            name=sis_package.name,
            vendor=sis_package.vendor,
            version=".".join(map(str, sis_package.version)) if isinstance(sis_package.version, tuple) else str(sis_package.version),
            app_type=AppType.SISX,
            executable=f"{sis_package.name}.app",
            capabilities=sis_package.capabilities,
            install_path=f"C:\\system\\apps\\{sis_package.name}\\",
            data_size=sum(f.size for f in sis_package.files)
        )
        self.apps[uid] = app

        # Write files to FS
        files_dict = {f.path: f.data for f in sis_package.files}
        self.fs.install_app(sis_package.name, files_dict)

        return app

    def install_jar(self, jar_package) -> SymbianApp:
        uid = self.next_uid
        self.next_uid += 1

        app = SymbianApp(
            uid=uid,
            name=jar_package.name,
            vendor=jar_package.vendor,
            version=jar_package.version,
            app_type=AppType.JAVA_MIDLET,
            executable=jar_package.midlet_class or f"{jar_package.name}.class",
            install_path=f"C:\\system\\midlets\\{jar_package.name}\\",
            data_size=len(jar_package.raw_data)
        )
        self.apps[uid] = app

        # Install JAR files
        files_dict = {f.name: f.data for f in jar_package.files}
        self.fs.install_app(jar_package.name, files_dict, drive="C")

        return app

    def install_exe(self, pe_info, name: str) -> SymbianApp:
        uid = self.next_uid
        self.next_uid += 1

        app = SymbianApp(
            uid=uid,
            name=name,
            vendor="Windows Compat",
            version="1.0",
            app_type=AppType.PE_EXE,
            executable=name,
            install_path=f"C:\\system\\apps\\{name}\\",
            data_size=len(pe_info.raw_data),
            capabilities=["AllFiles"]
        )
        self.apps[uid] = app
        self.fs.write_file(f"C:\\system\\apps\\{name}\\{name}.exe", pe_info.raw_data)
        return app

    def install_elf(self, elf_info, name: str) -> SymbianApp:
        uid = self.next_uid
        self.next_uid += 1

        app = SymbianApp(
            uid=uid,
            name=name,
            vendor="Linux Compat",
            version="1.0",
            app_type=AppType.ELF,
            executable=name,
            install_path=f"C:\\system\\apps\\{name}\\",
            data_size=len(elf_info.raw_data),
            capabilities=["AllFiles"]
        )
        self.apps[uid] = app
        self.fs.write_file(f"C:\\system\\apps\\{name}\\{name}.elf", elf_info.raw_data)
        return app

    def launch(self, uid: int) -> bool:
        app = self.apps.get(uid)
        if not app:
            return False
        app.state = AppState.RUNNING
        app.last_run = time.time()
        app.run_count += 1
        self.running[uid] = app
        return True

    def close(self, uid: int) -> bool:
        app = self.apps.get(uid)
        if not app:
            return False
        app.state = AppState.CLOSED
        if uid in self.running:
            del self.running[uid]
        return True

    def uninstall(self, uid: int) -> bool:
        if uid in self.apps:
            # Don't allow uninstalling system apps (UID < 0x10000000 or in default list)
            if uid < 0x101F0000 and uid in [0x10005901, 0x100058F3, 0x100058F4]:
                return False
            del self.apps[uid]
            if uid in self.running:
                del self.running[uid]
            return True
        return False

    def list_apps(self) -> List[Dict]:
        return [app.to_dict() for app in self.apps.values()]

    def list_running(self) -> List[Dict]:
        return [app.to_dict() for app in self.running.values()]

    def get_app(self, uid: int) -> Optional[SymbianApp]:
        return self.apps.get(uid)
