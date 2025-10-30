import cv2
import numpy as np

# Global variables
isFirstDetectedR = True
isFirstDetectedG = True
lastTrackBoxR = None
lastTrackBoxG = None
lastTrackNumR = 0
lastTrackNumG = 0

def isIntersected(r1, r2):
    """
    确定两个矩形区域是否相交
    """
    minX = max(r1[0], r2[0])
    minY = max(r1[1], r2[1])
    maxX = min(r1[0] + r1[2], r2[0] + r2[2])
    maxY = min(r1[1] + r1[3], r2[1] + r2[3])
    
    if minX < maxX and minY < maxY:
        return True
    else:
        return False

def processImgR(src, frame):
    """
    处理红色图像
    """
    global isFirstDetectedR, lastTrackBoxR, lastTrackNumR
    
    tmp = src.copy()
    contours, hierarchy = cv2.findContours(tmp, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    result = None
    resultNum = 0
    area = 0
    
    if len(contours) > 0:
        trackBox = [None] * len(contours)
        result = [None] * len(contours)
        
        # 确定要跟踪的区域
        for i in range(len(contours)):
            # 获取凸包的点集
            hull = cv2.convexHull(contours[i])
            # 获取边界矩形
            x, y, w, h = cv2.boundingRect(hull)
            trackBox[i] = (x, y, w, h)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, f"Red: {w}x{h}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        if isFirstDetectedR:
            lastTrackBoxR = trackBox.copy()
            lastTrackNumR = len(contours)
            isFirstDetectedR = False
        else:
            for i in range(len(contours)):
                for j in range(lastTrackNumR):
                    if isIntersected(trackBox[i], lastTrackBoxR[j]):
                        result[resultNum] = trackBox[i]
                        resultNum += 1
                        break
            
            lastTrackBoxR = trackBox.copy()
            lastTrackNumR = len(contours)
    else:
        isFirstDetectedR = True
        result = None
    
    if result is not None:
        for i in range(resultNum):
            if result[i] is not None:
                area += result[i][2] * result[i][3]  # width * height
    
    return area

def processImgG(src, frame):
    """
    处理绿色图像
    """
    global isFirstDetectedG, lastTrackBoxG, lastTrackNumG
    
    tmp = src.copy()
    contours, hierarchy = cv2.findContours(tmp, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    result = None
    resultNum = 0
    area = 0
    
    if len(contours) > 0:
        trackBox = [None] * len(contours)
        result = [None] * len(contours)
        
        # 确定要跟踪的区域
        for i in range(len(contours)):
            # 获取凸包的点集
            hull = cv2.convexHull(contours[i])
            # 获取边界矩形
            x, y, w, h = cv2.boundingRect(hull)
            trackBox[i] = (x, y, w, h)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Green: {w}x{h}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        if isFirstDetectedG:
            lastTrackBoxG = trackBox.copy()
            lastTrackNumG = len(contours)
            isFirstDetectedG = False
        else:
            for i in range(len(contours)):
                for j in range(lastTrackNumG):
                    if isIntersected(trackBox[i], lastTrackBoxG[j]):
                        result[resultNum] = trackBox[i]
                        resultNum += 1
                        break
            
            lastTrackBoxG = trackBox.copy()
            lastTrackNumG = len(contours)
    else:
        isFirstDetectedG = True
        result = None
    
    if result is not None:
        for i in range(resultNum):
            if result[i] is not None:
                area += result[i][2] * result[i][3]  # width * height
    
    return area

def handle_lights(frame: cv2.Mat):
    global isFirstDetectedR, isFirstDetectedG, lastTrackBoxR, lastTrackBoxG, lastTrackNumR, lastTrackNumG
    
    redCount = 0
    greenCount = 0

    # 亮度参数
    a = 0.3
    b = (1 - a) * 125

    # 导入视频的路径
    capture = cv2.VideoCapture("test/lights.mp4")
    if not capture.isOpened():
        print("Start device failed!\n")
        return -1

            
    # 调整亮度
    img = frame.copy()
    img = img.astype(np.float32)
    img = a * img + b
    img = np.clip(img, 0, 255).astype(np.uint8)

    # 转换为YCrCb颜色空间
    imgYCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)

    imgRed = np.zeros((imgYCrCb.shape[0], imgYCrCb.shape[1]), dtype=np.uint8)
    imgGreen = np.zeros((imgYCrCb.shape[0], imgYCrCb.shape[1]), dtype=np.uint8)

    # 分解YCrCb的三个成分
    planes = cv2.split(imgYCrCb)
    
    # 根据Cr分量拆分红色和绿色
    Cr_channel = planes[1]
    
    # RED, 145<Cr<470 红色
    imgRed[(Cr_channel > 145) & (Cr_channel < 470)] = 255
    
    # GREEN 95<Cr<110 绿色
    imgGreen[(Cr_channel > 95) & (Cr_channel < 110)] = 255

    # 膨胀和腐蚀
    kernel = np.ones((15, 15), np.uint8)
    imgRed = cv2.dilate(imgRed, kernel, iterations=1)
    imgRed = cv2.erode(imgRed, np.ones((1, 1), np.uint8), iterations=1)
    imgGreen = cv2.dilate(imgGreen, kernel, iterations=1)
    imgGreen = cv2.erode(imgGreen, np.ones((1, 1), np.uint8), iterations=1)

    redCount = processImgR(imgRed, frame)
    greenCount = processImgG(imgGreen, frame)

    if redCount == 0 and greenCount == 0:
        cv2.putText(frame, "lights out", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    elif redCount > greenCount and redCount > 500: # threhold
        cv2.putText(frame, f"red light {redCount}/{greenCount}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    elif redCount < greenCount and greenCount > 500:
        cv2.putText(frame, f"green light {redCount}/{greenCount}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    else:
        cv2.putText(frame, f"slight {redCount}/{greenCount}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

if __name__ == "__main__":
    pass