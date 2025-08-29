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
    height, width = image.shape[:2]
    # 梯形ROI
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Define trapezoid points  左下 右下 右上 左上
    pts = np.array([[0, height], [width-10, height], [width-50, 200], [100, 200]], np.int32)
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
    frame = cv2.resize(frame, (640, 480))
    # 获取黄色掩膜
    yellow_mask = get_yellow_mask(frame)
    
    # 查找赛道线
    track_line, pts = find_track_line(yellow_mask)
    # 查找轮廓
    edges = cv2.Canny(track_line, 50, 150)
    
    mask = edges != 0
    frame[mask] = [0, 0, 255]

    cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 55), thickness=1)

    # h,w = edges.shape[:2]
    # mid_line = w//2-1
    # cv2.line(frame, (mid_line, 0), (mid_line, h), (0, 255, 255), 1)

    follow,error =mid(frame, edges)
    cv2.putText(frame, f"Turn: {error}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(155,55,0), 2)

    cv2.imshow("Original", frame)
    cv2.imshow("Track Line", yellow_mask)


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
    main()
    # frame = cv2.imread("test/2.jpg")
    # handle_one_frame(frame)
    # cv2.waitKey(0)
    #  cv2.destroyAllWindows()
