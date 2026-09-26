"""
Web-based UI for OldPhoneEmulator
Provides iconic Nokia keypad, screen emulation, app launcher, ROM import
Runs on 0.0.0.0 for preview support
"""
import os
import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from ..core.rom_loader import RomLoader
from ..core.memory import Memory
from ..core.cpu_arm import ARMv5CPU
from ..core.kernel import SymbianKernel
from ..core.filesystem import SymbianFileSystem
from ..core.disk import DiskImage
from ..devices.nokia_profiles import DeviceRegistry
from ..symbian.os_versions import list_versions
from ..symbian.app_runtime import AppRuntime
from ..symbian.e32 import E32Api
from ..config import ROMS_DIR, BASE_DIR

class EmulatorState:
    def __init__(self):
        self.registry = DeviceRegistry()
        self.current_device = self.registry.get("nokia_n95")
        self.memory = Memory(ram_size=64*1024*1024)
        self.cpu = ARMv5CPU(self.memory)
        self.kernel = SymbianKernel(self.memory)
        self.fs = SymbianFileSystem(BASE_DIR / "fs")
        self.app_runtime = AppRuntime(self.fs)
        self.e32 = E32Api(self.kernel, self.fs, self.memory)

        self.roms = []
        self.disks = []
        self.screen_buffer = None
        self.running = False
        self.logs = []

        self.load_roms_dir()

    def load_roms_dir(self):
        try:
            self.roms = RomLoader.load_directory(ROMS_DIR)
        except Exception as e:
            self.log(f"Failed to load ROMs: {e}")

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.logs.append(entry)
        if len(self.logs) > 200:
            self.logs = self.logs[-200:]
        print(entry)

    def switch_device(self, device_id: str) -> bool:
        dev = self.registry.get(device_id)
        if dev:
            self.current_device = dev
            # Resize memory based on device
            self.memory = Memory(ram_size=dev.hardware.ram_mb * 1024 * 1024)
            self.cpu = ARMv5CPU(self.memory)
            self.kernel = SymbianKernel(self.memory)
            self.e32 = E32Api(self.kernel, self.fs, self.memory)
            self.log(f"Switched to {dev.name}")
            return True
        return False

    def import_rom(self, file_path: Path):
        try:
            rom = RomLoader.load(file_path)
            self.roms.append(rom)
            self.log(f"Imported ROM: {rom.path.name} ({rom.rom_type.value}) {rom.size} bytes")

            # Auto-handle based on type
            if rom.rom_type.value in ["sis", "sisx"]:
                if rom.parsed:
                    app = self.app_runtime.install_sis(rom.parsed)
                    self.log(f"Installed app: {app.name} (UID {app.uid:08X})")
            elif rom.rom_type.value == "jar":
                if rom.parsed:
                    app = self.app_runtime.install_jar(rom.parsed)
                    self.log(f"Installed MIDlet: {app.name}")
            elif rom.rom_type.value == "pe_exe":
                if rom.parsed:
                    app = self.app_runtime.install_exe(rom.parsed, file_path.stem)
                    self.log(f"Imported Windows EXE: {app.name} - compat layer")
            elif rom.rom_type.value == "elf":
                if rom.parsed:
                    app = self.app_runtime.install_elf(rom.parsed, file_path.stem)
                    self.log(f"Imported Linux ELF: {app.name} - compat layer")
            elif rom.rom_type.value in ["iso", "vhd", "qcow", "img"]:
                disk = DiskImage.parse(rom.raw_data, file_path)
                self.disks.append(disk)
                self.log(f"Loaded disk: {disk.label} ({disk.fs_type})")

            # Load ROM into memory if it's a Symbian ROM
            if "symbian" in rom.rom_type.value or "nokia" in rom.rom_type.value or "rom" in rom.rom_type.value:
                self.memory.load_rom(rom.raw_data, rom.load_address, rom.rom_type.value)
                self.cpu.reset(rom.entry_point)
                self.log(f"Loaded ROM to memory at 0x{rom.load_address:08X}, entry 0x{rom.entry_point:08X}")

            return rom
        except Exception as e:
            self.log(f"Failed to import {file_path}: {e}")
            raise

    def get_state(self):
        return {
            "device": self.current_device.to_dict() if self.current_device else None,
            "cpu": self.cpu.get_state_dict(),
            "kernel": self.kernel.get_stats(),
            "roms": [r.to_dict() for r in self.roms],
            "disks": [d.to_dict() for d in self.disks],
            "apps": self.app_runtime.list_apps(),
            "running_apps": self.app_runtime.list_running(),
            "drives": self.fs.get_drive_info(),
            "logs": self.logs[-50:],
            "running": self.running
        }

# Global state
emulator_state = EmulatorState()

