"""
Symbian OS Kernel emulation
Emulates E32 kernel, processes, threads, scheduler
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import time
import uuid

class ProcessState(Enum):
    CREATED = "created"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class ThreadState(Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    TERMINATED = "terminated"

@dataclass
class Thread:
    tid: int
    name: str
    process_id: int
    state: ThreadState = ThreadState.CREATED
    priority: int = 0
    stack_base: int = 0
    stack_size: int = 0x10000
    entry_point: int = 0
    registers: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "tid": self.tid,
            "name": self.name,
            "process": self.process_id,
            "state": self.state.value,
            "priority": self.priority,
            "entry": f"0x{self.entry_point:X}"
        }

@dataclass
class Process:
    pid: int
    name: str
    uid: int
    state: ProcessState = ProcessState.CREATED
    threads: List[Thread] = field(default_factory=list)
    heap_base: int = 0
    heap_size: int = 0
    code_base: int = 0
    code_size: int = 0
    data_base: int = 0
    capabilities: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "pid": self.pid,
            "name": self.name,
            "uid": f"0x{self.uid:08X}",
            "state": self.state.value,
            "threads": len(self.threads),
            "capabilities": self.capabilities
        }

class SymbianKernel:
    """
    Symbian E32 Kernel emulator
    Handles process/thread creation, scheduling, IPC, etc.
    """
    def __init__(self, memory):
        self.memory = memory
        self.processes: Dict[int, Process] = {}
        self.threads: Dict[int, Thread] = {}
        self.next_pid = 1
        self.next_tid = 1
        self.current_process: Optional[Process] = None
        self.current_thread: Optional[Thread] = None
        self.uptime_start = time.time()
        self.handles: Dict[int, object] = {}
        self.next_handle = 0x100

        # Create kernel process
        self._create_kernel_process()

    def _create_kernel_process(self):
        kernel = Process(
            pid=0,
            name="E32Kernel",
            uid=0x10000000,
            state=ProcessState.RUNNING,
            capabilities=["AllFiles", "Tcb", "ProtServ"]
        )
        self.processes[0] = kernel
        self.current_process = kernel

    def create_process(self, name: str, uid: int, code_base: int, code_size: int, capabilities: List[str] = None) -> Process:
        pid = self.next_pid
        self.next_pid += 1

        proc = Process(
            pid=pid,
            name=name,
            uid=uid,
            state=ProcessState.CREATED,
            code_base=code_base,
            code_size=code_size,
            heap_base=0x30000000 + pid * 0x1000000,
            heap_size=4*1024*1024,
            capabilities=capabilities or ["NetworkServices", "LocalServices"]
        )
        self.processes[pid] = proc

        # Create main thread
        thread = self.create_thread(f"{name}::Main", pid, code_base)
        proc.threads.append(thread)

        proc.state = ProcessState.RUNNING
        return proc

    def create_thread(self, name: str, pid: int, entry_point: int, stack_size: int = 0x10000) -> Thread:
        tid = self.next_tid
        self.next_tid += 1

        thread = Thread(
            tid=tid,
            name=name,
            process_id=pid,
            state=ThreadState.READY,
            entry_point=entry_point,
            stack_size=stack_size,
            stack_base=0x30000000 + pid*0x1000000 + 0x100000 - stack_size
        )
        self.threads[tid] = thread
        return thread

    def terminate_process(self, pid: int):
        if pid in self.processes:
            proc = self.processes[pid]
            proc.state = ProcessState.TERMINATED
            for t in proc.threads:
                t.state = ThreadState.TERMINATED

    def get_process(self, pid: int) -> Optional[Process]:
        return self.processes.get(pid)

    def list_processes(self) -> List[Dict]:
        return [p.to_dict() for p in self.processes.values()]

    def list_threads(self) -> List[Dict]:
        return [t.to_dict() for t in self.threads.values()]

    def get_uptime(self) -> float:
        return time.time() - self.uptime_start

    def handle_svc(self, svc_num: int, r0: int, r1: int, r2: int, r3: int) -> int:
        """
        Handle Supervisor Call (Symbian exec)
        """
        # Simplified SVC handling
        if svc_num == 0:  # Current process
            return self.current_process.pid if self.current_process else 0
        elif svc_num == 1:  # Current thread
            return self.current_thread.tid if self.current_thread else 0
        elif svc_num == 2:  # Create process
            return self.next_pid
        elif svc_num == 3:  # Uptime
            return int(self.get_uptime() * 1000)
        return 0

    def get_stats(self) -> Dict:
        return {
            "uptime": self.get_uptime(),
            "processes": len(self.processes),
            "threads": len(self.threads),
            "next_pid": self.next_pid,
            "next_tid": self.next_tid,
            "handles": len(self.handles)
        }
