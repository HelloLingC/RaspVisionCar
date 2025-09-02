# Left Motor Module
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# TB6612引脚定义
# 电机1
AIN1 = 17  # 控制电机1方向
AIN2 = 18  # 控制电机1方向
PWMA = 27  # 电机1 PWM速度控制
HALL_LEFT = 5   # 左侧霍尔传感器

# TB6612引脚
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)

# 霍尔传感器引脚
GPIO.setup(HALL_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 创建PWM对象，频率设置为1000Hz
pwm_a = GPIO.PWM(PWMA, 1000)
pwm_a.start(0) # 初始占空比为0

KP = 0.8    # 比例系数
KI = 0.2    # 积分系数
KD = 0.1    # 微分系数

left_pwm = 0          # 左侧当前PWM值
left_rpm = 0          # 左侧当前转速
left_counter = 0      #

# 霍尔传感器中断回调
def hall_left_callback(channel):
    global left_counter
    left_counter += 1
GPIO.add_event_detect(HALL_LEFT, GPIO.FALLING, callback=hall_left_callback, bouncetime=2)

def pwm_to_rpm(pwm):
    """将PWM值转换为RPM值"""
    return pwm * 0.5 + 0.0001

def calculate_rpm():
    """计算电机转速(RPM)"""
    global left_counter, left_rpm
    
    # 每0.5秒计算一次转速
    while True:
        time.sleep(0.5)  # 采样时间
        
        # 计算RPM (假设每个轮子有20个磁极)
        left_rpm = (left_counter / 20) * 60 * 2  # 乘以2是因为采样时间是0.5秒
        
        # 重置计数器
        left_counter = 0
        
        # 打印当前转速
        print(f"Left: {left_rpm:.2f} RPM")

def move(direction, pwm_value):
    """通过pwM控制左侧电机"""
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