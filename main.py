from dotenv import load_dotenv

from vision import curve_detector, light_detect
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

# SCREEN_WIDTH = 640
# SCREEN_HEIGHT = 480
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

UPTIME_START_WHEN = 0

def nothing(x):
    pass

# HSV 提取黄色赛道线
def get_yellow_mask(hsv):
    
    # 黄色的HSV范围
    if(config.SHOW_TRACKBAR):
        h_lower = cv2.getTrackbarPos("H Lower", "Video Trackbar")
        h_upper = cv2.getTrackbarPos("H Upper", "Video Trackbar")
        s_lower = cv2.getTrackbarPos("S Lower", "Video Trackbar")
        s_upper = cv2.getTrackbarPos("S Upper", "Video Trackbar")
        v_lower = cv2.getTrackbarPos("V Lower", "Video Trackbar")
        v_upper = cv2.getTrackbarPos("V Upper", "Video Trackbar")
        lower_yellow = np.array([h_lower, s_lower, v_lower])
        upper_yellow = np.array([h_upper, s_upper, v_upper])
    else:
        lower_yellow = np.array([10, 40, 120])
        upper_yellow = np.array([40, 255, 255])

    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # kernel = np.ones((5, 5), np.uint8)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 去噪点
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # 填补空洞

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)

    # mask = cv2.medianBlur(mask, 9)  # 中值滤波
    return mask

ROI_TOP_VERT = 100 # 从上往下第 x 行以下为ROI
def get_roi(image: Mat):
    height, width = image.shape[:2]
    # 梯形ROI
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Define trapezoid points  左下 右下 右上 左上
    left_bottom = [0, height]
    right_bottom = [width, height]
    left_top = [0, ROI_TOP_VERT]
    right_top = [width, ROI_TOP_VERT]
    pts = np.array([left_bottom, right_bottom, right_top, left_top], np.int32)
    pts = pts.reshape((-1, 1, 2))

    # Fill the trapezoid area on mask
    cv2.fillPoly(mask, [pts], 255)

    # Apply mask to image
    roi = cv2.bitwise_and(image, image, mask=mask)

    return roi, pts


"""
从图像底部向上扫描（逐行）
找出当前行左右赛道的边缘点 → 取两者中点 → 逐层向上平滑跟踪中线 → 得出最终中线。
"""
def mid(follow: Mat, mask: Mat) -> tuple[Mat, int]:
    mid_points = np.empty((0, 2), int)

    half_width= follow.shape[1] // 2
    half = half_width  # 从下往上扫描赛道,最下端取图片中线为分割线
    scan_times = 0
    invaild_times = 0;
    error = 0
    for y in range(follow.shape[0] - 1, -1, -1):
        have_left_lane = True
        have_right_lane = True
        scan_times += 1
        if scan_times > SCREEN_HEIGHT - ROI_TOP_VERT:
            break
        # 加入分割线左右各半张图片的宽度作为约束,减小邻近赛道的干扰
        if (mask[y][max(0,half-half_width):half] == np.zeros_like(mask[y][max(0,half-half_width):half])).all():
            # 分割线左端无赛道
            have_left_lane = False
            left = max(0,half-half_width)  # 取图片左边界
        else:
            left = np.average(np.where(mask[y][0:half] == 255))  # 计算分割线左端平均位置
        if (mask[y][half:min(follow.shape[1],half+half_width)] == np.zeros_like(mask[y][half:min(follow.shape[1],half+half_width)])).all():
            # 分割线右端无赛道
            have_right_lane = False
            right = min(follow.shape[1],half+half_width)  # 取图片右边界
        else:
            right = np.average(np.where(mask[y][half:follow.shape[1]] == 255)) + half  # 计算分割线右端平均位置

        mid = (left + right) // 2  # 计算拟合中点
        if not have_right_lane and not have_left_lane: # 左右两边都无赛道
            # follow[y, int(mid)] = 0;
            invaild_times += 1
        else:
            error += half_width - int(mid)
            # new_point = np.array([y, int(mid)])
            # mid_points = np.vstack([mid_points, new_point])
            follow[y, int(mid)] = 255  # 画出每行中点轨迹

        half = int(mid)  # 递归,从下往上确定拟合中点
        
    # print(f"invaild: {scan_times - invaild_times}")

    # print(f"{curv} : {direction}")
    return error / (scan_times - invaild_times) # error为正数右转,为负数左转

