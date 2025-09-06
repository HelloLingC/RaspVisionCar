"""
STM32串口通信模块
用于向STM32发送控制命令
"""

import serial
import serial.tools.list_ports
import time
import threading
import json
from typing import Optional, Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STM32SerialController:
    """STM32串口控制器类"""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0):
        """
        初始化STM32串口控制器
        
        Args:
            port: 串口端口，如果为None则自动检测
            baudrate: 波特率，默认115200
            timeout: 超时时间，默认1秒
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self.lock = threading.Lock()
        
        # 命令协议配置
        self.command_prefix = "CMD:"
        self.response_prefix = "ACK:"
        self.error_prefix = "ERR:"

        # 统计信息
        self.stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'errors': 0,
            'connection_time': None,
            'last_command_time': None
        }
    
    def find_stm32_port(self) -> Optional[str]:
        """
        自动查找STM32设备端口
        
        Returns:
            找到的端口名称，如果未找到返回None
        """
        try:
            ports = serial.tools.list_ports.comports()
            logger.info(f"发现 {len(ports)} 个串口设备:")
            
            for port in ports:
                logger.info(f"  - {port.device}: {port.description}")
                # 常见的STM32设备描述关键词
                stm32_keywords = ['STM32', 'USB Serial', 'Virtual COM Port', 'CH340', 'CP210']
                if any(keyword in port.description for keyword in stm32_keywords):
                    logger.info(f"找到可能的STM32设备: {port.device}")
                    return port.device
            
            # 如果没有找到特定设备，返回第一个可用端口
            if ports:
                logger.info(f"使用第一个可用端口: {ports[0].device}")
                return ports[0].device
                
        except Exception as e:
            logger.error(f"查找串口设备失败: {e}")
        
        return None
    
    def connect(self) -> bool:
        """
        连接到STM32设备
        
        Returns:
            连接是否成功
        """
        try:
            # 如果没有指定端口，自动查找
            if not self.port:
                self.port = self.find_stm32_port()
                if not self.port:
                    logger.error("未找到可用的串口设备")
                    return False
            
            # 创建串口连接
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # 等待连接稳定
            time.sleep(0.5)
            
            # 测试连接
            if self.serial_conn.is_open:
                self.connected = True
                self.stats['connection_time'] = time.time()
                logger.info(f"成功连接到STM32设备: {self.port}")
                
                # 发送测试命令
                if self._send_test_command():
                    return True
                else:
                    logger.warning("连接成功但测试命令失败")
                    return True  # 仍然返回True，可能STM32没有实现测试命令
            else:
                logger.error("串口连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接STM32设备失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        with self.lock:
            self.connected = False
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                    logger.info("STM32串口连接已断开")
                except Exception as e:
                    logger.error(f"断开连接时出错: {e}")
                finally:
                    self.serial_conn = None
    
    def _send_test_command(self) -> bool:
        """
        发送测试命令验证连接
        
        Returns:
            测试是否成功
        """
        try:
            test_cmd = f"{self.command_prefix}PING\n"
            response = self._send_raw_command(test_cmd, expect_response=True)
            return response is not None
        except:
            return False
    
    def _send_raw_command(self, command: str, expect_response: bool = False) -> Optional[str]:
        """
        发送原始命令到STM32
        
        Args:
            command: 要发送的命令
            expect_response: 是否期望响应
            
        Returns:
            响应内容，如果没有响应或出错返回None
        """
        if not self.connected or not self.serial_conn:
            logger.error("串口未连接")
            return None
        
        with self.lock:
            try:
                # 清空输入缓冲区
                self.serial_conn.reset_input_buffer()
                
                # 发送命令
                command_bytes = command.encode('utf-8')
                self.serial_conn.write(command_bytes)
                self.serial_conn.flush()
                
                self.stats['commands_sent'] += 1
                self.stats['last_command_time'] = time.time()
                logger.debug(f"发送命令: {command.strip()}")
                
                if expect_response:
                    # 读取响应
                    response = self.serial_conn.readline().decode('utf-8').strip()
                    if response:
                        self.stats['responses_received'] += 1
                        logger.debug(f"收到响应: {response}")
                        return response
                
                return None
                
            except Exception as e:
                logger.error(f"发送命令失败: {e}")
                self.stats['errors'] += 1
                return None
    
    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送结构化命令到STM32
        
        Args:
            command: 命令名称
            params: 命令参数
            
        Returns:
            包含执行结果的字典
        """
        try:
            # 构建命令
            cmd_data = {
                'cmd': command,
                'timestamp': time.time(),
                'params': params or {}
            }
            
            cmd_str = f"{self.command_prefix}{cmd_data}"
            
            # 发送命令
            response = self._send_raw_command(cmd_str, expect_response=True)
            
            if response:
                if response.startswith(self.response_prefix):
                    # 成功响应
                    try:
                        response_data = json.loads(response[len(self.response_prefix):])
                        return {
                            'success': True,
                            'data': response_data,
                            'raw_response': response
                        }
                    except json.JSONDecodeError:
                        return {
                            'success': True,
                            'data': response[len(self.response_prefix):],
                            'raw_response': response
                        }
                elif response.startswith(self.error_prefix):
                    # 错误响应
                    return {
                        'success': False,
                        'error': response[len(self.error_prefix):],
                        'raw_response': response
                    }
                else:
                    # 其他响应
                    return {
                        'success': True,
                        'data': response,
                        'raw_response': response
                    }
            else:
                return {
                    'success': False,
                    'error': 'No response from STM32',
                    'raw_response': None
                }
                
        except Exception as e:
            logger.error(f"发送命令时出错: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_response': None
            }
    
    def move_car(self, direction: str, speed: int = 50) -> Dict[str, Any]:
        """
        控制小车移动
        
        Args:
            direction: 移动方向 ('forward', 'backward', 'left', 'right', 'stop')
            speed: 移动速度 (0-100)
            
        Returns:
            执行结果
        """
        return self.send_command('move', {
            'direction': direction,
            'speed': speed
        })
    
    def set_motor_speed(self, left_speed: int, right_speed: int) -> Dict[str, Any]:
        """
        设置左右电机速度
        
        Args:
            left_speed: 左电机速度 (-100到100)
            right_speed: 右电机速度 (-100到100)
            
        Returns:
            执行结果
        """
        return self.send_command('set_motor_speed', {
            'left_speed': left_speed,
            'right_speed': right_speed
        })

    
    def get_sensor_data(self) -> Dict[str, Any]:
        """
        获取传感器数据
        
        Returns:
            传感器数据
        """
        return self.send_command('get_sensors')
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取STM32状态
        
        Returns:
            状态信息
        """
        return self.send_command('get_status')
    
    def emergency_stop(self) -> Dict[str, Any]:
        """
        紧急停止
        
        Returns:
            执行结果
        """
        return self.send_command('emergency_stop')
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.stats.copy()
        stats['connected'] = self.connected
        stats['port'] = self.port
        stats['baudrate'] = self.baudrate
        
        if self.stats['connection_time']:
            stats['uptime'] = time.time() - self.stats['connection_time']
        else:
            stats['uptime'] = 0
            
        return stats

# 全局STM32控制器实例
_stm32_controller: Optional[STM32SerialController] = None

def init_stm32_controller(port: Optional[str] = None, baudrate: int = 115200) -> bool:
    """
    初始化STM32控制器
    
    Args:
        port: 串口端口，如果为None则自动检测
        baudrate: 波特率
        
    Returns:
        初始化是否成功
    """
    global _stm32_controller
    
    try:
        _stm32_controller = STM32SerialController(port, baudrate)
        return _stm32_controller.connect()
    except Exception as e:
        logger.error(f"初始化STM32控制器失败: {e}")
        return False

def get_stm32_controller() -> Optional[STM32SerialController]:
    """
    获取STM32控制器实例
    
    Returns:
        STM32控制器实例，如果未初始化返回None
    """
    return _stm32_controller

def send_car_command(direction: str, speed: int = 50) -> Dict[str, Any]:
    """
    发送小车控制命令的便捷函数
    
    Args:
        direction: 移动方向
        speed: 移动速度
        
    Returns:
        执行结果
    """
    if not _stm32_controller:
        return {
            'success': False,
            'error': 'STM32控制器未初始化'
        }
    
    return _stm32_controller.move_car(direction, speed)

def cleanup_stm32_controller():
    """清理STM32控制器资源"""
    global _stm32_controller
    
    if _stm32_controller:
        _stm32_controller.disconnect()
        _stm32_controller = None

if __name__ == '__main__':
    # 测试代码
    print("STM32串口通信测试...")
    
    # 初始化控制器
    if init_stm32_controller():
        print("STM32控制器初始化成功")
        
        try:
            # 测试基本命令
            print("\n测试基本命令...")
            
            # 获取状态
            result = _stm32_controller.get_status()
            print(f"获取状态: {result}")
            
            # 控制小车前进
            result = _stm32_controller.move_car('forward', 50)
            print(f"前进命令: {result}")
            time.sleep(2)
            
            # 停止小车
            result = _stm32_controller.move_car('stop')
            print(f"停止命令: {result}")
            
            # 获取统计信息
            stats = _stm32_controller.get_stats()
            print(f"\n统计信息: {stats}")
            
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            cleanup_stm32_controller()
    else:
        print("STM32控制器初始化失败")