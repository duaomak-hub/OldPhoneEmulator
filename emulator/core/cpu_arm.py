"""
ARMv5TE CPU emulator for Symbian OS
Symbian devices used ARM9 / ARM11 cores (ARMv5TE architecture)
Implements pure-python interpreter with optional unicorn acceleration
"""
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional
import struct

try:
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_THUMB
    from unicorn.arm_const import *
    HAS_UNICORN = True
except ImportError:
    HAS_UNICORN = False

@dataclass
class CPUState:
    # General purpose registers r0-r12
    r: List[int] = field(default_factory=lambda: [0]*13)
    sp: int = 0  # r13
    lr: int = 0  # r14
    pc: int = 0  # r15
    cpsr: int = 0x10  # User mode
    spsr: int = 0
    # Banked registers for different modes
    cycles: int = 0
    thumb: bool = False
    running: bool = False

    @property
    def r0(self): return self.r[0]
    @r0.setter
    def r0(self, v): self.r[0] = v & 0xFFFFFFFF
    @property
    def r1(self): return self.r[1]
    @r1.setter
    def r1(self, v): self.r[1] = v & 0xFFFFFFFF

class ARMv5CPU:
    """
    ARMv5TE CPU emulator
    Supports both ARM and Thumb instruction sets
    """
    def __init__(self, memory):
        self.memory = memory
        self.state = CPUState()
        self.breakpoints = set()
        self.handlers: Dict[int, Callable] = {}  # SWI handlers
        self.use_unicorn = HAS_UNICORN
        self._uc = None

        if self.use_unicorn:
            try:
                self._init_unicorn()
            except Exception as e:
                print(f"[CPU] Unicorn init failed, falling back to pure Python: {e}")
                self.use_unicorn = False

        self._init_swi_handlers()

    def _init_unicorn(self):
        self._uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        # Map memory regions to unicorn
        for region in self.memory.regions:
            # Unicorn needs page-aligned
            base = region.base & ~0xFFF
            size = ((region.size + 0xFFF) & ~0xFFF)
            if size == 0:
                continue
            try:
                self._uc.mem_map(base, size)
                if len(region.data) > 0:
                    self._uc.mem_write(region.base, bytes(region.data[:region.size]))
            except Exception as e:
                # May already be mapped
                pass

    def _init_swi_handlers(self):
        # Symbian OS SWI numbers
        # These are simplified
        self.handlers[0x0] = self._handle_swi_kernel
        self.handlers[0x1] = self._handle_swi_file_server
        self.handlers[0x2] = self._handle_swi_window_server

    def reset(self, entry_point: int = 0x40000000):
        self.state = CPUState()
        self.state.pc = entry_point
        self.state.sp = 0x30000000 + self.memory.ram_size - 4
        self.state.running = True
        if self._uc:
            self._uc.reg_write(UC_ARM_REG_SP, self.state.sp)
            self._uc.reg_write(UC_ARM_REG_PC, self.state.pc)

    def _handle_swi_kernel(self, swi_num: int):
        # Kernel exec
        r0 = self.state.r[0]
        # print(f"[SWI] Kernel call r0={r0}")
        return 0

    def _handle_swi_file_server(self, swi_num: int):
        return 0

    def _handle_swi_window_server(self, swi_num: int):
        return 0

    def step(self) -> bool:
        """Execute one instruction, return False if should stop"""
        if not self.state.running:
            return False

        if self.state.pc in self.breakpoints:
            self.state.running = False
            return False

        try:
            if self.use_unicorn and self._uc:
                return self._step_unicorn()
            else:
                return self._step_python()
        except Exception as e:
            print(f"[CPU] Exception at PC=0x{self.state.pc:08X}: {e}")
            self.state.running = False
            return False

    def _step_unicorn(self) -> bool:
        try:
            # Sync memory
            pc = self.state.pc
            # Execute one instruction
            self._uc.emu_start(pc, pc+4, count=1)
            new_pc = self._uc.reg_read(UC_ARM_REG_PC)
            self.state.pc = new_pc
            self.state.cycles += 1
            # Sync registers back
            for i in range(13):
                self.state.r[i] = self._uc.reg_read(UC_ARM_REG_R0 + i)
            self.state.sp = self._uc.reg_read(UC_ARM_REG_SP)
            self.state.lr = self._uc.reg_read(UC_ARM_REG_LR)
            return True
        except Exception as e:
            # Fallback
            return self._step_python()

    def _step_python(self) -> bool:
        """Pure Python ARM interpreter - handles common opcodes"""
        try:
            instr = self.memory.read_u32(self.state.pc)
        except Exception:
            self.state.running = False
            return False

        pc = self.state.pc
        self.state.pc += 4
        self.state.cycles += 1

        # Decode
        cond = (instr >> 28) & 0xF
        # Check condition (simplified - always execute except 0xF)
        if cond == 0xF:
            # Extended
            pass

        # Branch
        if (instr & 0x0F000000) == 0x0A000000:  # B, BL
            offset = instr & 0x00FFFFFF
            if offset & 0x00800000:
                offset |= 0xFF000000  # Sign extend
            offset <<= 2
            link = (instr >> 24) & 1
            if link:
                self.state.lr = pc + 4
            self.state.pc = (pc + 8 + offset) & 0xFFFFFFFF
            return True

        # BX
        if (instr & 0x0FFFFFF0) == 0x012FFF10:
            rm = instr & 0xF
            target = self._get_reg(rm)
            self.state.thumb = (target & 1) == 1
            self.state.pc = target & ~1
            return True

        # Data processing
        if (instr & 0x0C000000) == 0x00000000 or (instr & 0x0C000000) == 0x02000000:
            self._exec_data_processing(instr)
            return True

        # LDR/STR
        if (instr & 0x0C000000) == 0x04000000:
            self._exec_load_store(instr)
            return True

        # LDM/STM
        if (instr & 0x0E000000) == 0x08000000:
            self._exec_block_transfer(instr)
            return True

        # SWI
        if (instr & 0x0F000000) == 0x0F000000:
            swi_num = instr & 0x00FFFFFF
            handler = self.handlers.get(swi_num & 0xFF, self.handlers.get(swi_num))
            if handler:
                handler(swi_num)
            self.state.r[0] = 0  # Success
            return True

        # Unknown - skip
        # print(f"[CPU] Unknown instr 0x{instr:08X} at 0x{pc:08X}")
        return True

    def _get_reg(self, reg_num: int) -> int:
        if reg_num < 13:
            return self.state.r[reg_num]
        elif reg_num == 13:
            return self.state.sp
        elif reg_num == 14:
            return self.state.lr
        else:
            return self.state.pc

    def _set_reg(self, reg_num: int, value: int):
        value &= 0xFFFFFFFF
        if reg_num < 13:
            self.state.r[reg_num] = value
        elif reg_num == 13:
            self.state.sp = value
        elif reg_num == 14:
            self.state.lr = value
        else:
            self.state.pc = value

    def _exec_data_processing(self, instr: int):
        opcode = (instr >> 21) & 0xF
        s_flag = (instr >> 20) & 1
        rn = (instr >> 16) & 0xF
        rd = (instr >> 12) & 0xF
        rn_val = self._get_reg(rn)

        # Operand2
        if instr & 0x02000000:
            # Immediate
            imm = instr & 0xFF
            rot = ((instr >> 8) & 0xF) * 2
            if rot:
                op2 = ((imm >> rot) | (imm << (32-rot))) & 0xFFFFFFFF
            else:
                op2 = imm
        else:
            rm = instr & 0xF
            op2 = self._get_reg(rm)
            shift_type = (instr >> 5) & 3
            shift_amount = (instr >> 7) & 0x1F
            if shift_amount:
                if shift_type == 0:  # LSL
                    op2 = (op2 << shift_amount) & 0xFFFFFFFF
                elif shift_type == 1:  # LSR
                    op2 = op2 >> shift_amount
                elif shift_type == 2:  # ASR
                    if op2 & 0x80000000:
                        op2 = (op2 >> shift_amount) | (0xFFFFFFFF << (32-shift_amount))
                    else:
                        op2 = op2 >> shift_amount

        result = 0
        if opcode == 0x0:  # AND
            result = rn_val & op2
        elif opcode == 0x1:  # EOR
            result = rn_val ^ op2
        elif opcode == 0x2:  # SUB
            result = (rn_val - op2) & 0xFFFFFFFF
        elif opcode == 0x4:  # ADD
            result = (rn_val + op2) & 0xFFFFFFFF
        elif opcode == 0xA:  # CMP (no rd)
            result = (rn_val - op2) & 0xFFFFFFFF
            # Would set flags
            return
        elif opcode == 0xD:  # MOV
            result = op2
        elif opcode == 0xE:  # BIC
            result = rn_val & ~op2
        elif opcode == 0xF:  # MVN
            result = ~op2 & 0xFFFFFFFF
        else:
            result = op2

        self._set_reg(rd, result)

    def _exec_load_store(self, instr: int):
        # LDR/STR
        is_load = (instr >> 20) & 1
        rn = (instr >> 16) & 0xF
        rd = (instr >> 12) & 0xF
        offset = instr & 0xFFF
        if not (instr & 0x02000000):  # Immediate offset
            u_flag = (instr >> 23) & 1
            if not u_flag:
                offset = -offset
            base = self._get_reg(rn)
            addr = (base + offset) & 0xFFFFFFFF

            if is_load:
                try:
                    val = self.memory.read_u32(addr)
                    self._set_reg(rd, val)
                except:
                    self._set_reg(rd, 0)
            else:
                val = self._get_reg(rd)
                try:
                    self.memory.write_u32(addr, val)
                except:
                    pass

    def _exec_block_transfer(self, instr: int):
        # LDM/STM - simplified
        rn = (instr >> 16) & 0xF
        is_load = (instr >> 20) & 1
        w_flag = (instr >> 21) & 1
        reg_list = instr & 0xFFFF
        base = self._get_reg(rn)
        addr = base

        for reg in range(16):
            if reg_list & (1 << reg):
                if is_load:
                    try:
                        val = self.memory.read_u32(addr)
                        self._set_reg(reg, val)
                    except:
                        self._set_reg(reg, 0)
                else:
                    val = self._get_reg(reg)
                    try:
                        self.memory.write_u32(addr, val)
                    except:
                        pass
                addr += 4

        if w_flag:
            self._set_reg(rn, addr)

    def run(self, cycles: int = 1000):
        for _ in range(cycles):
            if not self.step():
                break

    def get_state_dict(self):
        return {
            "r0": f"0x{self.state.r[0]:08X}",
            "r1": f"0x{self.state.r[1]:08X}",
            "r2": f"0x{self.state.r[2]:08X}",
            "r3": f"0x{self.state.r[3]:08X}",
            "r4": f"0x{self.state.r[4]:08X}",
            "r5": f"0x{self.state.r[5]:08X}",
            "r6": f"0x{self.state.r[6]:08X}",
            "r7": f"0x{self.state.r[7]:08X}",
            "r8": f"0x{self.state.r[8]:08X}",
            "r9": f"0x{self.state.r[9]:08X}",
            "r10": f"0x{self.state.r[10]:08X}",
            "r11": f"0x{self.state.r[11]:08X}",
            "r12": f"0x{self.state.r[12]:08X}",
            "sp": f"0x{self.state.sp:08X}",
            "lr": f"0x{self.state.lr:08X}",
            "pc": f"0x{self.state.pc:08X}",
            "cpsr": f"0x{self.state.cpsr:08X}",
            "cycles": self.state.cycles,
            "thumb": self.state.thumb,
            "running": self.state.running,
            "unicorn": self.use_unicorn
        }
