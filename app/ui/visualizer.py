"""
Volume Booster Pro - Hardware-Accelerated Spectrum Visualizer & Level Meter
Custom Qt widget rendering real-time frequency bars, gravity-decay peak caps, and VU level tracks.
"""

import math
from typing import List
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF


class SpectrumVisualizerWidget(QWidget):
    """Real-time 16-band audio spectrum visualizer with VU level meters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(88)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self.num_bars = 16
        self.bars = [0.05] * self.num_bars
        self.display_bars = [0.05] * self.num_bars
        self.peak_caps = [0.05] * self.num_bars
        self.peak_velocities = [0.0] * self.num_bars

        self.rms_level = 0.0
        self.display_rms = 0.0
        self.peak_level = 0.0
        self.is_playing = False
        self.idle_phase = 0.0

    def update_audio_data(self, bins: List[float], rms: float, peak: float, is_playing: bool):
        """Update spectrum data from audio monitor worker."""
        if len(bins) >= self.num_bars:
            self.bars = list(bins[:self.num_bars])
        self.rms_level = rms
        self.peak_level = peak
        self.is_playing = is_playing

        # Smooth interpolation (exponential smoothing)
        for i in range(self.num_bars):
            target = self.bars[i]
            if target > self.display_bars[i]:
                self.display_bars[i] = target
            else:
                self.display_bars[i] = self.display_bars[i] * 0.82 + target * 0.18

            # Peak cap gravity drop
            if self.display_bars[i] >= self.peak_caps[i]:
                self.peak_caps[i] = self.display_bars[i]
                self.peak_velocities[i] = 0.0
            else:
                self.peak_velocities[i] += 0.015
                self.peak_caps[i] = max(0.02, self.peak_caps[i] - self.peak_velocities[i])

        self.display_rms = self.display_rms * 0.75 + self.rms_level * 0.25
        self.update()

    def paintEvent(self, event):
        """Render glowing gradient frequency bars and VU meters."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()
        viz_h = h - 22

        # Background rounded dark card
        painter.setBrush(QColor(11, 15, 25, 230))
        painter.setPen(QColor(255, 255, 255, 15))
        painter.drawRoundedRect(0, 0, w, h, 8, 8)

        margin = 12
        available_w = w - (margin * 2)
        spacing = 4
        bar_w = (available_w - (spacing * (self.num_bars - 1))) / self.num_bars

        # Frequency bar gradient
        grad = QLinearGradient(0, viz_h, 0, 0)
        grad.setColorAt(0.0, QColor(0, 240, 255, 220))    # Neon Cyan
        grad.setColorAt(0.65, QColor(168, 85, 247, 230))  # Electric Purple
        grad.setColorAt(1.0, QColor(236, 72, 153, 240))   # Magenta

        # Ambient baseline waveform if audio is quiet
        if not self.is_playing:
            self.idle_phase += 0.04
            painter.setPen(QPen(QColor(0, 240, 255, 40), 1.5))
            for x in range(margin, w - margin, 4):
                rel_x = (x - margin) / available_w
                y = viz_h / 2.0 + math.sin(rel_x * 8.0 + self.idle_phase) * 5.0 * math.sin(rel_x * math.pi)
                painter.drawPoint(int(x), int(y))

        # Render 16 Frequency Bars
        for i in range(self.num_bars):
            val = self.display_bars[i]
            bar_height = max(4.0, val * (viz_h - 10))
            bx = margin + i * (bar_w + spacing)
            by = viz_h - bar_height

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_height), 2, 2)

            # Peak cap indicator
            cap_val = self.peak_caps[i]
            cap_y = viz_h - (cap_val * (viz_h - 10)) - 3.0
            if 0 <= cap_y <= viz_h:
                painter.setBrush(QColor(255, 255, 255, 220))
                painter.drawRoundedRect(QRectF(bx, cap_y, bar_w, 2.0), 1, 1)

        # Bottom VU Level Meter Track
        meter_y = h - 14
        meter_w = available_w
        meter_h = 5

        # Background track
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(QRectF(margin, meter_y, meter_w, meter_h), 2.5, 2.5)

        # Active fill
        fill_w = max(0.0, min(meter_w, self.display_rms * meter_w))
        if fill_w > 0:
            meter_grad = QLinearGradient(margin, 0, margin + meter_w, 0)
            meter_grad.setColorAt(0.0, QColor(16, 185, 129))   # Green
            meter_grad.setColorAt(0.6, QColor(0, 240, 255))    # Cyan
            meter_grad.setColorAt(0.85, QColor(168, 85, 247))  # Purple
            meter_grad.setColorAt(1.0, QColor(245, 158, 11))   # Amber
            painter.setBrush(QBrush(meter_grad))
            painter.drawRoundedRect(QRectF(margin, meter_y, fill_w, meter_h), 2.5, 2.5)

        # Decibel Tick Markers
        painter.setPen(QColor(100, 116, 139, 180))
        font = QFont("Segoe UI", 7)
        painter.setFont(font)

        markers = [("-24 dB", 0.15), ("-12 dB", 0.50), ("-6 dB", 0.75), ("0 dB", 0.98)]
        for label, pos in markers:
            tx = margin + pos * meter_w - 12
            painter.drawText(int(tx), int(meter_y - 2), label)
