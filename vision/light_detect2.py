import numpy as np
import cv2

def handle(frame, hsv):
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    circles = cv2.HoughCircles(
        mask, 
        cv2.HOUGH_GRADIENT, 
        dp=1, 
        minDist=10,
        param1=30, 
        param2=10,   # param2 越小越容易检测到小圆
        minRadius=10, 
        maxRadius=30
    )
    # if circles is not None:
    #     circles = np.uint16(np.around(circles))
    #     for (x, y, r) in circles[0, :]:
    #         cv2.circle(frame, (x, y), r, (0, 255, 0), 2)

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            # 圆形
            cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
            # 圆心
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
            # print(f"圆: 中心({x}, {y}), 半径{r}")