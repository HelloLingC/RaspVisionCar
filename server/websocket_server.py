# WebSocket server for RaspVisionCar console
# 使用 websockets 库实现 WebSocket 服务器

import asyncio
import websockets
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial_pi.serial_io as serial_io

# 导入电机控制器
try:
    from serial_pi.motor import Motor_Controller, get_motor_controller
    motor_controller = get_motor_controller()
    print("电机控制器初始化成功")
except ImportError as e:
    print(f"无法导入电机控制器: {e}")
    motor_controller = None

# 存储连接的客户端
connected_clients = set()

def calculate_motor_speeds(direction: str, speed: int) -> tuple:
    """
    根据方向和速度计算左右电机速度
    
    Args:
        direction: 方向 ('forward', 'backward', 'left', 'right')
        speed: 速度百分比 (0-100)
        
    Returns:
        (left_speed, right_speed) 元组，速度范围 -100 到 100
    """
    # 将百分比转换为实际速度值
    actual_speed = int(speed)
    
    if direction == 'forward':
        return (actual_speed, actual_speed)
    elif direction == 'backward':
        return (-actual_speed, -actual_speed)
    elif direction == 'left':
        # 左转：左轮减速或反转，右轮保持
        return (-actual_speed // 2, actual_speed)
    elif direction == 'right':
        # 右转：右轮减速或反转，左轮保持
        return (actual_speed, -actual_speed // 2)
    else:
        return (0, 0)

async def handle_client(websocket, path):
    """处理客户端 WebSocket 连接"""
    # 添加客户端到连接集合
    connected_clients.add(websocket)
    client_address = websocket.remote_address
    print(f"客户端连接: {client_address}")
    
    try:
        # 发送欢迎消息
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'WebSocket 连接成功'
        }))
        
        # 接收消息
        async for message in websocket:
            try:
                data = json.loads(message)
                command_type = data.get('type', '')
                
                if command_type == 'move':
                    # 处理移动命令
                    direction = data.get('direction', '')
                    speed = data.get('speed', 50)
                    
                    print(f"收到移动命令: 方向={direction}, 速度={speed}%")
                    
                    # 计算电机速度
                    left_speed, right_speed = calculate_motor_speeds(direction, speed)
                    
                    # 发送命令到STM32
                    if motor_controller:
                        try:
                            stm32_io = serial_io.get_stm32_io()
                            if stm32_io and stm32_io.connected:
                                # 使用串口IO发送电机速度命令
                                command = f'LS:{left_speed},RS:{right_speed}\n'
                                stm32_io.send_command(command)
                                print(f"已发送电机命令: {command.strip()}")
                                
                                # 发送确认消息
                                await websocket.send(json.dumps({
                                    'type': 'move_ack',
                                    'direction': direction,
                                    'speed': speed,
                                    'left_speed': left_speed,
                                    'right_speed': right_speed,
                                    'status': 'success'
                                }))
                            else:
                                print("STM32 串口未连接")
                                await websocket.send(json.dumps({
                                    'type': 'error',
                                    'message': 'STM32 串口未连接'
                                }))
                        except Exception as e:
                            print(f"发送移动命令失败: {e}")
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': f'发送命令失败: {str(e)}'
                            }))
                    else:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': '电机控制器未初始化'
                        }))
                
                elif command_type == 'stop':
                    # 停止命令
                    print("收到停止命令")
                    if motor_controller:
                        try:
                            stm32_io = serial_io.get_stm32_io()
                            if stm32_io and stm32_io.connected:
                                stm32_io.send_command('stop\n')
                                await websocket.send(json.dumps({
                                    'type': 'stop_ack',
                                    'status': 'success'
                                }))
                        except Exception as e:
                            print(f"发送停止命令失败: {e}")
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': f'发送停止命令失败: {str(e)}'
                            }))
                
                elif command_type == 'start':
                    # 启动命令
                    print("收到启动命令")
                    if motor_controller:
                        try:
                            stm32_io = serial_io.get_stm32_io()
                            if stm32_io and stm32_io.connected:
                                stm32_io.send_command('start\n')
                                await websocket.send(json.dumps({
                                    'type': 'start_ack',
                                    'status': 'success'
                                }))
                        except Exception as e:
                            print(f"发送启动命令失败: {e}")
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': f'发送启动命令失败: {str(e)}'
                            }))
                
                else:
                    # 未知命令类型
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'未知命令类型: {command_type}'
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': '无效的 JSON 格式'
                }))
            except Exception as e:
                print(f"处理消息时出错: {e}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'处理消息失败: {str(e)}'
                }))
    
    except websockets.exceptions.ConnectionClosed:
        print(f"客户端断开连接: {client_address}")
    except Exception as e:
        print(f"WebSocket 连接错误: {e}")
    finally:
        # 从连接集合中移除
        connected_clients.discard(websocket)

async def main(host='0.0.0.0', port=5000):
    """启动 WebSocket 服务器"""
    print(f'WebSocket 服务器启动: ws://{host}:{port}')
    
    # 初始化STM32串口连接
    if not serial_io.get_stm32_io():
        print("正在初始化 STM32 串口连接...")
        serial_io.init_stm32_io()
    
    # 启动 WebSocket 服务器
    async with websockets.serve(handle_client, host, port):
        print(f"✅ WebSocket 服务器运行中，等待客户端连接...")
        await asyncio.Future()  # 永远运行

def start_websocket_server(host='0.0.0.0', port=5000, debug=False):
    """启动 WebSocket 服务器（同步包装函数）"""
    try:
        asyncio.run(main(host, port))
    except KeyboardInterrupt:
        print("\nWebSocket 服务器已停止")
    except Exception as e:
        print(f"WebSocket 服务器错误: {e}")

if __name__ == '__main__':
    start_websocket_server()

