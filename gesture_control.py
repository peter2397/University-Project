import cv2
import mediapipe as mp
import math
import subprocess
import time
import json
import os
import broadlink

# ========== 參數 ==========
ADB_PATH = "adb"  # 需改成 adb 所在完整路徑或確實設環境變數
GESTURE_MAP_FILE = 'gesture_config.json'
reload_interval = 3
GESTURE_CONFIRMATION_FRAMES = 5
current_mode = None

# Broadlink設備參數
DEVICE_IP = '192.168.31.133'
DEVICE_MAC = bytearray.fromhex('e87072abbfbc')
DEVICE_TYPE = 0x6507

# Broadlink IR codes，請完整替換為正確byte碼
fan_codes = {
    "fan_power": b'&\x00\x18\x01th\x1aE\x18G\x18 \x1aE\x1aE\x18G\x18 \x1a \x18 \x1a \x18 \x1aE\x18 \x1a \x18G\x18 \x1a \x18 \x19F\x18G\x18F\x19E\x1aE\x1a \x18 \x19\x00\x05qth\x1aE\x1aE\x19!\x18E\x1aE\x1aE\x19\x1f\x1a \x18 \x1a \x18 \x1aE\x19 \x19 \x19F\x19\x1f\x1a \x18 \x19F\x19F\x19F\x18F\x19E\x1a \x18 \x19\x00\x05pui\x18G\x18E\x1a \x18G\x18F\x19E\x1a \x18 \x1a \x18 \x19!\x18F\x19 \x19 \x19E\x19 \x19 \x19 \x19F\x19E\x19F\x19F\x18F\x19 \x19 \x19\x00\x05puh\x19F\x18G\x18 \x1aE\x19F\x18G\x18 \x1a \x18 \x19 \x19 \x19F\x18 \x1a \x18F\x19 \x19 \x19 \x19F\x18F\x19E\x1aE\x19F\x19 \x19 \x19\x00\x05ptj\x19E\x19F\x19 \x19E\x1aE\x1aE\x19\x1f\x1a \x18 \x1a \x18 \x1aE\x19 \x19 \x19F\x19 \x19 \x19\x1f\x1aE\x19F\x19F\x18G\x18E\x1a \x18 \x1a\x00\r\x05',  # 電風扇開關
    "fan_add": b'&\x008\x00ui\x18F\x19E\x1a \x18G\x18G\x18F\x19E\x1aE\x1aE\x1aE\x18G\x18 \x1a \x18 \x1aE\x1a \x18 \x19 \x19 \x19 \x19 \x19 \x19 \x19F\x19 \x18\x00\r\x05', #電風扇風量加
    "fan_reduce": b'&\x008\x00ti\x19F\x19F\x19 \x19E\x19F\x19F\x19E\x19F\x19F\x19 \x19E\x19 \x19 \x19 \x19F\x19 \x19 \x19 \x19 \x18 \x1a \x18G\x18 \x1aE\x19\x1f\x1a\x00\r\x05', #電風扇風量減
    "ac_26":b'&\x00\x96\x00d=\r\x11\r\x11\r+\x0e,\x0c\x11\r\x11\r\x11\r\x11\x0e,\x0c\x11\r,\r+\r,\x0e+\r,\r+\r\x11\r\x11\r+\x0e,\r+\r,\r+\r,\x0e+\r\x11\r,\r+\r,\r,\r,\x0c,\r\x11\r\x11\x0e\x11\x0c,\r,\x0c,\r,\r,\r\x11\r\x11\r\x11\x0c,\r,\r\x11\r,\r\x11\r\x11\x0c\x12\r,\r+\r,\r+\r,\x0e+\r\x11\r\x11\r,\x0c\x11\r\x11\x0e\x11\r\x11\r\x11\r+\r\x11\r\x12\r\x11\r+\r,\r\x11\x0c\x12\r\x00\r\x05',  #冷氣26度
    "ac_25":b'&\x00\x96\x00d<\x0e\x10\x0e\x11\r+\r,\r\x11\x0c\x11\x0e\x11\r\x11\r,\x0c\x12\x0c,\r+\x0e,\r+\r,\r+\r\x11\x0e\x11\r,\x0c,\r,\x0c,\x0e,\x0c,\r,\x0c\x11\r,\x0e*\x0e,\r+\r,\r+\x0e\x10\x0e\x11\r\x11\r+\r,\r+\x0e,\r+\r\x11\r\x11\r\x11\x0e+\r,\r\x11\r\x11\x0c,\x0e\x10\x0e\x11\r+\r,\r+\r,\x0e+\r,\r\x11\x0c\x12\x0c,\x0e\x11\r\x11\x0c\x12\x0c\x11\r\x11\r,\x0e\x11\x0c\x11\r\x11\r,\r+\x0e+\x0e+\r\x00\r\x05',  #冷氣25度
    "ac_27":b'&\x00\x96\x00e<\r\x11\r\x11\r,\r+\x0e\x11\r\x11\r\x11\x0c\x11\r,\x0e\x11\x0c,\r,\r+\r,\x0c,\x0e,\x0c\x11\r\x11\r,\r+\x0e,\r+\r,\r+\r,\r\x11\r,\r,\x0c,\r,\x0c,\x0e+\r\x11\r\x11\r\x11\r,\x0c,\x0e+\r,\r+\r\x11\r\x11\x0e\x11\r+\r,\r\x11\r+\r,\x0e\x11\x0c\x11\r,\r+\r,\x0e+\r,\r+\r\x11\r\x11\r,\r\x11\r\x11\r\x11\r\x11\r\x11\r+\x0e\x11\r\x11\r\x11\r+\r,\r\x11\r,\r\x00\r\x05',   #冷氣27度
    "ac_24":b'&\x00\x96\x00d=\r\x11\r\x11\x0c,\r,\r\x11\r\x11\r\x11\r\x11\r+\x0e\x10\x0e,\r+\r,\r+\r,\r,\r\x11\r\x11\r+\r,\x0e+\r,\r+\r,\x0c,\x0e\x11\r+\r,\r+\r,\x0e+\r,\r\x11\x0c\x11\r\x11\r,\x0e+\r,\r+\r,\r\x11\r\x11\r\x11\r,\x0c,\r\x11\x0e\x11\r\x11\x0c\x11\r\x11\r,\x0e*\x0e,\r+\r,\x0c,\r\x11\x0e\x11\r+\r\x11\r\x11\r\x11\x0e\x11\x0c\x11\r,\r\x11\r\x11\x0c\x12\r,\r+\r,\r\x11\r\x00\r\x05',  #冷氣24度
    "ac_23":b'&\x00\x96\x00d<\r\x11\r\x12\x0c,\r,\x0c\x11\r\x11\r\x11\x0e\x11\r+\r\x11\r,\r+\r,\x0e+\r,\r+\r\x11\r\x11\x0e+\r,\r+\r,\r+\x0e,\r+\r\x11\r,\r+\x0e+\r,\r,\r+\r\x11\r\x11\x0e\x11\r+\r,\r+\r,\r,\r\x11\r\x11\r\x11\r+\x0e\x11\r,\x0c,\r,\x0c\x11\r\x11\x0e,\r+\r,\r+\r,\x0e+\r\x11\r\x11\r+\r\x11\r\x11\x0e\x11\r\x11\r\x11\x0c,\r\x11\r\x11\x0e\x11\x0c\x12\x0c\x11\r\x11\r,\x0e\x00\r\x05',  #冷氣23度
    "ac_power":b'&\x00\x96\x00d<\x0e\x11\x0c\x11\r,\r+\r\x11\x0e\x10\x0e\x11\r\x11\r+\r,\r+\x0e,\x0c,\r,\x0c,\r,\r\x10\x0e\x11\r,\r+\r,\x0c,\x0e,\x0c,\r+\r\x11\r,\x0e+\r,\r+\r,\r+\x0e\x10\x0e\x11\r\x11\r+\r,\x0c,\x0e,\x0c,\r\x11\r\x11\r\x11\r,\r,\x0c\x11\r\x11\r,\x0c\x12\r\x11\r,\r+\r,\r+\x0e,\r+\r\x11\r\x11\r+\r\x11\x0e\x11\r\x11\r\x11\r\x11\x0c,\r\x11\x0e\x11\x0c\x12\x0c,\r\x11\r+\r,\x0e\x00\r\x05'  #冷氣開關
}

