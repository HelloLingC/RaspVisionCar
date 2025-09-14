# STM32串口IO使用指南

## 概述

`serial_io.py` 模块提供了一个统一的STM32串口通信接口，整合了发送和接收功能，支持持续读取STM32数据。

## 主要特性

- ✅ **统一接口**: 整合发送和接收功能
- ✅ **持续读取**: 后台线程持续读取STM32数据
- ✅ **数据解析**: 自动解析不同前缀的数据包
- ✅ **回调机制**: 支持数据接收回调函数
- ✅ **队列管理**: 内置数据队列，避免数据丢失
- ✅ **统计信息**: 提供详细的通信统计
- ✅ **自动检测**: 自动检测STM32设备端口
- ✅ **线程安全**: 支持多线程环境

## 快速开始

### 1. 基本使用

```python
from gpio.serial_io import init_stm32_io, get_stm32_io, cleanup_stm32_io

# 初始化STM32 IO控制器
if init_stm32_io():
    stm32_io = get_stm32_io()
    
    # 发送命令
    result = stm32_io.move_car('forward', 50).
    print(f"移动结果: {result}")
    
    # 获取传感器数据
    sensor_data = stm32_io.get_sensor_data()
    print(f"传感器数据: {sensor_data}")
    
    # 清理资源
    cleanup_stm32_io()
```

### 2. 数据接收回调

```python
from gpio.serial_io import SerialData

def data_callback(data: SerialData):
    print(f"收到数据: {data.data_type}")
    print(f"内容: {data.parsed_data}")
    print(f"时间: {data.timestamp}")

# 添加回调函数
stm32_io.add_data_callback(data_callback)
```

### 3. 手动获取数据

```python
# 获取最新数据
latest_data = stm32_io.get_latest_data()
if latest_data:
    print(f"最新数据: {latest_data.parsed_data}")

# 获取特定类型的数据
sensor_data = stm32_io.get_latest_data("sensor_data")
if sensor_data:
    print(f"传感器数据: {sensor_data.parsed_data}")

# 获取所有队列中的数据
all_data = stm32_io.get_all_data("sensor_data")
for data in all_data:
    print(f"传感器数据: {data.parsed_data}")
```

## 数据格式

### 支持的数据类型

1. **响应数据** (`response`): 以 `ACK:` 开头
2. **错误数据** (`error`): 以 `ERR:` 开头  
3. **传感器数据** (`sensor_data`): 以 `DTP:` 开头
4. **原始数据** (`raw_data`): 其他格式

### 数据包格式

```json
{
  "timestamp": 1234567890.123,
  "raw_data": b"ACK:{\"status\":\"ok\"}",
  "parsed_data": {"status": "ok"},
  "data_type": "response"
}
```

## API参考

### STM32SerialIO类

#### 初始化
```python
stm32_io = STM32SerialIO(port=None, baudrate=115200, timeout=1.0)
```

#### 连接管理
- `connect()`: 连接到STM32设备
- `disconnect()`: 断开连接
- `find_stm32_port()`: 自动查找STM32端口

#### 数据接收
- `add_data_callback(callback)`: 添加数据回调函数
- `remove_data_callback(callback)`: 移除数据回调函数
- `get_latest_data(data_type=None, timeout=0.1)`: 获取最新数据
- `get_all_data(data_type=None)`: 获取所有数据
- `clear_data_queue()`: 清空数据队列

#### 命令发送
- `send_command(command, params=None)`: 发送结构化命令
- `move_car(direction, speed=50)`: 控制小车移动
- `set_motor_speed(left_speed, right_speed)`: 设置电机速度
- `get_sensor_data()`: 获取传感器数据
- `get_status()`: 获取状态
- `emergency_stop()`: 紧急停止

#### 统计信息
- `get_stats()`: 获取统计信息

### 全局函数

- `init_stm32_io(port=None, baudrate=115200)`: 初始化全局控制器
- `get_stm32_io()`: 获取全局控制器实例
- `cleanup_stm32_io()`: 清理全局控制器

## 使用示例

### 示例1: 基本控制

```python
from gpio.serial_io import init_stm32_io, get_stm32_io, cleanup_stm32_io

def main():
    # 初始化
    if not init_stm32_io():
        print("初始化失败")
        return
    
    stm32_io = get_stm32_io()
    
    try:
        # 控制小车
        stm32_io.move_car('forward', 50)
        time.sleep(2)
        stm32_io.move_car('stop')
        
        # 获取状态
        status = stm32_io.get_status()
        print(f"状态: {status}")
        
    finally:
        cleanup_stm32_io()
```

### 示例2: 数据监控

```python
from gpio.serial_io import init_stm32_io, get_stm32_io, cleanup_stm32_io, SerialData
import time

def monitor_sensors(data: SerialData):
    if data.data_type == "sensor_data":
        print(f"传感器数据: {data.parsed_data}")

def main():
    if not init_stm32_io():
        return
    
    stm32_io = get_stm32_io()
    stm32_io.add_data_callback(monitor_sensors)
    
    try:
        # 持续监控5秒
        time.sleep(5)
    finally:
        cleanup_stm32_io()
```

### 示例3: 高级使用

```python
from gpio.serial_io import STM32SerialIO, SerialData
import time

def main():
    # 直接创建实例
    stm32_io = STM32SerialIO()
    
    if not stm32_io.connect():
        print("连接失败")
        return
    
    try:
        # 添加多个回调
        def log_data(data: SerialData):
            print(f"[LOG] {data.data_type}: {data.parsed_data}")
        
        def alert_on_error(data: SerialData):
            if data.data_type == "error":
                print(f"[ALERT] 错误: {data.parsed_data}")
        
        stm32_io.add_data_callback(log_data)
        stm32_io.add_data_callback(alert_on_error)
        
        # 发送命令并等待响应
        result = stm32_io.send_command("get_sensors")
        print(f"命令结果: {result}")
        
        # 获取统计信息
        stats = stm32_io.get_stats()
        print(f"统计: {stats}")
        
    finally:
        stm32_io.disconnect()
```

## 注意事项

1. **资源管理**: 使用完毕后务必调用 `cleanup_stm32_io()` 或 `disconnect()`
2. **线程安全**: 模块内部使用线程锁，支持多线程环境
3. **数据队列**: 队列大小限制为1000，超出时会丢弃最旧的数据
4. **错误处理**: 所有方法都有异常处理，不会导致程序崩溃
5. **向后兼容**: 旧的 `serial_receive.py` 仍然可用，但会显示弃用警告

