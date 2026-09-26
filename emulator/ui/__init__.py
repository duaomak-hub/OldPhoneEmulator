"""
UI package - supports web and native
"""
try:
    from .web_server import EmulatorWebServer
except ImportError:
    EmulatorWebServer = None

__all__ = ["EmulatorWebServer"]
