import cv2
import numpy as np
from collections import deque

class CurveDetector:
    def __init__(self, window=5, smooth_len=10):
        """
        :param window: 三点计算曲率时的间隔点数
        :param smooth_len: 平滑历史长度（越大越稳但响应慢）
        """
        self.window = window
        self.curv_hist = deque(maxlen=smooth_len)

    @staticmethod
    def curvature_three_points(p1, p2, p3):
        """用三点求曲率"""
        (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
        a = np.hypot(x2-x1, y2-y1)
        b = np.hypot(x3-x2, y3-y2)
        c = np.hypot(x1-x3, y1-y3)
        s = (a + b + c) / 2
        area = np.sqrt(max(s * (s - a) * (s - b) * (s - c), 1e-6))
        if a * b * c == 0:
            return 0
        return 4 * area / (a * b * c)

    def calc_curve(self, edge_points):
        """计算平均曲率和方向"""
        curvatures = []
        directions = []
        w = self.window
        n = len(edge_points)
        if n < w + 1:
            return 0, "straight"

        for i in range(0, n - w, w):
            p1, p2, p3 = edge_points[i], edge_points[i + w // 2], edge_points[i + w]
            kappa = self.curvature_three_points(p1, p2, p3)
            # 判断方向：用向量叉积
            cross = np.cross(p2 - p1, p3 - p2)
            direction = "left" if cross > 0 else "right"
            curvatures.append(kappa)
            directions.append(direction)

        mean_curv = np.mean(curvatures)
        mean_dir = max(set(directions), key=directions.count)
        self.curv_hist.append(mean_curv)
        smooth_curv = np.mean(self.curv_hist)
        return smooth_curv, mean_dir

    def visualize(self, frame, edge_points, curvature, direction):
        """可视化结果"""
        if len(edge_points) > 1:
            for i in range(len(edge_points) - 1):
                cv2.line(frame, tuple(edge_points[i]), tuple(edge_points[i+1]), (255, 0, 255), 2)
        text = f"Curvature: {curvature:.4f} ({direction})"
        cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        return frame


if __name__ == '__main__':
    detector = CurveDetector(window=5, smooth_len=10)
    # 模拟一条曲线
    t = np.linspace(0, 1, 100)
    edge_points = np.array([[x*640, 240 + 80*np.sin(2*np.pi*x)] for x in t], dtype=np.float32)

    curv, direction = detector.calc_curve(edge_points)
    print(f"当前弯曲度: {curv:.4f}, 方向: {direction}")

    # 可选：显示
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = detector.visualize(frame, edge_points.astype(int), curv, direction)
    cv2.imshow("Curvature", frame)
    cv2.waitKey(0)