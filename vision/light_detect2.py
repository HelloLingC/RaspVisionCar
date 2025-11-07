import numpy as np
import cv2

def handle():
    lower_green = np.array([40, 60, 60])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)