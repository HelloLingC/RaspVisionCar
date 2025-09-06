# TCP客户端用于从串口TCP服务器读取JustFloat数据
# Should be running on PC

import socket
import struct
import threading
import time
import json
from typing import Optional, Dict, Any

class JustFloatTCPClient:
    """JustFloat TCP客户端类"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        """
        初始化TCP客户端
        
        Args:
            host: 服务器IP地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # 数据统计
        self.stats = {
            'bytes_received': 0,
            'packets_received': 0,
            'connection_time': None,
            'last_data_time': None,
            'errors': 0
        }
        
        # 最新接收的数据
        self.latest_data: Optional[Dict[str, Any]] = None
        
    def connect(self) -> bool:
        """
        连接到TCP服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5秒超时
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.stats['connection_time'] = time.time()
            print(f"成功连接到JustFloat服务器 {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"连接JustFloat服务器失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            
        print("JustFloat TCP客户端已断开连接")
    
    def parse_justfloat_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        解析JustFloat数据包
        
        JustFloat协议假设数据包格式为:
        - 包头: 4字节标识符 (0x4A, 0x75, 0x73, 0x74) = "Just"
        - 数据长度: 4字节 (小端序)
        - 数据: N个float32值 (小端序)
        - 校验和: 4字节 (可选)
        
        Args:
            data: 接收到的原始数据
            
        Returns:
            解析后的数据字典，如果解析失败返回None
        """
        try:
            if len(data) < 8:  # 至少需要包头+长度
                return None
                
            # 检查包头
            header = data[:4]
            if header != b'Just':
                # 如果不是标准包头，尝试直接解析为float数组
                return self.parse_simple_float_array(data)
            
            # 解析数据长度
            data_length = struct.unpack('<I', data[4:8])[0]
            
            if len(data) < 8 + data_length:
                print(f"数据包不完整: 期望{8 + data_length}字节，实际{len(data)}字节")
                return None
            
            # 解析float数据
            float_data = data[8:8+data_length]
            float_count = data_length // 4  # 每个float32占4字节
            
            if data_length % 4 != 0:
                print(f"数据长度不是4的倍数: {data_length}")
                return None
            
            values = []
            for i in range(float_count):
                offset = i * 4
                value = struct.unpack('<f', float_data[offset:offset+4])[0]
                values.append(value)
            
            return {
                'timestamp': time.time(),
                'values': values,
                'count': float_count,
                'raw_size': len(data)
            }
            
        except Exception as e:
            print(f"解析JustFloat数据失败: {e}")
            return None
    
    def parse_simple_float_array(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        解析简单的float数组（无包头）
        
        Args:
            data: 原始数据
            
        Returns:
            解析后的数据字典
        """
        try:
            if len(data) % 4 != 0:
                return None
                
            float_count = len(data) // 4
            values = []
            
            for i in range(float_count):
                offset = i * 4
                value = struct.unpack('<f', data[offset:offset+4])[0]
                values.append(value)
            
            return {
                'timestamp': time.time(),
                'values': values,
                'count': float_count,
                'raw_size': len(data)
            }
            
        except Exception as e:
            print(f"解析简单float数组失败: {e}")
            return None
    
    def receive_data_loop(self):
        """数据接收循环"""
        buffer = b''
        
        while self.running and self.connected:
            try:
                if not self.socket:
                    break
                    
                # 接收数据
                data = self.socket.recv(4096)
                if not data:
                    print("服务器关闭了连接")
                    break
                
                self.stats['bytes_received'] += len(data)
                buffer += data
                
                # 尝试解析数据包
                while len(buffer) >= 4:
                    # 查找包头
                    header_pos = buffer.find(b'Just')
                    if header_pos == -1:
                        # 没有找到包头，尝试解析为简单float数组
                        if len(buffer) >= 4 and len(buffer) % 4 == 0:
                            parsed_data = self.parse_simple_float_array(buffer)
                            if parsed_data:
                                self.latest_data = parsed_data
                                self.stats['packets_received'] += 1
                                self.stats['last_data_time'] = time.time()
                                print(f"接收到JustFloat数据: {parsed_data['values']}")
                            buffer = b''
                        else:
                            # 保留最后几个字节，可能是不完整的数据
                            buffer = buffer[-3:]
                        break
                    
                    # 移除包头前的数据
                    if header_pos > 0:
                        buffer = buffer[header_pos:]
                    
                    # 检查是否有足够的数据解析包头和长度
                    if len(buffer) < 8:
                        break
                    
                    # 解析数据长度
                    data_length = struct.unpack('<I', buffer[4:8])[0]
                    total_packet_size = 8 + data_length
                    
                    if len(buffer) < total_packet_size:
                        break  # 数据包不完整，等待更多数据
                    
                    # 解析完整数据包
                    packet_data = buffer[:total_packet_size]
                    parsed_data = self.parse_justfloat_data(packet_data)
                    
                    if parsed_data:
                        self.latest_data = parsed_data
                        self.stats['packets_received'] += 1
                        self.stats['last_data_time'] = time.time()
                        print(f"接收到JustFloat数据包: {parsed_data['values']}")
                    
                    # 移除已处理的数据
                    buffer = buffer[total_packet_size:]
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收数据时出错: {e}")
                self.stats['errors'] += 1
                time.sleep(0.1)
        
        self.connected = False
        print("数据接收循环结束")
    
    def start(self) -> bool:
        """
        启动TCP客户端
        
        Returns:
            bool: 启动是否成功
        """
        if self.running:
            print("TCP客户端已在运行")
            return True
        
        if not self.connect():
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self.receive_data_loop, daemon=True)
        self.thread.start()
        
        print("JustFloat TCP客户端已启动")
        return True
    
    def stop(self):
        """停止TCP客户端"""
        if not self.running:
            return
        
        self.running = False
        self.disconnect()
        print("JustFloat TCP客户端已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.stats.copy()
        stats['connected'] = self.connected
        stats['running'] = self.running
        
        if self.stats['connection_time']:
            stats['uptime'] = time.time() - self.stats['connection_time']
        else:
            stats['uptime'] = 0
            
        return stats
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        获取最新接收的数据
        
        Returns:
            最新数据字典，如果没有数据返回None
        """
        return self.latest_data

# 全局客户端实例
_justfloat_client: Optional[JustFloatTCPClient] = None

def start_justfloat_server(host: str = '127.0.0.1', port: int = 8080) -> bool:
    """
    启动JustFloat TCP客户端服务器
    
    Args:
        host: 服务器IP地址
        port: 服务器端口
        
    Returns:
        bool: 启动是否成功
    """
    global _justfloat_client
    
    if _justfloat_client and _justfloat_client.running:
        print("JustFloat客户端已在运行")
        return True
    
    _justfloat_client = JustFloatTCPClient(host, port)
    return _justfloat_client.start()

def stop_justfloat_server():
    """停止JustFloat TCP客户端服务器"""
    global _justfloat_client
    
    if _justfloat_client:
        _justfloat_client.stop()
        _justfloat_client = None

def get_justfloat_stats() -> Dict[str, Any]:
    """
    获取JustFloat连接统计信息
    
    Returns:
        统计信息字典
    """
    global _justfloat_client
    
    if _justfloat_client:
        return _justfloat_client.get_stats()
    else:
        return {
            'connected': False,
            'running': False,
            'bytes_received': 0,
            'packets_received': 0,
            'connection_time': None,
            'last_data_time': None,
            'errors': 0,
            'uptime': 0
        }

def get_justfloat_data() -> Optional[Dict[str, Any]]:
    """
    获取最新JustFloat数据
    
    Returns:
        最新数据字典，如果没有数据返回None
    """
    global _justfloat_client
    
    if _justfloat_client:
        return _justfloat_client.get_latest_data()
    else:
        return None

if __name__ == '__main__':
    # 测试代码
    print("启动JustFloat TCP客户端测试...")
    
    # 启动客户端
    if start_justfloat_server('127.0.0.1', 8080):
        try:
            # 运行30秒
            for i in range(30):
                time.sleep(1)
                stats = get_justfloat_stats()
                print(f"状态: 连接={stats['connected']}, 数据包={stats['packets_received']}, 错误={stats['errors']}")
                
                data = get_justfloat_data()
                if data:
                    print(f"最新数据: {data['values']}")
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            stop_justfloat_server()
    else:
        print("启动失败")