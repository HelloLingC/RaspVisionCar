# WebSocket server for RaspVisionCar console
# Handles real-time control commands and status updates

from flask import Flask
from flask_socketio import SocketIO, emit
import time
import json
import threading

# Create Flask App with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局状态变量
car_status = {
    'battery_level': 85,
    'current_speed': 0,
    'current_direction': 'stop',
    'connection_status': 'connected',
    'uptime': '00:00:00',
    'is_moving': False
}

# 启动时间记录
start_time = time.time()

def update_uptime():
    """更新运行时间"""
    global start_time
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    car_status['uptime'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def broadcast_status():
    """定期广播状态更新"""
    while True:
        try:
            update_uptime()
            socketio.emit('status_update', car_status)
            time.sleep(1)  # 每秒更新一次
        except Exception as e:
            print(f"状态广播错误: {e}")
            time.sleep(5)

# WebSocket 事件处理
@socketio.on('connect')
def handle_connect():
    print('WebSocket client connected')
    emit('status', {'message': 'Connected successfully', 'connected': True})
    emit('status_data', car_status)

@socketio.on('disconnect')
def handle_disconnect():
    print('WebSocket client disconnected')

@socketio.on('car_control')
def handle_car_control(data):
    """Handle car control command"""
    try:
        command = data.get('command', '')
        speed = data.get('speed', 50)
        direction = data.get('direction', '')
        
        print(f"WS_CMD: {command}, speed: {speed}, direction: {direction}")
        
        # Update car status
        car_status['current_speed'] = speed
        car_status['current_direction'] = direction
        car_status['is_moving'] = command == 'move' and speed > 0
        
        # Here you can add actual car control logic
        # 例如：control_car(direction, speed)
        
        # Send confirmation message back to client
        emit('control_response', {
            'status': 'success',
            'message': f'Command executed successfully: {command}',
            'command': command,
            'speed': speed,
            'direction': direction
        })
        
        # Broadcast status update to all connected clients
        socketio.emit('status_update', car_status)
        
    except Exception as e:
        print(f"Control command processing error: {e}")
        emit('control_response', {
            'status': 'error',
            'message': f'Command execution failed: {str(e)}'
        })

@socketio.on('get_status')
def handle_get_status():
    """Get current car status"""
    try:
        update_uptime()
        emit('status_data', car_status)
    except Exception as e:
        print(f"Get status error: {e}")
        emit('status_data', {'error': str(e)})

@socketio.on('emergency_stop')
def handle_emergency_stop():
    """Emergency stop"""
    try:
        print("紧急停止命令执行")
        
        # Update status
        car_status['current_speed'] = 0
        car_status['current_direction'] = 'stop'
        car_status['is_moving'] = False
        
        # Here you can add actual emergency stop logic
        # 例如：emergency_stop_car()
        
        emit('emergency_response', {
            'status': 'success',
            'message': '紧急停止已执行'
        })
        
        # 广播紧急停止事件
        socketio.emit('emergency_alert', {
            'message': '紧急停止已激活',
            'timestamp': time.time()
        })
        
        # 广播状态更新
        socketio.emit('status_update', car_status)
        
    except Exception as e:
        print(f"紧急停止错误: {e}")
        emit('emergency_response', {
            'status': 'error',
            'message': f'紧急停止失败: {str(e)}'
        })

@socketio.on('set_battery_level')
def handle_set_battery_level(data):
    """设置电池电量（用于测试）"""
    try:
        battery_level = data.get('battery_level', 85)
        car_status['battery_level'] = max(0, min(100, battery_level))
        
        emit('battery_update', {
            'battery_level': car_status['battery_level'],
            'timestamp': time.time()
        })
        
        print(f"电池电量更新为: {car_status['battery_level']}%")
        
    except Exception as e:
        print(f"电池电量设置错误: {e}")

def start_websocket_server(host='0.0.0.0', port=5000, debug=False):
    """启动 WebSocket 服务器"""
    print(f'WebSocket Server started running on {host}:{port}')
    
    # 启动状态广播线程
    status_thread = threading.Thread(target=broadcast_status, daemon=True)
    status_thread.start()
    
    # 启动 SocketIO 服务器
    socketio.run(app, host=host, port=port, debug=debug)

if __name__ == '__main__':
    start_websocket_server()