def handle_one_frame(frame: Mat) -> Mat:
    # BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # 高斯模糊  
    hsv = cv2.GaussianBlur(hsv, (7, 7), 0)

    roi, pts = get_roi(hsv)

    yellow_mask = get_yellow_mask(roi)

    edges = cv2.Canny(yellow_mask, 50, 100)

    mask = edges != 0
    frame[mask] = [0, 0, 255]

    # Draw ROI region
    cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 55), thickness=1)

    error = mid(frame, edges)

    if error > 0:
        direction = "left"
    else:
        direction = "right"
    
    # error = round(error)

    return direction, error

shutdown_flag = threading.Event()

def signal_handler(signum, frame):
    """信号处理器 for Ctrl+C"""
    print("\nReceived exit signal (Ctrl+C), shutting down gracefully...")
    shutdown_flag.set()
    server.cleanup_servers()
    sys.exit(0)

def main():
    if(config.FRAME_OUTPUT_METHOD == 1):
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if not serial_io.init_stm32_io():
            print("STM32 Serial IO initialization failed")
            exit(1)
        print("STM32 Serial IO initialized")
        
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
        out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'MJPG'), actual_fps, (SCREEN_WIDTH, SCREEN_HEIGHT))

    if config.SHOW_TRACKBAR:
        cv2.namedWindow("Video Trackbar", cv2.WINDOW_NORMAL)
        cv2.createTrackbar("H Lower", "Video Trackbar", 10, 179, nothing)
        cv2.createTrackbar("H Upper", "Video Trackbar", 40, 179, nothing)
        cv2.createTrackbar("S Lower", "Video Trackbar", 40, 255, nothing)
        cv2.createTrackbar("S Upper", "Video Trackbar", 255, 255, nothing)
        cv2.createTrackbar("V Lower", "Video Trackbar", 120, 255, nothing)
        cv2.createTrackbar("V Upper", "Video Trackbar", 255, 255, nothing)

    try:
        times = 0;
        while not shutdown_flag.is_set():
            ret, frame = cap.read()
            if not ret:
                break
                    
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))

            redCount, greenCount = light_detect.handle_lights(frame)
            direction, error = handle_one_frame(frame)

            signal_v = -1
            signal_cmd = ""

            if redCount == 0 and greenCount == 0:
                cv2.putText(frame, "lights out", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            elif redCount > greenCount and redCount > 500: # threhold
                signal_v = 0
            elif redCount < greenCount and greenCount > 500:
                signal_v = 1
            else:
                cv2.putText(frame, f"slight {redCount}/{greenCount}", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            if signal_v != -1: 
                # it's vaild, we should send the signal to the Slave
                signal_cmd = f"sig:{signal}"

            command = f"cv:{error},{signal_cmd}\n"
            motor.get_motor_controller().send_command(command)

            if signal_v == 0:
                cv2.putText(frame, f"red light {redCount}/{greenCount}", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
            elif signal_v == 1:
                cv2.putText(frame, f"green light {redCount}/{greenCount}", (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)            
 
            cv2.putText(frame, f"dir: {direction}", (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(155,55,0), 1)
            cv2.putText(frame, f"error: {error}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 30), 1)

            if config.RECORD_VIDEO:
                out.write(frame)

            if(config.FRAME_OUTPUT_METHOD == 1):
                success, jpeg_data = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
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
