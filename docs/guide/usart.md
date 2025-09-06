---
title: 树莓派USART通信
editLink: true
---


# 串口通信 UARTS

在树莓派5中， /dev/serial0 是指向 /dev/ttyAMA10 的符号链接。

将树莓派的两个引脚 GPIO14(TXD), GPIO15(RXD) 与 STM32 的 PA10(USART1_RX), PA9(USART_TX)相连。

我们要与下位机通信，则至需要关注串口 /dev/ttyAMA0

更多信息，请查阅[官方文档](https://www.raspberrypi.com/documentation/computers/configuration.html#configure-uarts)

### minicom 配置

为了能够实时查看STM32单片机发送到树莓派串口的数据，需要配置minicom 串口通信程序。

```shell
sudo apt install minicom

sudo minicom -s
```

进入 minicom 配置界面

```
选择 "Serial port setup" （串口设置）

按 A 设置串口设备（如 /dev/ttyS0）

按 E 设置波特率（Bps/Par/Bits），然后按 F 选择 115200 8N1

确保 "Hardware Flow Control" 和 "Software Flow Control" 都设置为 No

选择 "Save setup as dfl" 保存为默认配置，以后直接输入 sudo minicom 即可启动。

选择 "Exit" 开始通信。
```

## STM32 与树莓派通信协议

不使用二进制协议。JSON结构体

#### 帧格式

| 字段      | 说明         |
|-----------|--------------|
| Command   | 命令字节     |
| Data      | 数据内容     |


#### 命令格式

```
CMD:{"cmd": "MF", "timestamp": 1234567890.123, "params": {"direction": "forward", "speed": 50}}
```

#### Command（命令）

| 命令码  | 功能描述                    | 参数  |
|--------|-----------------------------|--------|
| MF   | 电机直行（速度可调）         |  speed   |
| MT   | 电机转向（带角度和速度）     | speed, angle   |
| BEZ   | 蜂鸣器                      |    |
| SPK   | 声音                        |    |

#### 响应格式

- 正常应答: `ACK:{"status": "ok", "data": {...}}`
- 错误应答: `ERR:error_messgae`

### 客户端主动上报

#### 命令格式

```
DTP:{"type": "MF", "params": {"direction": "forward", "speed": 50}}
```

