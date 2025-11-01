import cv2
from cv2.mat_wrapper import Mat
import numpy as np
import config
import server.http_server as server
import threading
import serial_pi.serial_io as serial_io
import serial_pi.motor as motor

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
ROI_TOP_VERT = 380

UPTIME_START_WHEN = 0

def nothing(x):
    pass

def get_yellow_mask(frame):
    frame = cv2.GaussianBlur(frame, (7, 7), 0)

    # BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
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

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 去噪点
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # 填补空洞
    # mask = cv2.medianBlur(mask, 9)  # 中值滤波
    return mask

def get_roi(image: Mat):
    height, width = image.shape[:2]
    # 梯形ROI
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Define trapezoid points  左下 右下 右上 左上
    pts = np.array([[0, height], [width-10, height], [width-80, 30], [120, 30]], np.int32)
    pts = pts.reshape((-1, 1, 2))

    # Fill the trapezoid area on mask
    cv2.fillPoly(mask, [pts], 255)

    # Apply mask to image
    roi = cv2.bitwise_and(image, image, mask=mask)

    return roi, pts


def mid(follow: Mat, mask: Mat) -> tuple[Mat, int]:
    halfWidth= follow.shape[1] // 2
    half = halfWidth  # 从下往上扫描赛道,最下端取图片中线为分割线
    for y in range(follow.shape[0] - 1, -1, -1):
        if SCREEN_HEIGHT - y > ROI_TOP_VERT:
            break
        # 加入分割线左右各半张图片的宽度作为约束,减小邻近赛道的干扰
        if (mask[y][max(0,half-halfWidth):half] == np.zeros_like(mask[y][max(0,half-halfWidth):half])).all():  # 分割线左端无赛道
            left = max(0,half-halfWidth)  # 取图片左边界
        else:
            left = np.average(np.where(mask[y][0:half] == 255))  # 计算分割线左端平均位置
        if (mask[y][half:min(follow.shape[1],half+halfWidth)] == np.zeros_like(mask[y][half:min(follow.shape[1],half+halfWidth)])).all():  # 分割线右端无赛道
            right = min(follow.shape[1],half+halfWidth)  # 取图片右边界
        else:
            right = np.average(np.where(mask[y][half:follow.shape[1]] == 255)) + half  # 计算分割线右端平均位置
 
        mid = (left + right) // 2  # 计算拟合中点
        half = int(mid)  # 递归,从下往上确定分割线
        follow[y, int(mid)] = 255  # 画出拟合中线

        # print(f"y: {y}, mid: {mid}")
 
        if y == 290:  # 设置指定提取中点的纵轴位置
            mid_output = int(mid)
 
    cv2.circle(follow, (mid_output, 290), 5, 255, -1)  # opencv为(x,y),画出指定提取中点
 
    error = follow.shape[1] // 2 - mid_output  # 计算图片中点与指定提取中点的误差
 
    return follow, error  # error为正数右转,为负数左转

# def mid(frame: Mat, edges: Mat) -> tuple[Mat, int]:
#     height, width = edges.shape[:2]

#     # 选取底部某一水平线
#     scan_y = int(height * 0.75)

#     # 提取该行的边缘像素（非零即检测到线）
#     scan_line = edges[scan_y, :]

#     # 找出所有非零点的 x 坐标
#     white_x = np.where(scan_line > 0)[0]

#     if len(white_x) < 2:
#         # 检测不到左右两条线，返回原图和 0 偏差
#         return frame, 0

#     # 左右两条线的最左最右点
#     left_x = white_x[0]
#     right_x = white_x[-1]

#     # 计算赛道中点
#     mid_x = (left_x + right_x) // 2

#     # 图像中心
#     center_x = width // 2

#     # 计算偏差（右偏为正，左偏为负）
#     error = mid_x - center_x

#     # --- 可视化部分 ---
#     # 画出扫描线
#     cv2.line(frame, (0, scan_y), (width, scan_y), (255, 255, 0), 1)
#     # 左右线
#     cv2.line(frame, (left_x, scan_y-5), (left_x, scan_y+5), (0, 255, 0), 3)
#     cv2.line(frame, (right_x, scan_y-5), (right_x, scan_y+5), (0, 255, 0), 3)
#     # 中点
#     cv2.circle(frame, (mid_x, scan_y), 5, (0, 0, 255), -1)
#     # 中心线h
#     cv2.line(frame, (center_x, 0), (center_x, height), (255, 0, 0), 1)

#     return frame, error



def handle_one_frame(frame: Mat):
    # TODO: Add light detection
    # light_detect.handle_lights(frame)

    roi, pts = get_roi(frame)
    roi = cv2.GaussianBlur(roi, (5, 5), 0)

    yellow_mask = get_yellow_mask(roi)

    edges = cv2.Canny(yellow_mask, 50, 150)
    # lines = cv2.HoughLinesP(
    #     edges,
    #     rho=1,
    #     theta=np.pi/180,
    #     threshold=20,
    #     minLineLength=15,
    #     maxLineGap=25
    # )

    # if lines is not None:
    #     for line in lines:
    #         x1, y1, x2, y2 = line[0]
    #         cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)


    mask = edges != 0
    frame[mask] = [0, 0, 255]

    # Draw ROI region
    cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 55), thickness=1)

    follow, error = mid(frame, edges)
    cv2.putText(frame, f"Turn: {error}", (config.DEBUG_LEFT_MARGIN, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(155,55,0), 2)

    motor.get_motor_controller().send_turn_angle(error)

    if(config.FRAME_OUTPUT_METHOD == 1):
        success, jpeg_data = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if success:
            server.output.write(jpeg_data.tobytes())
    elif(config.FRAME_OUTPUT_METHOD == 2):
        cv2.imshow("Original", frame)
        cv2.imshow("Track Line", yellow_mask)

def main():
    # 异步启动服务器
    if(config.FRAME_OUTPUT_METHOD == 1):
        if not serial_io.init_stm32_io():
            print("STM32 Serial IO initialization failed")
            exit(1)
        print("STM32 Serial IO initialized")

        server_thread = threading.Thread(target=server.start_http_server, daemon=True)
        server_thread.start()
        print("Console Server will be running asynchronously")

    cap = cv2.VideoCapture(0)
    # cap = cv2.VideoCapture("test/1.mp4")
    # cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
    # cap.set(cv2.CAP_PROP_CONTRAST, 0.6)
    # cap.set(cv2.CAP_PROP_SATURATION, 3)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Camera actual FPS: {actual_fps}")
    cap.set(cv2.CAP_PROP_FPS, 30)

    if config.SHOW_TRACKBAR:
        cv2.namedWindow("Video Trackbar", cv2.WINDOW_NORMAL)
        cv2.createTrackbar("H Lower", "Video Trackbar", 10, 179, nothing)
        cv2.createTrackbar("H Upper", "Video Trackbar", 40, 179, nothing)
        cv2.createTrackbar("S Lower", "Video Trackbar", 40, 255, nothing)
        cv2.createTrackbar("S Upper", "Video Trackbar", 255, 255, nothing)
        cv2.createTrackbar("V Lower", "Video Trackbar", 120, 255, nothing)
        cv2.createTrackbar("V Upper", "Video Trackbar", 255, 255, nothing)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (640, 480))

        handle_one_frame(frame)

        # 按'q'退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
