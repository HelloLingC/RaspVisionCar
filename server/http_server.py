# HTTP Flask server for RaspVisionCar console
# should be running on Raspberry Pi

from flask import Flask, Response, request, send_file
import time
import threading
import io
import sys
import os
import serial_pi.serial_io as serial_io

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入电机控制器
try:
    from serial_pi.motor import Motor_Controller
    motor_controller = Motor_Controller()
    print("电机控制器初始化成功")
except ImportError as e:
    print(f"无法导入电机控制器: {e}")
    motor_controller = None

app = Flask(__name__)

ASSETS_DIR = "assets"

# Global variable for streaming output
output = None

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

@app.route('/')
def auth():
    try:
        return send_file(f"{ASSETS_DIR}/auth.html")
    except FileNotFoundError:
        return "HTML file not found", 404

@app.route('/dashboard')
def dashboard():
    try:
        return send_file(f"{ASSETS_DIR}/index.html")
    except FileNotFoundError:
        return "HTML file not found", 404

@app.route('/main.js')
def main_js():
    try:
        return send_file(f"{ASSETS_DIR}/main.js", mimetype='application/javascript')
    except FileNotFoundError:
        return "JavaScript file not found", 404

@app.route('/control')
def control():
    command = request.args.get('command', '')

    print(f"HTTP Command: {command}")
    if command == 'start':
        serial_io.send_command('start:,')
    elif command == 'stop':
        serial_io.send_command('stop:,')
    elif command == 'beep':
        serial_io.send_command('beep:,')

    response = Response('OK')
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response

@app.route('/pid')
def pid_control():
    """PID参数调整接口"""
    direction = request.args.get('direction', '')  # 'direction' 或 'speed'
    kp = request.args.get('kp', '0')
    ki = request.args.get('ki', '0')
    kd = request.args.get('kd', '0')
    
    try:
        # 验证参数
        kp_val = float(kp)
        ki_val = float(ki)
        kd_val = float(kd)
        
        if direction not in ['direction', 'speed']:
            return Response('Invalid direction parameter', status=400)
        
        # 调用电机控制器的PID设置方法
        print(f"PID参数设置 - 方向: {direction}, Kp: {kp_val}, Ki: {ki_val}, Kd: {kd_val}")
        
        if motor_controller:
            try:
                motor_controller.set_pid_params(direction, kp_val, ki_val, kd_val)
                print(f"PID参数已发送到STM32: {direction} - Kp:{kp_val}, Ki:{ki_val}, Kd:{kd_val}")
            except Exception as e:
                print(f"发送PID参数到STM32时出错: {e}")
                return Response('PID参数发送失败', status=500)
        else:
            print("警告: 电机控制器未初始化，PID参数未发送")
        
        response = Response('PID参数设置成功')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except ValueError:
        return Response('Invalid PID parameters', status=400)
    except Exception as e:
        print(f"PID参数设置错误: {e}")
        return Response('PID参数设置失败', status=500)

@app.route('/stream.mjpg')
def stream():
    def generate():
        try:
            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                
                if frame:
                    # Build MJPEG frame
                    yield (b'--FRAME\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' +
                           frame + b'\r\n')
                
                # Add delay to control frame rate if needed
                # time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            print(f"Stream error: {e}")
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=FRAME',
        headers={
            'Age': '0',
            'Cache-Control': 'no-cache, private',
            'Pragma': 'no-cache'
        }
    )

def start_http_server(host='0.0.0.0', port=8080, debug=False):
    """Start HTTP server"""
    global output
    output = StreamingOutput()

    print(f'HTTP Server started running on {host}:{port}')
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    start_http_server()