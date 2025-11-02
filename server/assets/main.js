// RaspVisionCar Console JavaScript
// 处理小车控制和PID参数调整

// 全局变量
let currentSpeed = 50;
let uptimeInterval;
let websocket = null;

// 移动参数变量
let turnAngle = 20;  // 转向角度值
let moveSpeed = 50;  // 移动速度值

// WebSocket 连接
function connectWebSocket() {
    // 获取当前页面的主机和端口，构建 WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsPort = '5000'; // WebSocket 服务器端口
    const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}`;
    
    console.log(`正在连接 WebSocket: ${wsUrl}`);
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('WebSocket 连接成功');
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('收到 WebSocket 消息:', data);
                
                if (data.type === 'connected') {
                    console.log(data.message);
                } else if (data.type === 'move_ack') {
                    console.log(`移动命令确认`);
                } else if (data.type === 'error') {
                    console.error('WebSocket 错误:', data.message);
                    alert('错误: ' + data.message);
                }
            } catch (e) {
                console.error('解析 WebSocket 消息失败:', e);
            }
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket 错误:', error);
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket 连接关闭，尝试重新连接...');
            // 3秒后尝试重新连接
            setTimeout(connectWebSocket, 3000);
        };
    } catch (error) {
        console.error('创建 WebSocket 连接失败:', error);
        // 如果 WebSocket 不支持，可以回退到 HTTP
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('RaspVisionCar Console 初始化');
    
    // 初始化小车运行状态
    updateCarStatus(false);
    
    // 启动运行时间计时器
    startUptimeCounter();
    
    // 初始化PID参数显示
    updatePidDisplay();
    
    // 初始化移动参数显示
    updateTurnAngle(turnAngle);
    updateMoveSpeed(moveSpeed);
    
    // 连接 WebSocket
    connectWebSocket();
});

// 连接状态管理
function updateCarStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (status) {
        statusElement.textContent = 'Running';
        statusElement.style.color = '#4CAF50';
    } else {
        statusElement.textContent = 'Stopped';
        statusElement.style.color = '#dc3545';
    }
}

// 运行时间计时器
function startUptimeCounter() {
    let seconds = 0;
    uptimeInterval = setInterval(() => {
        seconds++;
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        const uptimeElement = document.getElementById('uptime');
        uptimeElement.textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
}

// 小车控制函数
function move(turn_angle, left_speed, right_speed) {
    console.log(`移动命令: 转向角度: ${turn_angle}, 左速度: ${left_speed}, 右速度: ${right_speed}`);

    // 通过 WebSocket 发送移动命令
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        const message = {
            type: 'move',
            turn_angle: turn_angle,
            left_speed: left_speed,
            right_speed: right_speed,
        };
        websocket.send(JSON.stringify(message));
        console.log('已通过 WebSocket 发送移动命令:', message);
    }
}

// 移动控制函数
function moveUp() {
    move(0, moveSpeed, moveSpeed);
}

function moveDown() {
    move(0, -moveSpeed, -moveSpeed);
}

function moveLeft() {
    move(turnAngle, moveSpeed, moveSpeed);
}

function moveRight() {
    move(-turnAngle, moveSpeed, moveSpeed);
}

function moveStop() {
    move(0, 0, 0);
}

// 更新转向角度
function updateTurnAngle(value) {
    turnAngle = parseInt(value);
    document.getElementById('turn-angle-value').textContent = turnAngle;
    document.getElementById('turn-angle-input').value = turnAngle;
    document.getElementById('turn-angle-number').value = turnAngle;
    console.log(`转向角度更新为: ${turnAngle}°`);
}

// 更新移动速度
function updateMoveSpeed(value) {
    moveSpeed = parseInt(value);
    document.getElementById('move-speed-value').textContent = moveSpeed;
    document.getElementById('move-speed-input').value = moveSpeed;
    document.getElementById('move-speed-number').value = moveSpeed;
    console.log(`移动速度更新为: ${moveSpeed}`);
}

function startCar() {
    console.log('启动小车');

    fetch('/control?command=start')
        .then(response => {
            if (response.ok) {
                console.log('小车启动成功');
                updateCarStatus(true);
            } else {
                console.error('小车启动失败');
                alert('小车启动失败');
            }
        })
        .catch(error => {
            console.error('启动小车时出错:', error);
            alert('启动小车时出错');
        });
}

function stopCar() {
    console.log('停止小车');
    
    fetch('/control?command=stop')
        .then(response => {
            if (response.ok) {
                console.log('小车停止成功');
                updateCarStatus(false);
            } else {
                console.error('小车停止失败');
                alert('小车停止失败');
            }
        })
        .catch(error => {
            console.error('停止小车时出错:', error);
            alert('停止小车时出错');
        });
}

function beep() {
    console.log('蜂鸣');

    fetch('/control?command=beep')
        .then(response => {
            if (response.ok) {
                console.log('蜂鸣成功');
            } else {
                console.error('蜂鸣失败');
                alert('蜂鸣失败');
            }
        })
        .catch(error => {
            console.error('蜂鸣时出错:', error);
            alert('蜂鸣时出错');
        });
}

// 速度控制
function updateSpeed(speed) {
    currentSpeed = parseInt(speed);
    document.getElementById('speed-value').textContent = currentSpeed + '%';
    console.log(`速度更新为: ${currentSpeed}%`);
}

// PID参数处理
function updatePidParam(type, param, value) {
    const valueElement = document.getElementById(`${type}-${param}-value`);
    if (valueElement) {
        valueElement.textContent = value;
    }
    console.log(`PID参数更新: ${type}.${param} = ${value}`);
}

function applyPidParams() {
    // 获取方向控制PID参数
    const directionKp = document.getElementById('direction-kp').value;
    const directionKi = document.getElementById('direction-ki').value;
    const directionKd = document.getElementById('direction-kd').value;
    
    // 获取速度控制PID参数
    const speedKp = document.getElementById('speed-kp').value;
    const speedKi = document.getElementById('speed-ki').value;
    const speedKd = document.getElementById('speed-kd').value;
    
    console.log('应用PID参数...');
    
    // 发送方向控制PID参数
    fetch(`/pid?direction=direction&kp=${directionKp}&ki=${directionKi}&kd=${directionKd}`)
        .then(response => {
            if (response.ok) {
                console.log('方向控制PID参数设置成功');
            } else {
                console.error('方向控制PID参数设置失败');
                throw new Error('方向控制PID参数设置失败');
            }
        })
        .then(() => {
            // 发送速度控制PID参数
            return fetch(`/pid?direction=speed&kp=${speedKp}&ki=${speedKi}&kd=${speedKd}`);
        })
        .then(response => {
            if (response.ok) {
                console.log('速度控制PID参数设置成功');
                alert('PID参数设置成功！');
            } else {
                console.error('速度控制PID参数设置失败');
                throw new Error('速度控制PID参数设置失败');
            }
        })
        .catch(error => {
            console.error('设置PID参数时出错:', error);
            alert('PID参数设置失败: ' + error.message);
        });
}

function resetPidParams() {
    // 重置方向控制PID参数
    document.getElementById('direction-kp').value = '1.0';
    document.getElementById('direction-ki').value = '0.1';
    document.getElementById('direction-kd').value = '0.1';
    
    // 重置速度控制PID参数
    document.getElementById('speed-kp').value = '1.0';
    document.getElementById('speed-ki').value = '0.1';
    document.getElementById('speed-kd').value = '0.1';
    
    // 更新显示
    updatePidDisplay();
    
    console.log('PID参数已重置为默认值');
    alert('PID参数已重置为默认值');
}

function updatePidDisplay() {
    // 更新方向控制PID显示
    updatePidParam('direction', 'kp', document.getElementById('direction-kp').value);
    updatePidParam('direction', 'ki', document.getElementById('direction-ki').value);
    updatePidParam('direction', 'kd', document.getElementById('direction-kd').value);
    
    // 更新速度控制PID显示
    updatePidParam('speed', 'kp', document.getElementById('speed-kp').value);
    updatePidParam('speed', 'ki', document.getElementById('speed-ki').value);
    updatePidParam('speed', 'kd', document.getElementById('speed-kd').value);
}

// 模拟数据更新（实际应用中应该从后端获取）
function updateStatusData() {
    // 模拟角度数据
    const angleElement = document.getElementById('battery-level');
    if (angleElement) {
        const angle = Math.floor(Math.random() * 180) - 90; // -90到90度
        angleElement.textContent = angle + '°';
    }
    
    // 模拟速度数据
    const speedElement = document.getElementById('current-speed');
    if (speedElement) {
        speedElement.textContent ='INF ++';
    }
}

// 定期更新状态数据
setInterval(updateStatusData, 2000);

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (uptimeInterval) {
        clearInterval(uptimeInterval);
    }
    // 关闭 WebSocket 连接
    if (websocket) {
        websocket.close();
    }
});
