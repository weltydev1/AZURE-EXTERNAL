import struct
from pymem import Pymem
def read_vec3(pm, addr):
    try:
        b = pm.read_bytes(addr, 12)
        x, y, z = struct.unpack('fff', b)
        return (x, y, z)
    except Exception:
        return (0.0, 0.0, 0.0)
def read_vec2(pm, addr):
    try:
        b = pm.read_bytes(addr, 8)
        pitch, yaw = struct.unpack('ff', b)
        return (pitch, yaw)
    except Exception:
        return (0.0, 0.0)
def write_vec2(pm, addr, angles):
    try:
        b = struct.pack('ff', angles[0], angles[1])
        pm.write_bytes(addr, b, 8)
    except Exception:
        pass
def read_int(pm, addr):
    try:
        return pm.read_int(addr)
    except Exception:
        return 0
def write_float(pm, addr, value):
    try:
        pm.write_float(addr, value)
    except Exception:
        pass
def write_int(pm, addr, value):
    try:
        pm.write_int(addr, value)
    except Exception:
        pass
