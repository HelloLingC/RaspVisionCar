
本项目使用STM32F103单片机，使用Keil5开发。

获取已编译的hex，可直接烧录

https://github.com/HelloLingC/RaspVisionCar-STM32

# 接线

## Motor

### PWM

PA6 TIM3_CH1 ->  Motor PWMA

PA7 TIM3_CH2 ->  Motor PWMB

PC15 - STBY

### Left Motor Driver

PB0 -> AIN1

PB1 -> AIN2

### Right Motor Driver

PA4 -> BIN1

PA5 -> BIN2

## Hall Encoder

### Left Encoder

E1A -> TIM2_CH1 PB6

E1B -> TIM2_CH2 PB7

### Right Encoder

E2A -> TIM4_CH1

E2B -> TIM4_CH2

GND

5V

# Raspberry Pi

PA9  USART_1 TX -> GPIO 15 RX

PA10 USART_1 RX -> GPIO 14 TX


# Lader

LD14 单向输入

PA3 USART_2 RX ->  LD14 TX

# OLED

