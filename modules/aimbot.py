import time
from pymem import Pymem
from pymem.process import module_from_name
from pymem.pattern import pattern_scan_module
from config import SETTINGS, PROCESS_NAME, CLIENT_DLL_NAME, ENGINE_DLL_NAME, OFFSET_LOCAL_PLAYER, OFFSET_ENTITY_LIST, OFFSET_STATIC_VIEW_ANGLES, ENTITY_SIZE_BYTES, OFFSET_HEALTH, OFFSET_ORIGIN, OFFSET_VIEW_MATRIX, OFFSET_TEAM, WH_OFFSET, OFFSET_FLASH_ALPHA, OFFSET_FLASH_DURATION, PLAYER_POSITIONS, OFFSET_BHOP_Y_POS, OFFSET_FORCE_JUMP, JUMP_KEY, pm, client_base, engine_base
from core.memory import read_int, read_vec3, read_vec2, write_int, write_float, write_vec2
from core.utils import is_lmb_pressed, calc_angle, normalize_angle, get_fov_distance
import keyboard
import math


def WorldToScreen(viewmatrix, coords, width, height):

    

    x = viewmatrix[0] * coords[0] + viewmatrix[1] * coords[1] + viewmatrix[2] * coords[2] + viewmatrix[3]
    y = viewmatrix[4] * coords[0] + viewmatrix[5] * coords[1] + viewmatrix[6] * coords[2] + viewmatrix[7]
    w = viewmatrix[12] * coords[0] + viewmatrix[13] * coords[1] + viewmatrix[14] * coords[2] + viewmatrix[15]
    
    if w < 0.1:
        return None 
    

    x = x / w
    y = y / w
    

    screen_x = (width / 2 * x) + (x + width / 2)
    screen_y = -(height / 2 * y) + (y + height / 2)
    
    return screen_x, screen_y, w

def bunnyhop_c_style_check():
    if not SETTINGS.get("BUNNYHOP_ACTIVE", False):
        return
        
    if keyboard.is_pressed(JUMP_KEY):
        
        try:
            VisY = pm.read_float(client_base + OFFSET_BHOP_Y_POS)
        except Exception:
            return

        VisYnew = VisY

        write_int(pm, client_base + OFFSET_FORCE_JUMP, 6)
        
        time.sleep(0.05)
        
        while keyboard.is_pressed(JUMP_KEY):
            
            try:
                VisYnew = pm.read_float(client_base + OFFSET_BHOP_Y_POS)
            except Exception:
                break
            
            if VisY != VisYnew:
                write_int(pm, client_base + OFFSET_FORCE_JUMP, 4)
                
                break 


