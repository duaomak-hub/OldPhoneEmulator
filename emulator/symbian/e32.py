"""
E32 - Symbian OS API shim
Provides Python implementation of common Symbian C++ APIs
"""
from typing import Dict, List, Callable
import time

class E32Api:
    """
    Shim for Symbian E32 APIs
    Used by emulator to handle app syscalls
    """
    def __init__(self, kernel, filesystem, memory):
        self.kernel = kernel
        self.fs = filesystem
        self.memory = memory
        self.start_time = time.time()

        # E32 function table
        self.functions: Dict[int, Callable] = {
            0x00: self.hal_function,
            0x01: self.tick_count,
            0x02: self.debug_print,
            0x03: self.user_heap,
            0x04: self.create_thread,
        }

    def hal_function(self, func_num: int, arg1: int = 0, arg2: int = 0) -> int:
        """
        HAL (Hardware Abstraction Layer) function
        """
        # HAL attributes - simplified
        hal_map = {
            0: 0x40000000,  # Memory size
            1: 104,  # CPU speed MHz
            2: 176,  # Display width
            3: 208,  # Display height
            4: 16,  # Display BPP
            5: 1,  # Has keyboard
            6: 0,  # Has pointer
        }
        return hal_map.get(func_num, 0)

    def tick_count(self) -> int:
        # Symbian tick = 1/64 sec?
        elapsed = time.time() - self.start_time
        return int(elapsed * 64)

    def debug_print(self, ptr: int) -> int:
        try:
            s = self.memory.read_cstring(ptr, 256)
            print(f"[E32 DEBUG] {s}")
            return 0
        except Exception as e:
            print(f"[E32 DEBUG] Failed to read string at 0x{ptr:X}: {e}")
            return -1

    def user_heap(self) -> int:
        # Return heap size
        return 4 * 1024 * 1024

    def create_thread(self, name_ptr: int, entry: int, stack_size: int) -> int:
        try:
            name = self.memory.read_cstring(name_ptr, 64)
        except:
            name = f"Thread_{entry:X}"
        # Create thread in kernel
        if self.kernel.current_process:
            thread = self.kernel.create_thread(name, self.kernel.current_process.pid, entry, stack_size)
            return thread.tid
        return -1

    def handle_swi(self, swi_num: int, r0: int, r1: int, r2: int, r3: int) -> int:
        """
        Handle SWI from CPU
        """
        func = self.functions.get(swi_num & 0xFF)
        if func:
            try:
                return func(r0, r1, r2, r3)
            except TypeError:
                try:
                    return func(r0)
                except:
                    return func()
        # Default
        return 0

    def get_system_info(self) -> Dict:
        return {
            "tick": self.tick_count(),
            "uptime": time.time() - self.start_time,
            "hal": {
                "memory": self.hal_function(0),
                "cpu_mhz": self.hal_function(1),
                "display": f"{self.hal_function(2)}x{self.hal_function(3)}"
            }
        }
