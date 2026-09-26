#!/usr/bin/env python3
"""
OldPhoneEmulator - Main Entry Point
A cross-platform Symbian OS / Nokia OS emulator supporting any ROM,
Windows EXE, Linux ELF, and disk images with iconic keypad and app launcher.

Usage:
    python main.py [--web] [--port 5000] [--device nokia_n95] [--rom path/to/rom]

Supports:
    - Symbian ROMs: .rom, .bin, .img, .rofs, .uda, .core, .md0
    - Nokia flash: .fpsx, .vpl, .dcp, .mcusw, .ppm
    - Packages: .sis, .sisx, .jar, .jad
    - Executables: .exe (PE), .elf (Linux)
    - Disk images: .iso, .vhd, .qcow, .vmdk, .img
"""
import argparse
import sys
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).parent))

from emulator.config import ROMS_DIR, BASE_DIR
from emulator.core.rom_loader import RomLoader
from emulator.devices.nokia_profiles import DeviceRegistry
from emulator.ui.web_server import EmulatorWebServer, emulator_state

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██╗     ██████╗ ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗ ║
║  ██╔═══██╗██║     ██╔══██╗██╔══██╗██║  ██║██╔═══██╗████╗  ██║ ║
║  ██║   ██║██║     ██║  ██║██████╔╝███████║██║   ██║██╔██╗ ██║ ║
║  ██║   ██║██║     ██║  ██║██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║ ║
║  ╚██████╔╝███████╗██████╔╝██║     ██║  ██║╚██████╔╝██║ ╚████║ ║
║   ╚═════╝ ╚══════╝╚═════╝ ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                              ║
║  ███████╗███╗   ███╗██╗   ██╗██╗      █████╗ ████████╗ ██████╗ ██████╗  ║
║  ██╔════╝████╗ ████║██║   ██║██║     ██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗ ║
║  █████╗  ██╔████╔██║██║   ██║██║     ███████║   ██║   ██║   ██║██████╔╝ ║
║  ██╔══╝  ██║╚██╔╝██║██║   ██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗ ║
║  ███████╗██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║ ║
║  ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝ ║
║                                                              ║
║  Symbian OS Emulator • Nokia Iconic Phones • Cross-Platform  ║
║  Supports: ROM, SIS, JAR, EXE, ELF, ISO, VHD, QCOW           ║
║  Devices: 3310, 6600, N70, N95, 5800, N8, 808 PureView & more ║
╚══════════════════════════════════════════════════════════════╝
    """)

def list_devices():
    reg = DeviceRegistry()
    print("\n📱 Available Nokia Devices:\n")
    for dev in reg.list_all():
        iconic = "⭐ ICONIC" if dev.iconic else ""
        print(f"  {dev.id:18} {dev.name:25} {dev.family.value:12} {dev.year} {dev.screen.resolution:10} {iconic}")
        print(f"    └─ {dev.description}")
    print()

def list_roms():
    print(f"\n💾 ROMs in {ROMS_DIR}:\n")
    roms = RomLoader.load_directory(ROMS_DIR)
    if not roms:
        print("  No ROMs found. Import with --rom or via web UI.")
        print(f"  Supported: {', '.join(RomLoader.get_supported_extensions())}")
    else:
        for rom in roms:
            print(f"  {rom.path.name:30} {rom.rom_type.value:15} {rom.size/1024/1024:.2f} MB  MD5:{rom.md5[:8]}")
    print()

def main():
    parser = argparse.ArgumentParser(description="OldPhoneEmulator - Symbian OS Emulator")
    parser.add_argument("--web", action="store_true", help="Start web UI (default)")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default 0.0.0.0)")
    parser.add_argument("--device", type=str, default="nokia_n95", help="Device ID (default nokia_n95)")
    parser.add_argument("--rom", type=str, help="Path to ROM file to load")
    parser.add_argument("--list-devices", action="store_true", help="List available devices")
    parser.add_argument("--list-roms", action="store_true", help="List ROMs in roms/")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no web)")

    args = parser.parse_args()

    print_banner()

    if args.list_devices:
        list_devices()
        return

    if args.list_roms:
        list_roms()
        return

    # Device selection
    if args.device:
        if not emulator_state.switch_device(args.device):
            print(f"⚠️  Unknown device '{args.device}', using default")
            emulator_state.switch_device("nokia_n95")
        else:
            print(f"📱 Device: {emulator_state.current_device.name}")

    # ROM loading
    if args.rom:
        rom_path = Path(args.rom)
        if rom_path.exists():
            try:
                rom = emulator_state.import_rom(rom_path)
                print(f"💾 Loaded ROM: {rom.path.name} ({rom.rom_type.value})")
            except Exception as e:
                print(f"❌ Failed to load ROM: {e}")
                sys.exit(1)
        else:
            print(f"❌ ROM not found: {rom_path}")
            sys.exit(1)

    # Load existing ROMs
    emulator_state.load_roms_dir()
    print(f"💾 Found {len(emulator_state.roms)} ROM(s) in {ROMS_DIR}")
    print(f"📦 {len(emulator_state.app_runtime.apps)} apps installed")

    if args.cli:
        # CLI mode
        print("\n🖥️  CLI Mode - Commands: help, devices, roms, apps, cpu, key <key>, quit\n")
        while True:
            try:
                cmd = input("emulator> ").strip().split()
                if not cmd:
                    continue
                if cmd[0] in ["quit", "exit", "q"]:
                    break
                elif cmd[0] == "help":
                    print("Commands: devices, roms, apps, cpu, key <key>, reset, step, power, quit")
                elif cmd[0] == "devices":
                    list_devices()
                elif cmd[0] == "roms":
                    list_roms()
                elif cmd[0] == "apps":
                    for app in emulator_state.app_runtime.list_apps():
                        print(f"  {app['uid']} {app['name']} ({app['type']}) - {app['state']}")
                elif cmd[0] == "cpu":
                    print(emulator_state.cpu.get_state_dict())
                elif cmd[0] == "key" and len(cmd) > 1:
                    key = cmd[1]
                    emulator_state.log(f"Key press: {key}")
                    print(f"Pressed {key}")
                elif cmd[0] == "reset":
                    emulator_state.cpu.reset()
                    print("CPU reset")
                elif cmd[0] == "step":
                    emulator_state.cpu.step()
                    print(f"PC: 0x{emulator_state.cpu.state.pc:08X}")
                elif cmd[0] == "power":
                    emulator_state.running = not emulator_state.running
                    print(f"Power {'ON' if emulator_state.running else 'OFF'}")
                else:
                    print(f"Unknown command: {cmd[0]}")
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    else:
        # Web mode (default)
        print(f"\n🌐 Starting Web UI on http://{args.host}:{args.port}")
        print(f"   - Iconic Nokia keypad")
        print(f"   - App launcher with import")
        print(f"   - ROM manager (supports any ROM type)")
        print(f"   - Disk image support (ISO, VHD, QCOW, etc)")
        print(f"   - Windows EXE & Linux ELF compatibility")
        print(f"\n   Press Ctrl+C to stop\n")

        server = EmulatorWebServer(host=args.host, port=args.port)
        try:
            server.run(debug=False)
        except KeyboardInterrupt:
            print("\n👋 Shutting down emulator...")

if __name__ == "__main__":
    main()
