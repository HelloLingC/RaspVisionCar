#!/usr/bin/env python3
"""
STM32串口通信测试脚本
用于测试与STM32的串口通信功能
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from serial_pi.serial_io import init_stm32_io, get_stm32_io, cleanup_stm32_io
from serial_pi.motor import Motor_Controller


def test_motor_control():
    """测试电机控制"""
    print("\n=== 测试电机控制 ===")
    
    controller = Motor_Controller()
    if not controller:
        print("错误: STM32控制器未初始化")
        return False
    
    # 测试设置电机速度
    print("1. 测试设置电机速度 (前进)...")
    result = controller.set_motor_speed(50, 50)
    print(f"   结果: {result}")
    time.sleep(2)
    
    print("2. 测试设置电机速度 (左转)...")
    result = controller.set_motor_speed(-30, 30)
    print(f"   结果: {result}")
    time.sleep(2)
    
    print("3. 测试设置电机速度 (停止)...")
    result = controller.set_motor_speed(0, 0)
    print(f"   结果: {result}")
    
    return True

def show_statistics():
    """显示统计信息"""
    print("\n=== 统计信息 ===")
    
    controller = get_stm32_io()
    if not controller:
        print("错误: STM32控制器未初始化")
        return
    
    stats = controller.get_stats()
    print(f"连接状态: {'已连接' if stats['connected'] else '未连接'}")
    print(f"串口端口: {stats['port']}")
    print(f"波特率: {stats['baudrate']}")
    print(f"运行时间: {stats['uptime']:.2f} 秒")
    print(f"发送命令数: {stats['commands_sent']}")
    print(f"收到响应数: {stats['responses_received']}")
    print(f"错误次数: {stats['errors']}")

def main():
    """主测试函数"""
    print("STM32串口通信测试")
    print("=" * 50)
    
    # 初始化STM32控制器
    print("正在初始化STM32控制器...")
    if not init_stm32_io():
        print("错误: STM32控制器初始化失败")
        print("请检查:")
        print("1. STM32设备是否已连接")
        print("2. 串口驱动是否已安装")
        print("3. 串口是否被其他程序占用")
        return
    
    print("STM32控制器初始化成功!")
    
    try:
        # 运行测试
        test_motor_control()

        # 显示统计信息
        show_statistics()
        
        print("\n测试完成!")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
    finally:
        # 清理资源
        cleanup_stm32_io()
        print("STM32控制器资源已清理")

if __name__ == '__main__':
    main()