def create_app():
    app = Flask(__name__,
                template_folder=str(Path(__file__).parent / "web" / "templates"),
                static_folder=str(Path(__file__).parent / "web" / "static"))

    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
    app.config['UPLOAD_FOLDER'] = str(ROMS_DIR)

    @app.route("/")
    def index():
        return render_template("index.html",
                               devices=emulator_state.registry.to_dict_list(),
                               current_device=emulator_state.current_device.to_dict() if emulator_state.current_device else None,
                               symbian_versions=[v.to_dict() for v in list_versions()])

    @app.route("/api/state")
    def api_state():
        return jsonify(emulator_state.get_state())

    @app.route("/api/devices")
    def api_devices():
        return jsonify(emulator_state.registry.to_dict_list())

    @app.route("/api/device/<device_id>", methods=["POST"])
    def api_switch_device(device_id):
        ok = emulator_state.switch_device(device_id)
        return jsonify({"success": ok, "device": emulator_state.current_device.to_dict() if ok else None})

    @app.route("/api/roms")
    def api_roms():
        return jsonify([r.to_dict() for r in emulator_state.roms])

    @app.route("/api/roms/upload", methods=["POST"])
    def api_upload_rom():
        if 'file' not in request.files:
            return jsonify({"error": "No file"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No filename"}), 400

        filename = secure_filename(file.filename)
        save_path = ROMS_DIR / filename
        file.save(str(save_path))

        try:
            rom = emulator_state.import_rom(save_path)
            return jsonify({"success": True, "rom": rom.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/rom/<path:rom_name>/info")
    def api_rom_info(rom_name):
        for r in emulator_state.roms:
            if r.path.name == rom_name:
                return jsonify(r.to_dict())
        return jsonify({"error": "Not found"}), 404

    @app.route("/api/apps")
    def api_apps():
        return jsonify(emulator_state.app_runtime.list_apps())

    @app.route("/api/apps/<int:uid>/launch", methods=["POST"])
    def api_launch_app(uid):
        ok = emulator_state.app_runtime.launch(uid)
        emulator_state.log(f"{'Launched' if ok else 'Failed to launch'} app UID 0x{uid:08X}")
        return jsonify({"success": ok})

    @app.route("/api/apps/<int:uid>/close", methods=["POST"])
    def api_close_app(uid):
        ok = emulator_state.app_runtime.close(uid)
        return jsonify({"success": ok})

    @app.route("/api/apps/<int:uid>/uninstall", methods=["POST"])
    def api_uninstall_app(uid):
        ok = emulator_state.app_runtime.uninstall(uid)
        return jsonify({"success": ok})

    @app.route("/api/cpu/step", methods=["POST"])
    def api_cpu_step():
        steps = int(request.json.get("steps", 1)) if request.is_json else 1
        for _ in range(steps):
            emulator_state.cpu.step()
        return jsonify(emulator_state.cpu.get_state_dict())

    @app.route("/api/cpu/run", methods=["POST"])
    def api_cpu_run():
        cycles = int(request.json.get("cycles", 1000)) if request.is_json else 1000
        emulator_state.cpu.run(cycles)
        return jsonify(emulator_state.cpu.get_state_dict())

    @app.route("/api/cpu/reset", methods=["POST"])
    def api_cpu_reset():
        entry = request.json.get("entry_point") if request.is_json else None
        if entry:
            try:
                ep = int(entry, 0)
                emulator_state.cpu.reset(ep)
            except:
                emulator_state.cpu.reset()
        else:
            emulator_state.cpu.reset()
        return jsonify(emulator_state.cpu.get_state_dict())

    @app.route("/api/keypress", methods=["POST"])
    def api_keypress():
        data = request.json or {}
        key = data.get("key", "")
        action = data.get("action", "press")  # press, release, long

        emulator_state.log(f"Key {action}: {key}")

        # Map to emulator actions
        # For now just log and simulate
        # In real emulator, this would inject into window server

        # Special handling
        if key == "power":
            emulator_state.running = not emulator_state.running
        elif key.startswith("num_"):
            pass  # Number keys

        return jsonify({"success": True, "key": key, "action": action})

    @app.route("/api/fs/list")
    def api_fs_list():
        path = request.args.get("path", "C:\\")
        files = emulator_state.fs.list_dir(path)
        return jsonify([f.to_dict() for f in files])

    @app.route("/api/fs/drives")
    def api_fs_drives():
        return jsonify(emulator_state.fs.get_drive_info())

    @app.route("/api/disks")
    def api_disks():
        return jsonify([d.to_dict() for d in emulator_state.disks])

    @app.route("/api/logs")
    def api_logs():
        return jsonify(emulator_state.logs[-100:])

    @app.route("/api/screen")
    def api_screen():
        # Return simulated screen buffer
        # For now generate a Nokia-like screen
        dev = emulator_state.current_device
        if not dev:
            return jsonify({"error": "No device"}), 400

        # Generate a simple screen representation
        # In real emulator, this would be framebuffer from VRAM
        return jsonify({
            "width": dev.screen.width,
            "height": dev.screen.height,
            "running": emulator_state.running,
            "apps": emulator_state.app_runtime.list_running()
        })

    return app

class EmulatorWebServer:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.app = create_app()

    def run(self, debug=False):
        print(f"""
╔════════════════════════════════════════════════╗
║   OldPhoneEmulator - Symbian OS Emulator       ║
║   Device: {emulator_state.current_device.name if emulator_state.current_device else 'None':<30} ║
║   ROMs: {len(emulator_state.roms):<3}  Apps: {len(emulator_state.app_runtime.apps):<3}                    ║
║   Listening on http://{self.host}:{self.port}           ║
╚════════════════════════════════════════════════╝
        """)
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)
