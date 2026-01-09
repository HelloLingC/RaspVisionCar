import os

# or 320*240
SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", 640))
SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", 480))

OPENCV_DETECT_ON = int(os.getenv("OPENCV_DETECT_ON", 1))

# 0: Don't Output 1: Output for ControlPanel, 2: Output with cs2.imshow()
FRAME_OUTPUT_METHOD = int(os.getenv("FRAME_OUTPUT_METHOD", 1))
VIDEO_INPUT_PATH = os.getenv("VIDEO_INPUT_PATH", "")

SHOW_TRACKBAR = int(os.getenv("SHOW_TRACKBAR", 0))
ENABLE_TURN_ANGLE_UPDATE = int(os.getenv("ENABLE_TURN_ANGLE_UPDATE", 1))
RECORD_VIDEO = int(os.getenv("RECORD_VIDEO", 0))