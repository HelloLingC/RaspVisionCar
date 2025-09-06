#!/usr/bin/env python3
"""
启动脚本 - 同时运行 HTTP 服务器和 WebSocket 服务器
"""

import threading
import time
import sys
import os

# 添加 server 目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def start_http_server():
    """启动 HTTP 服务器"""
    try:
        from server.http_server import start_http_server
        print("正在启动 HTTP 服务器...")
        start_http_server(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"HTTP 服务器启动失败: {e}")

def start_websocket_server():
    """启动 WebSocket 服务器"""
    try:
        from server.websocket_server import start_websocket_server
        print("正在启动 WebSocket 服务器...")
        start_websocket_server(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"WebSocket 服务器启动失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("VisionCar 服务器启动器")
    print("=" * 50)
    print("HTTP 服务器: http://localhost:8080")
    print("WebSocket 服务器: ws://localhost:5000")
    print("=" * 50)
    
    # 创建线程
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    
    try:
        # 启动线程
        http_thread.start()
        time.sleep(1)  # 等待 HTTP 服务器启动
        
        websocket_thread.start()
        time.sleep(1)  # 等待 WebSocket 服务器启动
        
        print("\n✅ 两个服务器都已启动!")
        print("📱 访问 http://localhost:8080 使用控制面板")
        print("🔌 WebSocket 连接: ws://localhost:5000")
        print("\n按 Ctrl+C 停止服务器...")
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务器...")
        print("✅ 服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动过程中发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
