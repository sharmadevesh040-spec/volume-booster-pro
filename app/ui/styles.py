"""
Volume Booster Pro - Cyber Dark Glassmorphic Design System (QSS)
Tailored HSL/Hex palette with deep navy/slate backgrounds, neon cyan and purple accents.
"""

CYBER_DARK_STYLESHEET = """
/* Base Application Window */
QMainWindow, QDialog {
    background-color: #090d16;
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    outline: none;
}

/* Glassmorphism Cards */
QFrame.glass-card {
    background-color: rgba(18, 24, 38, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

QFrame.glass-card:hover {
    border-color: rgba(0, 240, 255, 0.25);
}

/* Section Labels */
QLabel.section-title {
    font-size: 11px;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Volume Readouts */
QLabel.volume-num {
    font-size: 26px;
    font-weight: 900;
    color: #00f0ff;
    letter-spacing: -0.5px;
}

QLabel.volume-db {
    font-size: 12px;
    font-weight: 700;
    color: #a855f7;
}

/* Status Badges */
QLabel.badge-apo-active {
    background-color: rgba(0, 240, 255, 0.12);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 10px;
    color: #00f0ff;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
}

QLabel.badge-apo-warning {
    background-color: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 10px;
    color: #fbbf24;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
}

QLabel.status-pill-active {
    background-color: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.5);
    border-radius: 12px;
    color: #34d399;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 12px;
}

QLabel.status-pill-bypass {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 12px;
    color: #f87171;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 12px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #00f0ff;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #00f0ff;
    border-color: #ffffff;
}

QSlider::handle:horizontal:pressed {
    background: #a855f7;
    border-color: #ffffff;
}

/* Push Buttons */
QPushButton {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 14px;
    color: #f8fafc;
    font-weight: 600;
}

QPushButton:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(0, 240, 255, 0.4);
}

QPushButton:pressed {
    background: rgba(0, 240, 255, 0.15);
}

QPushButton.btn-primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7);
    color: #090d16;
    border: none;
    font-weight: 800;
    border-radius: 8px;
    padding: 10px 18px;
}

QPushButton.btn-primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #c084fc);
}

QPushButton.btn-bypass-active {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #f43f5e);
    color: #ffffff;
    border: none;
    font-weight: 800;
    border-radius: 8px;
    padding: 10px 18px;
}

/* Preset Chips */
QPushButton.preset-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 6px;
    font-weight: 700;
    font-size: 11px;
}

QPushButton.preset-btn:hover {
    border-color: rgba(0, 240, 255, 0.5);
    background: rgba(0, 240, 255, 0.08);
}

QPushButton.preset-btn.active-preset {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 240, 255, 0.2), stop:1 rgba(168, 85, 247, 0.25));
    border: 1px solid #00f0ff;
    color: #00f0ff;
}

/* Snap Tick Buttons */
QPushButton.tick-btn {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 4px;
}

QPushButton.tick-btn:hover {
    color: #00f0ff;
}

QPushButton.tick-btn.active-tick {
    color: #00f0ff;
}

/* Combo Box */
QComboBox {
    background: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px 12px;
    color: #f8fafc;
    font-weight: 600;
}

QComboBox:hover {
    border-color: rgba(0, 240, 255, 0.4);
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0e1422;
    border: 1px solid rgba(0, 240, 255, 0.3);
    selection-background-color: rgba(0, 240, 255, 0.2);
    selection-color: #00f0ff;
    color: #f8fafc;
    padding: 4px;
}

/* Warning Alerts */
QFrame.warning-banner {
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 8px;
    padding: 8px 12px;
}

QLabel.warning-text {
    color: #fde68a;
    font-size: 11px;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    font-size: 11px;
    color: #94a3b8;
}

QCheckBox:hover {
    color: #f8fafc;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.05);
}

QCheckBox::indicator:checked {
    background: #00f0ff;
    border-color: #00f0ff;
}

/* Tooltips */
QToolTip {
    background-color: #0e1422;
    color: #f8fafc;
    border: 1px solid #00f0ff;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
}
"""
