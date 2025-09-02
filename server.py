from flask import Flask, Response, request, send_file
import time
import threading
import io
import urllib

app = Flask(__name__)

# Global variable for streaming output
output = None

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()
    
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

@app.route('/')
def index():
    try:
        return send_file("server.html")
    except FileNotFoundError:
        return "HTML file not found", 404

@app.route('/control')
def control():
    command = request.args.get('command', '')
    speed = request.args.get('speed', '50')
    
    # Process your control commands here
    print(f"Command: {command}, Speed: {speed}")
    
    response = Response('OK')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/stream.mjpg')
def stream():
    def generate():
        try:
            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                
                if frame:
                    # Build MJPEG frame
                    yield (b'--FRAME\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' +
                           frame + b'\r\n')
                
                # Add delay to control frame rate if needed
                # time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            print(f"Stream error: {e}")
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=FRAME',
        headers={
            'Age': '0',
            'Cache-Control': 'no-cache, private',
            'Pragma': 'no-cache'
        }
    )

def start_server():
    global output
    output = StreamingOutput()
    
    print('Control Server started running on port 8080')
    app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == '__main__':
    start_server()