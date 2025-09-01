import socket

class CarClient():
    def __init__(self, pi_ip, port=5000):
        self.pi_ip = pi_ip
        self.port = port

    def send(self, msg):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.pi_ip, self.port))
            
            command = msg
            client_socket.send(command.encode())
            
            response = client_socket.recv(1024).decode()
            print(f"Response: {response}")
            
            client_socket.close()
            return True
            
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
        finally:
            client_socket.close()
    
    def send_command(self, status, angle, speed):
        self.send(f"{status},{angle},{speed}")