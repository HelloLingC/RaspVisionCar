"""
STM32串口IO统一模块
整合发送和接收功能，实现持续读取STM32数据
"""

import serial
import serial.tools.list_ports
import time
import threading
import json
import queue
from typing import Optional, Dict, Any, List, Callable
import logging
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SerialData:
    """串口数据结构"""
    timestamp: float
    raw_data: bytes
    parsed_data: Optional[Dict[str, Any]] = None
    data_type: str = "unknown"

class STM32SerialIO:
    """STM32串口IO统一控制器"""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0):
        """
        初始化STM32串口IO控制器
        
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
        
        # 数据接收相关
        self.receive_thread: Optional[threading.Thread] = None
        self.receive_running = False
        self.data_queue = queue.Queue(maxsize=1000)
        self.data_buffer = b''
        self.data_callbacks: List[Callable[[SerialData], None]] = []
        
        # 协议配置
        self.response_prefix = "ACK:"
        self.error_prefix = "ERR:"
        self.data_prefix = "DTP"
        
        # 统计信息
        self.stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'data_received': 0,
            'errors': 0,
            'connection_time': None,
            'last_command_time': None,
            'last_data_time': None,
            'bytes_received': 0,
            'bytes_sent': 0
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
            
            if "/dev/ttyAMA0" in [port.device for port in ports]:
                logger.info(f"使用 /dev/ttyAMA0 端口")
                return "/dev/ttyAMA0"
            # 如果没有找到特定设备，返回第一个可用端口
            # if ports:
            #     logger.info(f"使用第一个可用端口: {ports[0].device}")
            #     return ports[0].device
                
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
                
                # 启动数据接收线程
                self.start_receiving()
                
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
            
            # 停止接收线程
            self.stop_receiving()
            
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                    logger.info("STM32串口连接已断开")
                except Exception as e:
                    logger.error(f"断开连接时出错: {e}")
                finally:
                    self.serial_conn = None
    
    def start_receiving(self):
        """启动数据接收线程"""
        if self.receive_running:
            return
        
        self.receive_running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        logger.info("数据接收线程已启动")
    
    def stop_receiving(self):
        """停止数据接收线程"""
        self.receive_running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        logger.info("数据接收线程已停止")
    
    def _receive_loop(self):
        """数据接收循环"""
        logger.info("开始持续读取STM32数据...")
        
        while self.receive_running and self.connected:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    time.sleep(0.1)
                    continue
                
                # 读取可用数据
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    if data:
                        self._process_received_data(data)
                else:
                    time.sleep(0.01)  # 短暂休眠避免CPU占用过高
                    
            except Exception as e:
                logger.error(f"接收数据时出错: {e}")
                self.stats['errors'] += 1
                time.sleep(0.1)
    
    def _process_received_data(self, data: bytes):
        """处理接收到的数据"""
        try:
            self.data_buffer += data
            self.stats['bytes_received'] += len(data)
            self.stats['last_data_time'] = time.time()
            
            # 处理完整的数据包
            while b'\n' in self.data_buffer:
                line_end = self.data_buffer.find(b'\n')
                line = self.data_buffer[:line_end].strip()
                self.data_buffer = self.data_buffer[line_end + 1:]
                
                if line:
                    self._parse_and_queue_data(line)
                    
        except Exception as e:
            logger.error(f"处理接收数据时出错: {e}")
            self.stats['errors'] += 1
    
    def _parse_and_queue_data(self, data: bytes):
        """解析并队列化数据"""
        try:
            # 创建串口数据对象
            serial_data = SerialData(
                timestamp=time.time(),
                raw_data=data,
                data_type="unknown"
            )

            # 尝试解析数据
            data_str = data.decode('utf-8')
            # print(f"收到数据: {data_str}")

            # 添加到队列
            try:
                self.data_queue.put_nowait(serial_data)
            except queue.Full:
                # 队列满时移除最旧的数据
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.put_nowait(serial_data)
                except queue.Empty:
                    pass
            
            # 调用回调函数
            for callback in self.data_callbacks:
                try:
                    callback(serial_data)
                except Exception as e:
                    logger.error(f"数据回调函数执行失败: {e}")
                    
        except Exception as e:
            logger.error(f"解析数据时出错: {e}")
            self.stats['errors'] += 1
    
    def add_data_callback(self, callback: Callable[[SerialData], None]):
        """
        添加数据接收回调函数
        
        Args:
            callback: 回调函数，接收SerialData参数
        """
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable[[SerialData], None]):
        """
        移除数据接收回调函数
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def get_latest_data(self, data_type: Optional[str] = None, timeout: float = 0.1) -> Optional[SerialData]:
        """
        获取最新的数据
        
        Args:
            data_type: 数据类型过滤，如果为None则获取任何类型
            timeout: 超时时间
            
        Returns:
            最新的数据，如果没有数据返回None
        """
        try:
            if data_type:
                # 查找特定类型的数据
                latest_data = None
                temp_queue = queue.Queue()
                
                # 遍历队列查找最新数据
                while not self.data_queue.empty():
                    try:
                        data = self.data_queue.get_nowait()
                        if data.data_type == data_type:
                            latest_data = data
                        temp_queue.put(data)
                    except queue.Empty:
                        break
                
                # 将数据放回队列
                while not temp_queue.empty():
                    try:
                        self.data_queue.put_nowait(temp_queue.get_nowait())
                    except queue.Full:
                        break
                
                return latest_data
            else:
                # 获取最新数据
                return self.data_queue.get(timeout=timeout)
                
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"获取数据时出错: {e}")
            return None
    
    def get_all_data(self, data_type: Optional[str] = None) -> List[SerialData]:
        """
        获取所有队列中的数据
        
        Args:
            data_type: 数据类型过滤，如果为None则获取所有类型
            
        Returns:
            数据列表
        """
        data_list = []
        temp_queue = queue.Queue()
        
        try:
            # 清空队列并收集数据
            while not self.data_queue.empty():
                try:
                    data = self.data_queue.get_nowait()
                    if not data_type or data.data_type == data_type:
                        data_list.append(data)
                    temp_queue.put(data)
                except queue.Empty:
                    break
            
            # 将数据放回队列
            while not temp_queue.empty():
                try:
                    self.data_queue.put_nowait(temp_queue.get_nowait())
                except queue.Full:
                    break
                    
        except Exception as e:
            logger.error(f"获取所有数据时出错: {e}")
        
        return data_list
    
    def clear_data_queue(self):
        """清空数据队列"""
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

    def _send_test_command(self) -> bool:
        """
        发送测试命令验证连接

        Returns:
            测试是否成功
        """
        try:
            test_cmd = "ping"
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
                # 发送命令
                command_bytes = command.encode('utf-8')
                self.serial_conn.write(command_bytes)
                self.serial_conn.flush()

                self.stats['commands_sent'] += 1
                self.stats['bytes_sent'] += len(command_bytes)
                self.stats['last_command_time'] = time.time()
                logger.debug(f"发送命令: {command.strip()}")

                if expect_response:
                    # 等待响应
                    start_time = time.time()
                    while time.time() - start_time < self.timeout:
                        data = self.get_latest_data("response", timeout=0.1)
                        if data:
                            return data.parsed_data
                    return None
                
                return None
                
            except Exception as e:
                logger.error(f"发送命令失败: {e}")
                self.stats['errors'] += 1
                return None

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        """
        return self._send_raw_command(command, expect_response=True)

    def get_status(self) -> Dict[str, Any]:
        """
        获取STM32状态
        
        Returns:
            状态信息
        """
        return self.send_command('get_status')
    
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
        stats['queue_size'] = self.data_queue.qsize()
        stats['receive_running'] = self.receive_running
        
        if self.stats['connection_time']:
            stats['uptime'] = time.time() - self.stats['connection_time']
        else:
            stats['uptime'] = 0
            
        return stats

# 全局STM32控制器实例
_stm32_io: Optional[STM32SerialIO] = None

def init_stm32_io(port: Optional[str] = None, baudrate: int = 115200) -> bool:
    """
    初始化STM32 IO控制器
    
    Args:
        port: 串口端口，如果为None则自动检测
        baudrate: 波特率
        
    Returns:
        初始化是否成功
    """
    global _stm32_io
    
    try:
        _stm32_io = STM32SerialIO(port, baudrate)
        return _stm32_io.connect()
    except Exception as e:
        logger.error(f"初始化STM32 IO控制器失败: {e}")
        return False

def get_stm32_io() -> Optional[STM32SerialIO]:
    """
    获取STM32 IO控制器实例
    
    Returns:
        STM32 IO控制器实例，如果未初始化返回None
    """
    return _stm32_io

def cleanup_stm32_io():
    """清理STM32 IO控制器资源"""
    global _stm32_io
    
    if _stm32_io:
        _stm32_io.disconnect()
        _stm32_io = None

if __name__ == '__main__':
    # 测试代码
    print("STM32串口IO测试...")
    
    # 数据接收回调函数
    def data_callback(data: SerialData):
        print(f"[{datetime.fromtimestamp(data.timestamp).strftime('%H:%M:%S.%f')[:-3]}] "
              f"收到数据: {data.data_type} - {data.parsed_data}")
    
    # 初始化控制器
    if init_stm32_io():
        print("STM32 IO控制器初始化成功")
        
        # 添加数据回调
        _stm32_io.add_data_callback(data_callback)
        
        try:
            # 测试基本命令
            print("\n测试基本命令...")
            
            # 获取状态
            result = _stm32_io.get_status()
            print(f"获取状态: {result}")

            # 持续读取数据5秒
            print("\n持续读取数据5秒...")
            start_time = time.time()
            while time.time() - start_time < 5:
                latest_data = _stm32_io.get_latest_data()
                if latest_data:
                    print(f"最新数据: {latest_data.data_type} - {latest_data.parsed_data}")
            
            # 获取统计信息
            stats = _stm32_io.get_stats()
            print(f"\n统计信息: {stats}")
            
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            cleanup_stm32_io()
    else:
        print("STM32 IO控制器初始化失败")
