#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JustFloat TCP客户端测试脚本
用于测试与STM32串口TCP服务器的通信
"""

import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.serial_tcp_client import start_justfloat_server, stop_justfloat_server, get_justfloat_stats, get_justfloat_data

def test_justfloat_client():
    """测试JustFloat TCP客户端"""
    print("=" * 50)
    print("JustFloat TCP客户端测试")
    print("=" * 50)
    
    # 配置参数
    HOST = str(input("HOST: "))  # TCP Server IP
    PORT = int(input("PORT: "))  # TCP Server Port
    
    print(f"尝试连接到 {HOST}:{PORT}")
    
    # 启动客户端
    if start_justfloat_server(HOST, PORT):
        print("✓ TCP客户端启动成功")

        try:
            # 运行测试循环
            for i in range(60):  # 运行60秒
                time.sleep(1)
              
                # 获取统计信息
                stats = get_justfloat_stats()
                print(f"\r[{i+1:2d}s] 连接: {'✓' if stats['connected'] else '✗'} | "
                      f"数据包: {stats['packets_received']} | "
                      f"字节: {stats['bytes_received']} | "
                      f"错误: {stats['errors']}", end='', flush=True)
                
                # 获取最新数据
                data = get_justfloat_data()
                if data:
                    print(f"\n📊 最新数据: {data['values']}")
                    print(f"   时间戳: {time.strftime('%H:%M:%S', time.localtime(data['timestamp']))}")
                    print(f"   数据量: {data['count']} 个浮点数")
                
                # 每10秒显示一次详细状态
                if (i + 1) % 10 == 0:
                    print(f"\n📈 详细状态:")
                    print(f"   运行时间: {stats['uptime']:.1f}秒")
                    if stats['last_data_time']:
                        last_data_age = time.time() - stats['last_data_time']
                        print(f"   最后数据: {last_data_age:.1f}秒前")
                    else:
                        print(f"   最后数据: 无")
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断测试")
        except Exception as e:
            print(f"\n\n❌ 测试过程中出错: {e}")
        finally:
            # 停止客户端
            stop_justfloat_server()
            print("✓ TCP客户端已停止")
    else:
        print("❌ TCP客户端启动失败")
        print("请检查:")
        print("1. STM32 TCP服务器是否正在运行")
        print("2. IP地址和端口是否正确")
        print("3. 网络连接是否正常")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == '__main__':
    test_justfloat_client()
