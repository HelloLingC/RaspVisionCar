from typing import Dict, Any
import time
import config
from serial_pi.serial_io import get_stm32_io

class Motor_Controller:

    def send_turn_angle(self, angle: int):
        try:
            # 限速：两次发送之间至少间隔 50ms
            # min_interval_seconds = 0.05
            # last_ts = getattr(self, "_last_turn_send_ts", 0.0)
            # now = time.monotonic()
            # delta = now - last_ts
            # if delta < min_interval_seconds:
            #     time.sleep(min_interval_seconds - delta)

            # # 记录发送时间戳
            # self._last_turn_send_ts = time.monotonic()
            if(config.ENABLE_TURN_ANGLE_UPDATE):
                return get_stm32_io().send_command(f'cv:{angle}\n')
            else:
                pass
                # print(f"Turn angle update is disabled, angle: {angle}")
        except Exception as e:
            # print(f"发送转向角度失败: {e}")
            print(f"Send turn angle failed: {e}")

    def set_motor_speed(self, left_speed: int, right_speed: int) -> Dict[str, Any]:
        """
        设置左右电机速度
        
        Args:
            left_speed: 左电机速度 (-100到100)
            right_speed: 右电机速度 (-100到100)
            
        Returns:
            执行结果
        """
        stm32_io = get_stm32_io()
        if stm32_io:
            return stm32_io.send_command(f'LS:{left_speed},RS:{right_speed}\n')
        return None
    
    def set_pid_params(self, direction: str, kp: float, ki: float, kd: float):
        stm32_io = get_stm32_io()
        if stm32_io:
            return stm32_io.send_command(f'PID:{direction}:{kp}:{ki}:{kd}\n')
        return None


motor_controller = Motor_Controller()

def get_motor_controller() -> Motor_Controller:
    return motor_controller