device = broadlink.gendevice(DEVICE_TYPE, (DEVICE_IP, 80), DEVICE_MAC)
device.auth()

# 需要雙發送的電風扇風量命令
fan_double_send_cmds = {"fan_add", "fan_reduce"}

# 儲存冷氣目前溫度，全程追蹤
current_ac_temp = None

def load_gesture_commands_and_mode():
    if os.path.exists(GESTURE_MAP_FILE):
        with open(GESTURE_MAP_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            current_mode = config.get("current_mode", "tv")
            gesture_commands = config.get(current_mode, {})
            ac_init_temp = config.get("ac_init_temp", 25)  # 冷氣初始溫度預設25
            return gesture_commands, current_mode, ac_init_temp
    return {}, "tv", 25

def map_command(cmd_key):
    mapping = {
        "power": f"{ADB_PATH} shell input keyevent 26",
        "home": f"{ADB_PATH} shell input keyevent 3",
        "channel_up": f"{ADB_PATH} shell input keyevent 166",
        "channel_down": f"{ADB_PATH} shell input keyevent 167",
        "volume_up": f"{ADB_PATH} shell input keyevent 24",
        "volume_down": f"{ADB_PATH} shell input keyevent 25",
        "choose": f"{ADB_PATH} shell input keyevent 66",
        "return": f"{ADB_PATH} shell input keyevent 4",
        "youtube": f"{ADB_PATH} shell am start -n com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity"
    }
    return mapping.get(cmd_key.lower(), None)



def execute_adb_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"指令執行成功: {command}")
        else:
            print(f"指令執行失敗: {command}\n錯誤訊息: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("指令執行逾時，請檢查ADB連線狀態。")

def send_broadlink_command(cmd_key, current_mode):
    # 依模式替換 power 指令
    if cmd_key == "power":
        if current_mode == "ac":
            real_key = "ac_power"
        elif current_mode == "fan":
            real_key = "fan_power"
        else:
            real_key = cmd_key
    else:
        real_key = cmd_key

    code = fan_codes.get(real_key)
    if not code:
        print(f"Broadlink IR code 不存在: {real_key}")
        return False
    try:
        device.send_data(code)
        print(f"Broadlink 發送: {real_key}")
        return True
    except Exception as e:
        print(f"Broadlink 發送失敗: {real_key} 錯誤: {e}")
        return False


def send_fan_command_twice(cmd_key):
    # 電風扇風量加減指令需連發兩次，間隔1秒
    send_broadlink_command(cmd_key)
    time.sleep(1)
    send_broadlink_command(cmd_key)

def send_ac_temperature_command(temp, current_mode):
    code_key = f"ac_{temp}"
    if code_key not in fan_codes:
        print(f"無對應冷氣溫度 IR code: {temp}")
        return False
    return send_broadlink_command(code_key, current_mode)



# ========== 手勢辨識核心邏輯 ==========
def calculate_angle(a, b, c):
    ab = [a.x - b.x, a.y - b.y]
    cb = [c.x - b.x, c.y - b.y]
    dot = ab[0] * cb[0] + ab[1] * cb[1]
    norm_ab = math.hypot(ab[0], ab[1])
    norm_cb = math.hypot(cb[0], cb[1])
    if norm_ab * norm_cb == 0: return 0
    cos_angle = dot / (norm_ab * norm_cb)
    angle = math.acos(max(min(cos_angle, 1), -1))
    return math.degrees(angle)

def is_finger_straight(lm, mcp, pip, tip, threshold=160):
    return calculate_angle(lm[mcp], lm[pip], lm[tip]) > threshold

def is_finger_bent(lm, mcp, pip, tip, threshold=140):
    return calculate_angle(lm[mcp], lm[pip], lm[tip]) < threshold

def get_finger_direction(lm, mcp, tip, palm_width):
    dx = (lm[tip].x - lm[mcp].x) / palm_width
    dy = (lm[tip].y - lm[mcp].y) / palm_width
    angle = math.degrees(math.atan2(-dy, dx))
    if -45 <= angle <= 45:
        return 'RIGHT'
    elif 45 < angle <= 135:
        return 'UP'
    elif angle > 135 or angle < -135:
        return 'LEFT'
    elif -135 < angle < -45:
        return 'DOWN'
    return None

def check_palm(lm):
    return (is_finger_straight(lm, 2, 3, 4, 140) and is_finger_straight(lm, 5, 6, 8) and
            is_finger_straight(lm, 9, 10, 12) and is_finger_straight(lm, 13, 14, 16) and
            is_finger_straight(lm, 17, 18, 20))

def check_fist(lm):
    return (is_finger_bent(lm, 2, 3, 4, 160) and is_finger_bent(lm, 5, 6, 8) and
            is_finger_bent(lm, 9, 10, 12) and is_finger_bent(lm, 13, 14, 16) and
            is_finger_bent(lm, 17, 18, 20))

def check_ok(lm):
    distance = math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y)
    other_fingers_straight = (
        is_finger_straight(lm, 9, 10, 12) and
        is_finger_straight(lm, 13, 14, 16) and
        is_finger_straight(lm, 17, 18, 20))
    return distance < 0.056 and other_fingers_straight

