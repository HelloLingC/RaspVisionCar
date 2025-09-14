from typing import Dict, Any
from gpio.serial_io import get_stm32_io


class Motor_Controller:
    def __init__(self):
        self.stm32_io = get_stm32_io()

    def move_car(self, speed: int = 50, angle: int = 0) -> Dict[str, Any]:
        """
        控制小车移动

        Args:
            speed: 移动速度 (-100到100)
            angle: 移动角度 (0-360), 0表示直行, 正数表示向右转, 负数表示向左转

        Returns:
            执行结果
        """
        return self.stm32_io.send_command('move', {
            'angle': angle,
            'speed': speed
        })
    
    def set_motor_speed(self, left_speed: int, right_speed: int) -> Dict[str, Any]:
        """
        设置左右电机速度
        
        Args:
            left_speed: 左电机速度 (-100到100)
            right_speed: 右电机速度 (-100到100)
            
        Returns:
            执行结果
        """
        return self.stm32_io.send_command('set_motor_speed', {
            'left_speed': left_speed,
            'right_speed': right_speed
        })
    
    def emergency_stop(self) -> Dict[str, Any]:
        """
        紧急停止
        
        Returns:
            执行结果
        """
        return self.stm32_io.send_command('emergency_stop')
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """
        获取传感器数据
        
        Returns:
            传感器数据
        """
        return self.stm32_io.send_command('get_sensors')