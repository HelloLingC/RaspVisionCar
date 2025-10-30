from typing import Dict, Any
from serial_pi.serial_io import get_stm32_io


class Motor_Controller:
    def __init__(self):
        self.stm32_io = get_stm32_io()

    def set_motor_speed(self, left_speed: int, right_speed: int) -> Dict[str, Any]:
        """
        设置左右电机速度
        
        Args:
            left_speed: 左电机速度 (-100到100)
            right_speed: 右电机速度 (-100到100)
            
        Returns:
            执行结果
        """
        return self.stm32_io.send_command(f'LS:{left_speed},RS:{right_speed}')
    
    def set_pid_params(self, direction: str, kp: float, ki: float, kd: float):
        self.stm32_io.send_command(f'PID:{direction}:{kp}:{ki}:{kd}')
        