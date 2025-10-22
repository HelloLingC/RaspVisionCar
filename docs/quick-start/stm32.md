
# STM32 快速开始指南

本项目使用 STM32F103 单片机，使用 Keil5 开发。

## 获取固件

获取已编译的 hex 文件，可直接烧录：

[RaspVisionCar-STM32](https://github.com/HelloLingC/RaspVisionCar-STM32)

## 接线说明

### 电机驱动 (Motor)

#### PWM 信号

| STM32 引脚 | 功能 | 连接目标 |
|-----------|------|----------|
| PA6 | TIM3_CH1 | Motor PWMA |
| PA7 | TIM3_CH2 | Motor PWMB |
| PC15 | - | STBY |

#### 左电机驱动

| STM32 引脚 | 连接目标 |
|-----------|----------|
| PB0 | AIN1 |
| PB1 | AIN2 |

#### 右电机驱动

| STM32 引脚 | 连接目标 |
|-----------|----------|
| PA4 | BIN1 |
| PA5 | BIN2 |

### 霍尔编码器 (Hall Encoder)

#### 左编码器

| H桥驱动板 | STM32 引脚 | 功能 |
|----------|-----------|------|
| E1A | PA0 | TIM2_CH1 |
| E1B | PA1 | TIM2_CH2 |

#### 右编码器

| H桥驱动板 | STM32 引脚 | 功能 |
|----------|-----------|------|
| E2A | PB6 | TIM4_CH1 |
| E2B | PB7 | TIM4_CH2 |

### ICM42688 姿态传感器

| ICM42688 | STM32 引脚 | 功能 |
|----------|-----------|------|
| SCL | PB10 | I2C 2 |
| SDA | PB11 | I2C 2 |

### 有源蜂鸣器

PC14

#### 电源连接

- **GND**: 接地
- **5V**: 5V 电源

### 树莓派通信 (Raspberry Pi)

| STM32 引脚 | 功能 | 树莓派引脚 |
|-----------|------|-----------|
| PA9 | USART_1 TX | GPIO 15 (RX) |
| PA10 | USART_1 RX | GPIO 14 (TX) |

### 激光雷达 (Lidar)

| 设备 | STM32 引脚 | 功能 | 说明 |
|------|-----------|------|------|
| LD14 | PA3 | USART_2 RX | 单向输入，接收 LD14 TX |

### OLED 显示屏

