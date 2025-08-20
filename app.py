from flask import Flask, request, jsonify, render_template
import json, os
import subprocess
from pyngrok import ngrok
import atexit

# 設定你的 Ngrok Authtoken
ngrok.set_auth_token("2qI8XKVIU0OJuNiE59vtNfR0lUR_3cWTRbXyax6GGkULTNA89")

PYTHON_PATH = r"C:\Users\hu030\PycharmProjects\FlaskProject\.venv\Scripts\python.exe"
SCRIPT_PATH = r"C:\Users\hu030\PycharmProjects\FlaskProject\gesture_control.py"

app = Flask(__name__)
CONFIG_PATH = "gesture_config.json"
process = None  # 用來管理手勢辨識子程序

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_gesture_config', methods=['GET'])
def get_gesture_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/save_gesture_config', methods=['POST'])
def save_gesture_config():
    data = request.get_json()
    configs = data.get('configs')
    current_mode = data.get('current_mode')

    if not isinstance(configs, dict):
        return jsonify({"status": "error", "msg": "configs 必須是 dict"}), 400

    configs["current_mode"] = current_mode

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success"})

@app.route('/start_gesture_project', methods=['POST'])
def start_gesture_project():
    global process
    if process and process.poll() is None:
        return jsonify({"status": "already running"})

    if not os.path.isfile(PYTHON_PATH):
        return jsonify({"status": "error", "message": "找不到 python 執行檔路徑"})
    if not os.path.isfile(SCRIPT_PATH):
        return jsonify({"status": "error", "message": "找不到手勢辨識程式路徑"})

    # 用指定虛擬環境 Python 路徑啟動
    process = subprocess.Popen([PYTHON_PATH, SCRIPT_PATH])
    return jsonify({"status": "started"})

@app.route('/stop_gesture_project', methods=['POST'])
def stop_gesture_project():
    global process
    if process and process.poll() is None:
        process.terminate()
        process = None
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not running"})

if __name__ == '__main__':
    import atexit

    tunnel = ngrok.connect(5000, bind_tls=True)
    print("ngrok 埠轉發網址：", tunnel.public_url)

    @atexit.register
    def cleanup():
        print("關閉 ngrok 隧道...")
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()

    app.run(host='0.0.0.0', port=5000)

