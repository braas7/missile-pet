from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPolygon, QCursor
from PyQt6.QtCore import Qt, QTimer, QPoint
import win32gui
import win32con
import win32api
import math
import sys
import threading

app = QApplication(sys.argv)

class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        # Screen size
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

        # Click-through
        hwnd = int(self.winId())
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            ex_style |
            win32con.WS_EX_LAYERED |
            win32con.WS_EX_TRANSPARENT
        )

        # Missile state
        self.x = self.screen_w / 2
        self.y = self.screen_h / 2
        self.vx = 0
        self.vy = 0
        self.angle = 0

        # Tunables (change live via CMD)
        self.accel = 2.5
        self.friction = 0.995
        self.bounce = 0.9

        # Update loop
        timer = QTimer(self)
        timer.timeout.connect(self.update_overlay)
        timer.start(16)

        # CMD thread
        threading.Thread(target=self.cmd_loop, daemon=True).start()

    def cmd_loop(self):
        while True:
            cmd = input(">> ").strip().lower().split()

            if not cmd:
                continue

            if cmd[0] == "accel":
                self.accel = float(cmd[1])
                print("accel =", self.accel)

            elif cmd[0] == "friction":
                self.friction = float(cmd[1])
                print("friction =", self.friction)

            elif cmd[0] == "bounce":
                self.bounce = float(cmd[1])
                print("bounce =", self.bounce)

            elif cmd[0] == "quit":
                QApplication.quit()
                break

            else:
                print("commands: accel X | friction X | bounce X | quit")

    def update_overlay(self):

        mx = QCursor.pos().x()
        my = QCursor.pos().y()

        dx = mx - self.x
        dy = my - self.y

        dist = math.hypot(dx, dy)

        if dist > 0:
            dx /= dist
            dy /= dist

            self.vx += dx * self.accel
            self.vy += dy * self.accel

        # friction (slipperiness)
        self.vx *= self.friction
        self.vy *= self.friction

        # move
        self.x += self.vx
        self.y += self.vy

        # border bounce
        if self.x < 0:
            self.x = 0
            self.vx *= -self.bounce

        if self.x > self.screen_w:
            self.x = self.screen_w
            self.vx *= -self.bounce

        if self.y < 0:
            self.y = 0
            self.vy *= -self.bounce

        if self.y > self.screen_h:
            self.y = self.screen_h
            self.vy *= -self.bounce

        # rotate
        if self.vx or self.vy:
            self.angle = math.atan2(self.vy, self.vx)

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = 50

        points = [
            QPoint(size, 0),
            QPoint(-size // 2, -size // 3),
            QPoint(-size // 2, size // 3)
        ]

        rotated = []

        for p in points:
            rx = p.x() * math.cos(self.angle) - p.y() * math.sin(self.angle)
            ry = p.x() * math.sin(self.angle) + p.y() * math.cos(self.angle)

            rotated.append(QPoint(int(self.x + rx), int(self.y + ry)))

        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygon(rotated))

overlay = Overlay()
overlay.show()

sys.exit(app.exec())