import cv2
from cv2.mat_wrapper import Mat
import numpy as np
import light_detect
import config
import server.http_server as server
import threading

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
ROI_TOP_VERT = 230

FRAME_OUTPUT_METHOD = 1 # 0: Don't Output 1: Output for ControlPanel, 2: Output with cs2.imshow() 

UPTIME_START_WHEN = 0

def get_yellow_mask(frame):
    # BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 黄色的HSV范围
    lower_yellow = np.array([10, 40, 120])
    upper_yellow = np.array([40, 255, 255])

    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.medianBlur(mask, 9)  # 中值滤波
    mask = cv2.dilate(mask, dilate_kernel)  # 膨胀
    mask = cv2.erode(mask, erode_kernel)  # 腐蚀
    return mask

def find_track_line(image: Mat):
    height, width = image.shape[:2]
    # 梯形ROI
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Define trapezoid points  左下 右下 右上 左上
    pts = np.array([[0, height], [width-10, height], [width-80, ROI_TOP_VERT], [170, ROI_TOP_VERT]], np.int32)
    pts = pts.reshape((-1, 1, 2))

    # Fill the trapezoid area on mask
    cv2.fillPoly(mask, [pts], 255)

    # Apply mask to image
    roi = cv2.bitwise_and(image, image, mask=mask)

    return roi, pts


def mid(follow, mask):
    halfWidth= follow.shape[1] // 2
    half = halfWidth  # 从下往上扫描赛道,最下端取图片中线为分割线
    for y in range(follow.shape[0] - 1, -1, -1):
        if SCREEN_HEIGHT - y > ROI_TOP_VERT + 20:
            break
        # V2改动:加入分割线左右各半张图片的宽度作为约束,减小邻近赛道的干扰
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
 
        if y == 360:  # 设置指定提取中点的纵轴位置
            mid_output = int(mid)
 
    cv2.circle(follow, (mid_output, 360), 5, 255, -1)  # opencv为(x,y),画出指定提取中点
 
    error = follow.shape[1] // 2 - mid_output  # 计算图片中点与指定提取中点的误差
 
    return follow, error  # error为正数右转,为负数左转


def handle_one_frame(frame: Mat):
    light_detect.handle_lights(frame)

    yellow_mask = get_yellow_mask(frame)

    track_line, pts = find_track_line(yellow_mask)

    edges = cv2.Canny(track_line, 50, 150)

    mask = edges != 0
    frame[mask] = [0, 0, 255]

    cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 55), thickness=1)

    follow,error =mid(frame, edges)
    cv2.putText(frame, f"Turn: {error}", (config.DEBUG_LEFT_MARGIN, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(155,55,0), 2)

    
    if(FRAME_OUTPUT_METHOD == 1):
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 90]
        success, jpeg_data = cv2.imencode('.jpeg', frame)
        if success:
            server.output.write(jpeg_data.tobytes())
    elif(FRAME_OUTPUT_METHOD == 2):
        cv2.imshow("Original", frame)
        cv2.imshow("Track Line", yellow_mask)

def main():
    # 异步启动服务器
    if(FRAME_OUTPUT_METHOD == 1):
        server_thread = threading.Thread(target=server.start_http_server, daemon=True)
        server_thread.start()
        print("Control Server will be runing async")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
    # cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        # cap.set(cv2.CAP_PROP_SATURATION, 3)
    # cap = cv2.VideoCapture("test/1.mp4")
    # cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
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
