// WebSocket 连接 - 连接到独立的 WebSocket 服务器
const socket = io('http://localhost:5000');

// 连接状态
let isConnected = false;
let currentSpeed = 50;

// WebSocket 事件监听
socket.on('connect', function() {
    console.log('WebSocket 连接成功');
    isConnected = true;
    updateConnectionStatus('已连接', true);
});

socket.on('disconnect', function() {
    console.log('WebSocket 连接断开');
    isConnected = false;
    updateConnectionStatus('连接断开', false);
});

socket.on('status', function(data) {
    console.log('服务器状态:', data);
    if (data.connected) {
        updateConnectionStatus('已连接', true);
    }
});

socket.on('control_response', function(data) {
    console.log('控制响应:', data);
    if (data.status === 'success') {
        showNotification('命令执行成功: ' + data.message, 'success');
    } else {
        showNotification('命令执行失败: ' + data.message, 'error');
    }
});

socket.on('status_update', function(data) {
    console.log('状态更新:', data);
    updateStatusDisplay(data);
});

socket.on('emergency_alert', function(data) {
    console.log('紧急警报:', data);
    showNotification('紧急停止已激活!', 'warning');
});

// 更新连接状态显示
function updateConnectionStatus(status, connected) {
    const statusElement = document.getElementById('connection-status');
    statusElement.textContent = status;
    statusElement.style.color = connected ? '#4CAF50' : '#f44336';
}

// 显示通知
function showNotification(message, type) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    // 根据类型设置颜色
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#4CAF50';
            break;
        case 'error':
            notification.style.backgroundColor = '#f44336';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ff9800';
            break;
        default:
            notification.style.backgroundColor = '#2196F3';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// 更新状态显示
function updateStatusDisplay(data) {
    if (data.current_speed !== undefined) {
        document.getElementById('current-speed').textContent = data.current_speed + ' km/h';
    }
}

// 更新速度显示
function updateSpeed(value) {
    document.getElementById('speed-value').textContent = value + '%';
    currentSpeed = parseInt(value);
    console.log('设置速度:', value + '%');
}

// 移动控制函数
function move(direction) {
    if (!isConnected) {
        showNotification('WebSocket 未连接，无法发送命令', 'error');
        return;
    }
    
    const directions = {
        'forward': '前进',
        'backward': '后退',
        'left': '左转',
        'right': '右转'
    };
    
    console.log('小车' + directions[direction]);
    
    // 通过 WebSocket 发送控制命令
    socket.emit('car_control', {
        command: 'move',
        direction: direction,
        speed: currentSpeed
    });
}

// 停止函数
function stop() {
    if (!isConnected) {
        showNotification('WebSocket 未连接，无法发送命令', 'error');
        return;
    }
    
    console.log('小车停止');
    
    // 通过 WebSocket 发送停止命令
    socket.emit('car_control', {
        command: 'stop',
        direction: 'stop',
        speed: 0
    });
}

// 启动小车
function startCar() {
    if (!isConnected) {
        showNotification('WebSocket 未连接，无法发送命令', 'error');
        return;
    }
    
    console.log('启动小车');
    
    // 通过 WebSocket 发送启动命令
    socket.emit('car_control', {
        command: 'start',
        direction: 'start',
        speed: currentSpeed
    });
}

// 停止小车
function stopCar() {
    if (!isConnected) {
        showNotification('WebSocket 未连接，无法发送命令', 'error');
        return;
    }
    
    console.log('停止小车');
    
    // 通过 WebSocket 发送停止命令
    socket.emit('car_control', {
        command: 'stop',
        direction: 'stop',
        speed: 0
    });
}

// 紧急停止
function emergencyStop() {
    if (!isConnected) {
        showNotification('WebSocket 未连接，无法发送命令', 'error');
        return;
    }
    
    console.log('紧急停止！');
    
    // 通过 WebSocket 发送紧急停止命令
    socket.emit('emergency_stop');
}

// 键盘控制
document.addEventListener('keydown', function(event) {
    switch(event.key) {
        case 'ArrowUp':
            move('forward');
            break;
        case 'ArrowDown':
            move('backward');
            break;
        case 'ArrowLeft':
            move('left');
            break;
        case 'ArrowRight':
            move('right');
            break;
        case ' ':
            stop();
            break;
    }
});

// 定期获取状态更新
setInterval(() => {
    if (isConnected) {
        socket.emit('get_status');
    }
}, 5000); // 每5秒获取一次状态

// 处理状态数据
socket.on('status_data', function(data) {
    if (data.error) {
        console.error('获取状态错误:', data.error);
        return;
    }
    
    // 更新电池电量
    if (data.battery_level !== undefined) {
        document.getElementById('battery-level').textContent = data.battery_level + '%';
    }
    
    // 更新当前速度
    if (data.current_speed !== undefined) {
        document.getElementById('current-speed').textContent = data.current_speed + ' km/h';
    }
    
    // 更新运行时间
    if (data.uptime !== undefined) {
        document.getElementById('uptime').textContent = data.uptime;
    }
});

// 模拟实时状态更新（作为备用，当WebSocket不可用时）
setInterval(() => {
    if (!isConnected) {
        const uptimeElement = document.getElementById('uptime');
        let time = uptimeElement.textContent.split(':');
        let hours = parseInt(time[0]);
        let minutes = parseInt(time[1]);
        let seconds = parseInt(time[2]);
        
        seconds++;
        if (seconds >= 60) {
            seconds = 0;
            minutes++;
            if (minutes >= 60) {
                minutes = 0;
                hours++;
            }
        }
        
        uptimeElement.textContent = 
            hours.toString().padStart(2, '0') + ':' +
            minutes.toString().padStart(2, '0') + ':' +
            seconds.toString().padStart(2, '0');
            
        // 模拟电池电量变化
        const batteryElement = document.getElementById('battery-level');
        let battery = parseInt(batteryElement.textContent);
        if (battery > 20) {
            batteryElement.textContent = (battery - 0.1).toFixed(1) + '%';
        }
    }
}, 1000);