def check_peace(lm):
    if (is_finger_straight(lm, 5, 6, 8) and is_finger_straight(lm, 9, 10, 12) and
        is_finger_bent(lm, 2, 3, 4, 160) and is_finger_bent(lm, 13, 14, 16) and
        is_finger_bent(lm, 17, 18, 20)):
        distance = math.hypot(lm[8].x - lm[12].x, lm[8].y - lm[12].y)
        return distance > 0.08
    return False

def check_thumb_pointing(lm, palm_width):
    if (is_finger_straight(lm, 2, 3, 4, 140) and is_finger_bent(lm, 5, 6, 8) and
        is_finger_bent(lm, 9, 10, 12) and is_finger_bent(lm, 13, 14, 16) and
        is_finger_bent(lm, 17, 18, 20)):
        direction = get_finger_direction(lm, 2, 4, palm_width)
        if direction:
            if direction in ['UP', 'DOWN']:
                return f'THUMB_{direction}'
            elif lm[4].x > lm[5].x:
                return 'THUMB_RIGHT'
            else:
                return 'THUMB_LEFT'
    return None

def check_index_pointing(lm, palm_width):
    if (is_finger_straight(lm, 5, 6, 8) and is_finger_bent(lm, 2, 3, 4, 160) and
        is_finger_bent(lm, 9, 10, 12) and is_finger_bent(lm, 13, 14, 16) and
        is_finger_bent(lm, 17, 18, 20)):
        return get_finger_direction(lm, 5, 8, palm_width)
    return None

