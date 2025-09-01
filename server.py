from http import server
import cv2
import time
import threading
import io
import urllib

html = """
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()
    
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class ServerHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            content = html.encode()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/control':
            self.handle_control_request()
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            
            try:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame

                    # 构建MJPEG帧
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                    
                    # 添加短暂延迟以控制帧率
                    # time.sleep(0.033)  # 约30 FPS
                    
            except Exception as e:
                print(f"Stream error: {e}")
            finally:
                if 'cap' in locals():
                    cap.release()

    def handle_control_request(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        command = query_params.get('command', [''])[0]
        speed = query_params.get('speed', ['50'])[0]

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'OK')


class Server(server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True 

def start_server():
    global html
    with open("server.html", encoding="utf-8") as f:
        html = f.read()
    print('Control Server started running on port 8080')
    server = Server(('0.0.0.0', 8080), ServerHandler)
    server.serve_forever()

output = StreamingOutput()

if __name__ == '__main__':
    start_server()