def aimbot_loop():
    global pm, client_base, engine_base
    try:
        pm = Pymem(PROCESS_NAME)
        client_base = module_from_name(pm.process_handle, CLIENT_DLL_NAME).lpBaseOfDll
        engine_base = module_from_name(pm.process_handle, ENGINE_DLL_NAME).lpBaseOfDll
    except Exception:
        return
    addr_local_ptr_static = client_base + OFFSET_LOCAL_PLAYER
    addr_entity_list_base = client_base + OFFSET_ENTITY_LIST
    addr_view_angles_static = engine_base + OFFSET_STATIC_VIEW_ANGLES
    addr_wh_static = client_base + WH_OFFSET
    while True:
        try:
            if SETTINGS["WH_ACTIVE"]:
                write_int(pm, addr_wh_static, 2)
            else:
                write_int(pm, addr_wh_static, 1)
        except Exception:
            pass
        try:
            local_player_ptr = read_int(pm, addr_local_ptr_static)
            if local_player_ptr == 0:
                time.sleep(0.005)
                continue
            
            bunnyhop_c_style_check()
            
            local_health = read_int(pm, local_player_ptr + OFFSET_HEALTH)
            local_team = read_int(pm, local_player_ptr + OFFSET_TEAM)
            local_pos = read_vec3(pm, local_player_ptr + OFFSET_ORIGIN)
            current_view_angles = read_vec2(pm, addr_view_angles_static)
            is_player_team = local_team in [2, 3, 5]
            current_player_data = []
            if SETTINGS["ANTIFLASH_ACTIVE"]:
                write_float(pm, local_player_ptr + OFFSET_FLASH_ALPHA, 0.0)
                write_float(pm, local_player_ptr + OFFSET_FLASH_DURATION, 0.0)
            if local_health > 0 and is_player_team:
                current_hitbox_offset = SETTINGS["HITBOX_OFFSETS"].get(SETTINGS["CURRENT_HITBOX_KEY"], 1.0)
                best_target_ptr = 0
                best_target_value = float('inf') if SETTINGS["CURRENT_AIM_PRIORITY"] == "Distance" else 0
                MAX_ENT = 32
                for i in range(MAX_ENT):
                    ent_ptr_addr = addr_entity_list_base + i * ENTITY_SIZE_BYTES
                    ent_ptr = read_int(pm, ent_ptr_addr)
                    if ent_ptr and ent_ptr != 0 and ent_ptr != local_player_ptr:
                        try:
                            hp = read_int(pm, ent_ptr + OFFSET_HEALTH)
                            team = read_int(pm, ent_ptr + OFFSET_TEAM)
                            pos = read_vec3(pm, ent_ptr + OFFSET_ORIGIN)
                            is_target_team = team in [2, 3, 5]
                            if hp > 0 and is_target_team:
                                relative_pos_x = pos[0] - local_pos[0]
                                relative_pos_y = pos[1] - local_pos[1]
                                current_player_data.append({
                                    'x': relative_pos_x,
                                    'y': relative_pos_y,
                                    'team': team,
                                    'is_enemy': team != local_team
                                })
                                if SETTINGS["AIM_ACTIVE"] and is_lmb_pressed():
                                    target_pos_center = (pos[0], pos[1], pos[2] + current_hitbox_offset)
                                    target_angles = calc_angle(local_pos, target_pos_center)
                                    distance = ((target_pos_center[0] - local_pos[0])**2 + (target_pos_center[1] - local_pos[1])**2 + (target_pos_center[2] - local_pos[2])**2)**0.5
                                    if distance > SETTINGS["MAX_AIM_DISTANCE"]:
                                        continue
                                    fov_dist = get_fov_distance(current_view_angles, target_angles)
                                    if fov_dist < SETTINGS["MAX_FOV_DEGREES"]:
                                        is_new_best = False
                                        if SETTINGS["CURRENT_AIM_PRIORITY"] == "Distance":
                                            if distance < best_target_value:
                                                best_target_value = distance
                                                is_new_best = True
                                        elif SETTINGS["CURRENT_AIM_PRIORITY"] == "Health":
                                            if hp < best_target_value:
                                                best_target_value = hp
                                                is_new_best = True
                                        if is_new_best or (not best_target_ptr):
                                            best_target_ptr = ent_ptr
                                            best_target_angles_raw = target_angles
                        except Exception:
                            pass
                PLAYER_POSITIONS[:] = current_player_data
                if best_target_ptr != 0:
                    target_pitch = normalize_angle(best_target_angles_raw[0], True)
                    target_yaw = normalize_angle(best_target_angles_raw[1], False)
                    current_pitch = current_view_angles[0]
                    current_yaw = current_view_angles[1]
                    delta_pitch = target_pitch - current_pitch
                    delta_yaw = normalize_angle(target_yaw - current_yaw, False)
                    smooth_factor = SETTINGS["AIM_SMOOTH_FACTOR"]
                    if smooth_factor < 1.0:
                        smooth_factor = 1.0
                    new_pitch = current_pitch + (delta_pitch / smooth_factor)
                    new_yaw = current_yaw + (delta_yaw / smooth_factor)
                    final_pitch = normalize_angle(new_pitch, True)
                    final_yaw = normalize_angle(new_yaw, False)
                    if SETTINGS["AIM_ACTIVE"]:
                        write_vec2(pm, addr_view_angles_static, (final_pitch, final_yaw))
                else:
                    pass
        except Exception:
            pass
        time.sleep(0.005)
