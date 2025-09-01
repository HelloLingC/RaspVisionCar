import socket
import subprocess

def get_ip_address():
    ip_address = subprocess.check_output(['hostname', '-I']).decode().split()
    if(not ip_address):
        raise Exception("Unable to determine IP")
    else:
        ip_address = ip_address[0]
    return ip_address

# Server running on Raspberry Pi
def start_server():
    host = '0.0.0.0'
    port = 5000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)

    print(f"Server started on {get_ip_address()}:{port}")

    conn, addr = s.accept()
    print('Connected by', addr)

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            print(data)

            # examine format
            if ',' not in data:
                print(f"Unknown format: {data}")
                continue

            status, angle, speed = data.split(',')
            # control_car(float(angle), float(speed))
            conn.send("OK".encode())

    except Exception as e:
        print(e)
    finally:
        conn.close()