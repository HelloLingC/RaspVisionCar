import server.http_server as http_server
import server.websocket_server as websocket_server

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