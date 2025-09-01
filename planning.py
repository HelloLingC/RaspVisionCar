import RPi.GPIO as GPIO
import time
import threading
from collections import deque

# 设置GPIO模式
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# TB6612引脚定义
# 电机1
AIN1 = 17  # 控制电机1方向
AIN2 = 18  # 控制电机1方向
PWMA = 27  # 电机1 PWM速度控制

# 电机2
BIN1 = 22  # 控制电机2方向
BIN2 = 23  # 控制电机2方向
PWMB = 24  # 电机2 PWM速度控制

# 霍尔传感器引脚
HALL_LEFT = 5   # 左侧霍尔传感器
HALL_RIGHT = 6  # 右侧霍尔传感器

# 设置TB6612控制引脚
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)

# 设置霍尔传感器引脚
GPIO.setup(HALL_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(HALL_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 创建PWM对象，频率设置为1000Hz
pwm_a = GPIO.PWM(PWMA, 1000)
pwm_b = GPIO.PWM(PWMB, 1000)
pwm_a.start(0)
pwm_b.start(0)

# PID参数
KP = 0.8    # 比例系数
KI = 0.2    # 积分系数
KD = 0.1    # 微分系数

# 全局变量
left_counter = 0      # 左侧霍尔计数器
right_counter = 0     # 右侧霍尔计数器
left_rpm = 0          # 左侧转速
right_rpm = 0         # 右侧转速
target_rpm = 50       # 目标转速
left_pwm = 0          # 左侧当前PWM值
right_pwm = 0         # 右侧当前PWM值
left_errors = deque(maxlen=10)  # 存储左侧误差用于积分和微分计算
right_errors = deque(maxlen=10) # 存储右侧误差用于积分和微分计算

# 霍尔传感器中断回调函数
def hall_left_callback(channel):
    global left_counter
    left_counter += 1

def hall_right_callback(channel):
    global right_counter
    right_counter += 1

# 添加中断检测
GPIO.add_event_detect(HALL_LEFT, GPIO.FALLING, callback=hall_left_callback, bouncetime=2)
GPIO.add_event_detect(HALL_RIGHT, GPIO.FALLING, callback=hall_right_callback, bouncetime=2)

# 电机控制函数
def motor_left_control(direction, pwm_value):
    """控制左侧电机"""
    if direction == "forward":
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
    elif direction == "stop":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW)
    
    pwm_a.ChangeDutyCycle(pwm_value)

def motor_right_control(direction, pwm_value):
    """控制右侧电机"""
    if direction == "forward":
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
    elif direction == "stop":
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.LOW)
    
    pwm_b.ChangeDutyCycle(pwm_value)

# PID计算函数
def compute_pid(current_rpm, target_rpm, errors):
    """计算PID输出"""
    error = target_rpm - current_rpm
    errors.append(error)
    
    # 比例项
    p_term = KP * error
    
    # 积分项
    i_term = KI * sum(errors)
    
    # 微分项
    if len(errors) > 1:
        d_term = KD * (errors[-1] - errors[-2])
    else:
        d_term = 0
    
    # PID总和
    output = p_term + i_term + d_term
    
    # 限制输出在0-100范围内
    output = max(0, min(100, output))
    
    return output

# 转速计算函数
def calculate_rpm():
    """计算电机转速(RPM)"""
    global left_counter, right_counter, left_rpm, right_rpm
    
    # 每0.5秒计算一次转速
    while True:
        time.sleep(0.5)  # 采样时间
        
        # 计算RPM (假设每个轮子有20个磁极)
        left_rpm = (left_counter / 20) * 60 * 2  # 乘以2是因为采样时间是0.5秒
        right_rpm = (right_counter / 20) * 60 * 2
        
        # 重置计数器
        left_counter = 0
        right_counter = 0
        
        # 打印当前转速
        print(f"Left: {left_rpm:.2f} RPM, Right: {right_rpm:.2f} RPM")

# PID控制线程
def pid_control():
    """PID控制循环"""
    global left_pwm, right_pwm
    
    while True:
        # 计算左侧电机PID
        left_pwm = compute_pid(left_rpm, target_rpm, left_errors)
        
        # 计算右侧电机PID
        right_pwm = compute_pid(right_rpm, target_rpm, right_errors)
        
        # 应用PWM值
        motor_left_control("forward", left_pwm)
        motor_right_control("forward", right_pwm)
        
        time.sleep(0.1)  # PID控制周期

# 主函数
def main():
    try:
        # 启动转速计算线程
        rpm_thread = threading.Thread(target=calculate_rpm)
        rpm_thread.daemon = True
        rpm_thread.start()
        
        # 启动PID控制线程
        pid_thread = threading.Thread(target=pid_control)
        pid_thread.daemon = True
        pid_thread.start()
        
        print("智能小车PID控制已启动，目标转速: {} RPM".format(target_rpm))
        print("按Ctrl+C停止程序")
        
        # 主循环
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Keyboard interrupt, stopping...")
    finally:
        # 清理GPIO设置
        motor_left_control("stop", 0)
        motor_right_control("stop", 0)
        pwm_a.stop()
        pwm_b.stop()
        GPIO.cleanup()
        print("OK, GPIO cleared up")

if __name__ == "__main__":
    main()