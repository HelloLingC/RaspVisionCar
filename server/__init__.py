import server.http_server as http_server
import server.websocket_server as websocket_server
import threading

# 全局变量存储服务器线程
http_thread = None
ws_thread = None

def start_servers():
    """启动HTTP和WebSocket服务器"""
    global http_thread, ws_thread
    
    # 在单独线程中启动HTTP服务器（Flask是阻塞的）
    http_thread = threading.Thread(target=http_server.start_http_server, daemon=False)
    http_thread.start()
    print("HTTP Server started in background thread")

    # 在单独线程中启动WebSocket服务器（asyncio.run是阻塞的）
    ws_thread = threading.Thread(target=websocket_server.start_websocket_server, daemon=False)
    ws_thread.start()
    print("WebSocket Server started in background thread")

def cleanup_servers():
    """清理服务器资源"""
    global http_thread, ws_thread
    
    print("\n正在关闭服务器...")
    
    # 停止HTTP服务器
    try:
        http_server.stop_http_server()
    except Exception as e:
        print(f"关闭HTTP服务器时出错: {e}")
    
    # 停止WebSocket服务器
    try:
        websocket_server.stop_websocket_server()
    except Exception as e:
        print(f"关闭WebSocket服务器时出错: {e}")