def recognize_gesture(hand_landmarks, handedness):
    if handedness.classification[0].label != 'Right': return None
    lm = hand_landmarks.landmark
    palm_width = math.hypot(lm[5].x - lm[17].x, lm[5].y - lm[17].y) + 1e-6
    if check_palm(lm): return "PALM"
    if check_fist(lm): return "FIST"
    if check_ok(lm): return "OK"
    if check_peace(lm): return "PEACE"
    thumb_gesture = check_thumb_pointing(lm, palm_width)
    if thumb_gesture: return thumb_gesture
    index_gesture = check_index_pointing(lm, palm_width)
    if index_gesture: return index_gesture
    return None

def main():
    global current_ac_temp
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("無法開啟攝像頭。")
        return

    prev_gesture = None
    gesture_counter = 0
    prev_time = 0
    last_reload = time.time()
    gesture_commands, current_mode, ac_init_temp = load_gesture_commands_and_mode()
    current_ac_temp = ac_init_temp  # 初始冷氣溫度

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("無法讀取畫面，程式結束。")
                break

            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            curr_time = time.time()
            time_diff = curr_time - prev_time
            if time_diff > 0:
                fps = 1 / time_diff
                prev_time = curr_time
                cv2.putText(image, f'FPS: {int(fps)}', (image.shape[1]-150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

            results = hands.process(rgb_image)
            current_gesture = None
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    gesture = recognize_gesture(hand_landmarks, handedness)  # 你的 recognize_gesture 函式
                    if gesture:
                        current_gesture = gesture
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            now = time.time()
            if now - last_reload > reload_interval:
                gesture_commands, current_mode, ac_init_temp = load_gesture_commands_and_mode()
                last_reload = now
                # 若使用者網站改了初始冷氣溫度，就更新
                if current_ac_temp is None:
                    current_ac_temp = ac_init_temp
                print(f"<< 目前模式: {current_mode}，指令表: {gesture_commands}，冷氣初始溫度: {ac_init_temp}")

            if current_gesture is not None and current_gesture == prev_gesture:
                gesture_counter +=1
            else:
                gesture_counter = 0

            if gesture_counter == GESTURE_CONFIRMATION_FRAMES:
                print(f"辨識到穩定手勢：[{current_gesture}]，已觸發指令！")
                cmd_to_send = gesture_commands.get(current_gesture)

                if current_mode == "fan":
                    if cmd_to_send in {"fan_add", "fan_reduce"}:
                        send_fan_command_twice(cmd_to_send, current_mode)
                    elif cmd_to_send:
                        send_broadlink_command(cmd_to_send, current_mode)

                elif current_mode == "ac":
                    # 冷氣溫度加減邏輯
                    if current_gesture == "UP":
                        if current_ac_temp < 27:
                            current_ac_temp += 1
                            send_ac_temperature_command(current_ac_temp, current_mode)
                    elif current_gesture == "DOWN":
                        if current_ac_temp > 23:
                            current_ac_temp -=1
                            send_ac_temperature_command(current_ac_temp, current_mode)
                    elif cmd_to_send:
                        send_broadlink_command(cmd_to_send, current_mode)

                else:
                    # 其他模式使用ADB指令
                    if cmd_to_send:
                        execute_adb_command(cmd_to_send)

            prev_gesture = current_gesture

            if current_gesture:
                cv2.putText(image, f'Gesture: {current_gesture}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.putText(image, f'Mode: {current_mode}', (12, image.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (90,80,180), 2)

            cv2.imshow('Hand Gesture Control', image)
            if cv2.waitKey(5) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
