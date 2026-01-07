import cv2
import numpy as np
from cv2.mat_wrapper import Mat
import config

# ROI 从上往下第 x 行以下为ROI
ROI_TOP_VERT = 100

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
        upper_yellow = np.array([38, 255, 255])

    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # kernel = np.ones((5, 5), np.uint8)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 去噪点
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # 填补空洞

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)

    # mask = cv2.medianBlur(mask, 9)  # 中值滤波
    return mask

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
def mid(follow: Mat, mask: Mat, screen_height: int) -> tuple[Mat, int]:
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
        if scan_times > screen_height - ROI_TOP_VERT:
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

def handle_one_frame(frame: Mat, screen_height: int) -> Mat:
    # BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # 高斯模糊  
    hsv = cv2.GaussianBlur(hsv, (7, 7), 0)

    # light_detect2.handle(frame, hsv)

    roi, pts = get_roi(hsv)

    yellow_mask = get_yellow_mask(roi)

    edges = cv2.Canny(yellow_mask, 50, 100)

    mask = edges != 0
    frame[mask] = [0, 0, 255]

    # Draw ROI region
    cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 55), thickness=1)

    error = mid(frame, edges, screen_height)

    if error > 0:
        direction = "left"
    else:
        direction = "right"
    
    # error = round(error)

    return direction, error

