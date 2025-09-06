
本项目使用STM32F103单片机，使用Keil5开发。

获取已编译的hex，可直接烧录

https://github.com/HelloLingC/RaspVisionCar-STM32

# 接线

## Motor

### Engine

PA6 TIM3_CH1 ->  Motor PWMA
PA7 TIM3_CH2 ->  Motor PWMB

STBY ->

PB0 -> AIN1

PB1 -> AIN2

PA4 -> BIN1

PA5 -> BIN2

### Hall Encoder

E2B TIM2

E2A

E1B

E1A TIM4

GND

5V

# Raspberry Pi

PA9  USART_1 TX -> GPIO

PA10 USART_1 RX -> GPIO


# Lader

LD14 单向输入

PA3 USART_2 RX ->  LD14 TX

# OLED

