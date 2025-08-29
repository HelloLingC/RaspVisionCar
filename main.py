import cv2
from cv2.mat_wrapper import Mat
import numpy as np

def get_yellow_mask(frame):
    # 转换到HSV颜色空间
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 定义黄色的HSV范围
    lower_yellow = np.array([10, 40, 120])
    upper_yellow = np.array([40, 255, 255])
    
    # 创建黄色掩膜
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.medianBlur(mask, 9)  # 中值滤波
    mask = cv2.dilate(mask, dilate_kernel)  # 膨胀
    mask = cv2.erode(mask, erode_kernel)  # 腐蚀
    
    return mask

def find_track_line(image: Mat):
    # ROI
    # height, width = image.shape[:2]
    # # 梯形ROI
    # mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # # Define trapezoid points  左下 右下 右上 左上
    # pts = np.array([[50, height], [width-10, height], [width-50, 200], [50, 200]], np.int32)
    # pts = pts.reshape((-1, 1, 2))

    # # Fill the trapezoid area on mask
    # cv2.fillPoly(mask, [pts], 255)

    # # Apply mask to image
    # roi = cv2.bitwise_and(image, image, mask=mask)
    roi = image
    
    return roi

def handle_one_frame(frame: Mat):
    frame = cv2.resize(frame, (640, 480))
    # 获取黄色掩膜
    yellow_mask = get_yellow_mask(frame)
    
    # 查找赛道线
    track_line = find_track_line(yellow_mask)
    # 查找轮廓
    edges = cv2.Canny(track_line, 50, 150)
    
    # mask = edges != 0
    # frame[mask] = [0, 0, 255]

    h,w = edges.shape[:2]
    mid_line = w//2-1
    print(f"Mid line of screen: {mid_line}")
    cv2.line(frame, (mid_line, 0), (mid_line, h), (0, 0, 255), 1)

    left_boundary_points = []
    right_boundary_points = []
    for y in range(h-1, -1, -1): # 从height-1到0，步长为-1
        row = edges[y,:]
        l_inner = -1
        r_inner = -1
        for x in range(0, w//2-1): # Left-half
            if(row[x] == 255):
               l_inner = x
        for x in range(w//2, w-1): # Right-half
            if(row[x] == 255):
                r_inner = x
                break # if find r in first time, jump out
        if l_inner != -1:
            point = (l_inner, y)
        else: # No left boundary
            point = (0, y)
        cv2.circle(frame, point, 2, (0, 255, 0), -1)  # 绿色点表示左边界
        left_boundary_points.append(point)
        
        if r_inner != -1:
            cv2.circle(frame, (r_inner, y), 2, (255, 0, 0), -1)  # 蓝色点表示右边界
            right_boundary_points.append((r_inner, y))

    
    # 显示结果
    cv2.imshow("Original", frame)
    cv2.imshow("Track Line", track_line)


def main():
    # cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
    # cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
    cap = cv2.VideoCapture("test/1.mp4")
    # cap.set(cv2.CAP_PROP_SATURATION, 3)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 处理当前帧
        handle_one_frame(frame)
        
        # 按'q'退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # main() 
    frame = cv2.imread("test/2.jpg")
    handle_one_frame(frame)
    cv2.waitKey(0)
    #  cv2.destroyAllWindows()
