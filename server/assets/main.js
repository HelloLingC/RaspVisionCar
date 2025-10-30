// RaspVisionCar Console JavaScript
// 处理小车控制和PID参数调整

// 全局变量
let currentSpeed = 50;
let isConnected = false;
let uptimeInterval;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('RaspVisionCar Console 初始化');
    
    // 初始化连接状态
    updateConnectionStatus(true);
    
    // 启动运行时间计时器
    startUptimeCounter();
    
    // 初始化PID参数显示
    updatePidDisplay();
});

// 连接状态管理
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.textContent = '已连接';
        statusElement.style.color = '#4CAF50';
        isConnected = true;
    } else {
        statusElement.textContent = '未连接';
        statusElement.style.color = '#dc3545';
        isConnected = false;
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
function move(direction) {
    if (!isConnected) {
        alert('设备未连接，无法控制');
        return;
    }
    
    console.log(`移动命令: ${direction}, 速度: ${currentSpeed}`);
    
    // 发送控制命令到后端
    fetch(`/control?command=${direction}&speed=${currentSpeed}`)
        .then(response => {
            if (response.ok) {
                console.log(`移动命令发送成功: ${direction}`);
            } else {
                console.error('移动命令发送失败');
            }
        })
        .catch(error => {
            console.error('发送移动命令时出错:', error);
        });
}

function startCar() {
    if (!isConnected) {
        alert('设备未连接，无法启动');
        return;
    }

    console.log('启动小车');

    fetch('/control?command=start')
        .then(response => {
            if (response.ok) {
                console.log('小车启动成功');
                alert('小车已启动');
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
    if (!isConnected) {
        alert('设备未连接，无法停止');
        return;
    }
    
    console.log('停止小车');
    
    fetch('/control?command=stop')
        .then(response => {
            if (response.ok) {
                console.log('小车停止成功');
                alert('小车已停止');
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
    if (!isConnected) {
        alert('设备未连接，无法蜂鸣');
        return;
    }

    console.log('蜂鸣');

    fetch('/control?command=beep')
        .then(response => {
            if (response.ok) {
                console.log('蜂鸣成功');
                alert('蜂鸣成功');
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
    if (!isConnected) {
        alert('设备未连接，无法设置PID参数');
        return;
    }
    
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
        const speed = Math.floor(Math.random() * 20); // 0-20 km/h
        speedElement.textContent = speed + ' km/h';
    }
}

// 定期更新状态数据
setInterval(updateStatusData, 2000);

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (uptimeInterval) {
        clearInterval(uptimeInterval);
    }
});
