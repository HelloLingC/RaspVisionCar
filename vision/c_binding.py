import cv2
import numpy as np
import cpp_processor # 导入你编译好的C++模块！

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 直接将numpy数组（即OpenCV图像）传递给C++函数！
    # 几乎没有开销
    result_image = cpp_processor.process_image(frame)

    # 现在result_image就是一个numpy数组，可以直接用OpenCV显示
    cv2.imshow('Processed by C++', result_image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()