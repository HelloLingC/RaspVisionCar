from dotenv import load_dotenv

from vision import curve_detector, light_detect2, light_detect, track_line
load_dotenv()  # 必须在所有导入之前加载 .env 文件

import cv2
from cv2.mat_wrapper import Mat
import numpy as np
import server as server
import asyncio
import threading
import signal
import sys
import serial_pi.serial_io as serial_io
import serial_pi.motor as motor
import config

UPTIME_START_WHEN = 0

def nothing(x):
    pass

shutdown_flag = threading.Event()

def signal_handler(signum, frame):
    """信号处理器 for Ctrl+C"""
    print("\nReceived exit signal (Ctrl+C), shutting down gracefully...")
    shutdown_flag.set()
    server.cleanup_servers()
    sys.exit(0)

def main():
    if(config.FRAME_OUTPUT_METHOD == 0 or config.FRAME_OUTPUT_METHOD == 1):
        if not serial_io.init_stm32_io():
            print("STM32 Serial IO initialization failed")
            exit(1)
        print("STM32 Serial IO initialized")
    if(config.FRAME_OUTPUT_METHOD == 1):
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动服务器
        server.start_servers()
    
    cap = cv2.VideoCapture(0)
    # cap = cv2.VideoCapture("/Users/lingc/Documents/output1.avi")
    # cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
    # cap.set(cv2.CAP_PROP_CONTRAST, 0.6)
    # cap.set(cv2.CAP_PROP_SATURATION, 3)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Camera actual FPS: {actual_fps}")

    if config.RECORD_VIDEO:
        out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'MJPG'), actual_fps, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    if config.SHOW_TRACKBAR:
        cv2.namedWindow("Video Trackbar", cv2.WINDOW_NORMAL)
        cv2.createTrackbar("H Lower", "Video Trackbar", 10, 179, nothing)
        cv2.createTrackbar("H Upper", "Video Trackbar", 40, 179, nothing)
        cv2.createTrackbar("S Lower", "Video Trackbar", 40, 255, nothing)
        cv2.createTrackbar("S Upper", "Video Trackbar", 255, 255, nothing)
        cv2.createTrackbar("V Lower", "Video Trackbar", 120, 255, nothing)
        cv2.createTrackbar("V Upper", "Video Trackbar", 255, 255, nothing)

    try:
        while not shutdown_flag.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            r_frame = cv2.resize(frame, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

            if config.OPENCV_DETECT_ON:
                direction, error = track_line.handle_one_frame(r_frame, config.SCREEN_HEIGHT)

                redCount, greenCount = light_detect.handle_lights(frame)

                signal_v, signal_cmd = light_detect.process_signal(frame, redCount, greenCount)

                  # if signal_v == 0:
                #     cv2.putText(frame, f"red light {redCount}/{greenCount}", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                # elif signal_v == 1:
                #     cv2.putText(frame, f"green light {redCount}/{greenCount}", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)            

                command = f"cv:{error},{signal_cmd}\n"
                motor.get_motor_controller().send_command(command)

                cv2.putText(frame, f"dir: {direction}", (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(155,55,0), 1)
                cv2.putText(frame, f"error: {error}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 30), 1)

            if config.RECORD_VIDEO:
                out.write(frame)

            if(config.FRAME_OUTPUT_METHOD == 1):
                success, jpeg_data = cv2.imencode('.jpeg', r_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                if success:
                    server.http_server.output.write(jpeg_data.tobytes())
            elif(config.FRAME_OUTPUT_METHOD == 2):
                cv2.imshow("Original", frame)
                # cv2.imshow("Track Line", yellow_mask)

            # 按'q'退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # 清理资源
        cap.release()
        cv2.destroyAllWindows()

        # 关闭服务器
        server.cleanup_servers()

if __name__ == "__main__":
    main()
