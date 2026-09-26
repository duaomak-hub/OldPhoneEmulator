"""
Native UI fallback - tries Tkinter, then Pygame, then web
"""
import sys
from pathlib import Path

def try_tkinter_ui():
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog
        print("Starting Tkinter UI...")
        # Simple Tkinter UI
        root = tk.Tk()
        root.title("OldPhoneEmulator - Symbian OS")
        root.geometry("400x700")
        root.configure(bg="#1a1a28")

        label = tk.Label(root, text="📱 OldPhoneEmulator\nSymbian OS Emulator\n\nIconic Nokia Keypad\nApp Launcher\nROM Support: .rom .sis .exe .elf .iso",
                         bg="#1a1a28", fg="white", font=("Arial", 12), justify="left")
        label.pack(pady=20)

        # Device selector
        from ..devices.nokia_profiles import DeviceRegistry
        reg = DeviceRegistry()
        devices = [d.name for d in reg.list_all()]

        var = tk.StringVar(value=devices[5] if len(devices)>5 else devices[0])
        opt = tk.OptionMenu(root, var, *devices)
        opt.pack(pady=10)

        def import_rom():
            path = filedialog.askopenfilename(filetypes=[("All ROMs", "*.rom *.bin *.img *.sis *.sisx *.jar *.exe *.elf *.iso *.vhd")])
            if path:
                print(f"Import {path}")

        btn = tk.Button(root, text="Import ROM", command=import_rom)
        btn.pack(pady=10)

        root.mainloop()
        return True
    except Exception as e:
        print(f"Tkinter failed: {e}")
        return False

def try_pygame_ui():
    try:
        import pygame
        print("Starting Pygame UI...")
        pygame.init()
        screen = pygame.display.set_mode((360, 640))
        pygame.display.set_caption("OldPhoneEmulator - Nokia N95")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 20)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    print(f"Key {event.key}")

            screen.fill((168, 198, 134))  # Nokia screen color
            text = font.render("NOKIA N95 Emulator", True, (0,0,0))
            screen.blit(text, (80, 300))
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        return True
    except Exception as e:
        print(f"Pygame failed: {e}")
        return False

def start_native():
    if try_tkinter_ui():
        return
    if try_pygame_ui():
        return
    print("No native UI available, falling back to web UI...")
    from .web_server import EmulatorWebServer
    server = EmulatorWebServer()
    server.run()
