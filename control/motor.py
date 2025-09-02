import motor_left
from enum import Enum

class Status(Enum):
    MOVING = 1
    STOPPED = 2

MOTOR_STATUS = Status.STOPPED

def move(direction, speed):
    """移动电机"""
    motor_left.move(direction, 1000)

def loop():
    """PID速度环"""
    global left_pwm, right_pwm
    
    while (MOTOR_STATUS != Status.STOPPED):
        # 计算左侧电机PID
        # left_pwm = compute_pid(left_rpm, target_rpm, left_errors)
        
        # 计算右侧电机PID
        # right_pwm = compute_pid(right_rpm, target_rpm, right_errors)
        
        # 应用PWM值
        motor_left.move("forward", left_pwm)
        # motor_right_control("forward", right_pwm)

        # time.sleep(0.1)  # PID控制周期