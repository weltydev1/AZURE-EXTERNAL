import ctypes
import math
from config import LMB_VK_CODE, VK_INSERT
def is_key_pressed(vk_code):
    return ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000
def is_lmb_pressed():
    return is_key_pressed(LMB_VK_CODE)
def is_insert_pressed():
    return ctypes.windll.user32.GetAsyncKeyState(VK_INSERT) & 1
def calc_angle(local_pos, target_pos):
    dx = target_pos[0] - local_pos[0]
    dy = target_pos[1] - local_pos[1]
    dz = target_pos[2] - local_pos[2]
    dist_2d = math.sqrt(dx*dx + dy*dy)
    pitch = -math.degrees(math.atan2(dz, dist_2d))
    yaw = math.degrees(math.atan2(dy, dx))
    return (pitch, yaw)
def normalize_angle(angle, is_pitch):
    if is_pitch:
        angle = max(min(angle, 89.0), -89.0)
    else:
        while angle > 180.0:
            angle -= 360.0
        while angle < -180.0:
            angle += 360.0
    return angle
def get_fov_distance(current_angles, target_angles):
    delta_yaw = normalize_angle(current_angles[1] - target_angles[1], False)
    delta_pitch = normalize_angle(current_angles[0] - target_angles[0], True)
    fov_distance = math.sqrt(delta_yaw**2 + delta_pitch**2)
    return fov_distance
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]
def get_game_window_rect(window_title):
    hWnd = ctypes.windll.user32.FindWindowW(None, window_title)
    rect = RECT()
    if hWnd:
        ctypes.windll.user32.GetWindowRect(hWnd, ctypes.pointer(rect))
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    return None
