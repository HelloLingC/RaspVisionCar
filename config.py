import os

# 0: Don't Output 1: Output for ControlPanel, 2: Output with cs2.imshow() 
FRAME_OUTPUT_METHOD = int(os.getenv("FRAME_OUTPUT_METHOD", 1))
VIDEO_INPUT_PATH = os.getenv("VIDEO_INPUT_PATH", "")

SHOW_TRACKBAR = int(os.getenv("SHOW_TRACKBAR", 0))
ENABLE_TURN_ANGLE_UPDATE = int(os.getenv("ENABLE_TURN_ANGLE_UPDATE", 0))
RECORD_VIDEO = int(os.getenv("RECORD_VIDEO", 0))