"""
Volume Booster Pro - Equalizer APO Setup and Diagnostics Dialog
Provides transparent configuration instructions, detection, and download guidance.
"""

import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTextEdit
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from app.apo_engine import EqualizerApoEngine

EQUALIZER_APO_DOWNLOAD_URL = "https://sourceforge.net/projects/equalizerapo/"


class ApoSetupDialog(QDialog):
    """Dialog providing diagnostics and step-by-step setup for Equalizer APO."""

    def __init__(self, apo_engine: EqualizerApoEngine, parent=None):
        super().__init__(parent)
        self.apo = apo_engine
        self.setWindowTitle("Equalizer APO - System Engine Setup & Diagnostics")
        self.setFixedSize(560, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()
        self._refresh_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        title_label = QLabel("🛠️ Equalizer APO System Engine")
        title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #00f0ff;")
        layout.addWidget(title_label)

        desc = QLabel(
            "Equalizer APO is the standard Windows Audio Processing Object (APO) framework. "
            "It intercepts and modifies system audio at the kernel engine level (audiodg.exe) "
            "with zero latency, zero CPU overhead, and without requiring any virtual cables."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; line-height: 1.4;")
        layout.addWidget(desc)

        # Status Card
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setStyleSheet(
            "QFrame#statusCard { background: rgba(18, 24, 38, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 12px; }"
        )
        card_layout = QVBoxLayout(self.status_card)
        card_layout.setSpacing(6)

        self.status_header = QLabel("Detection Status: Checking...")
        self.status_header.setStyleSheet("font-weight: 700; font-size: 13px;")
        card_layout.addWidget(self.status_header)

        self.path_label = QLabel("Install Path: Not detected")
        self.path_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        card_layout.addWidget(self.path_label)

        self.config_label = QLabel("Integration Status: Not linked")
        self.config_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        card_layout.addWidget(self.config_label)

        layout.addWidget(self.status_card)

        # Step-by-Step Guide
        guide_header = QLabel("SETUP INSTRUCTIONS:")
        guide_header.setStyleSheet("font-size: 11px; font-weight: 800; color: #a855f7; letter-spacing: 0.5px;")
        layout.addWidget(guide_header)

        instructions = (
            "1. Download Equalizer APO (Official SourceForge installer).\n"
            "2. Run the installer and complete the setup wizard.\n"
            "3. In the 'Configurator' window, check your Playback Device (e.g. Speakers / Headphones).\n"
            "4. Reboot your Windows PC to allow the Windows Audio Engine to register the APO.\n"
            "5. Volume Booster Pro will automatically detect the installation and apply real-time boost!"
        )
        guide_box = QTextEdit()
        guide_box.setReadOnly(True)
        guide_box.setPlainText(instructions)
        guide_box.setStyleSheet(
            "background: rgba(11, 15, 25, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); "
            "border-radius: 8px; color: #cbd5e1; padding: 8px; font-family: monospace; font-size: 11px;"
        )
        layout.addWidget(guide_box)

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.btn_download = QPushButton("🌐 Download Equalizer APO")
        self.btn_download.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7); "
            "color: #090d16; font-weight: 800; padding: 8px 16px; border-radius: 8px;"
        )
        self.btn_download.clicked.connect(self._open_download)
        btn_layout.addWidget(self.btn_download)

        self.btn_refresh = QPushButton("🔄 Recheck Installation")
        self.btn_refresh.clicked.connect(self._refresh_status)
        btn_layout.addWidget(self.btn_refresh)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _refresh_status(self):
        """Update detection UI."""
        self.apo = EqualizerApoEngine()
        installed = self.apo.is_installed()

        if installed:
            self.status_header.setText("Detection Status: ✅ Installed and Ready")
            self.status_header.setStyleSheet("color: #10b981; font-weight: 800; font-size: 13px;")
            self.path_label.setText(f"Install Path: {self.apo.install_dir}")

            integrated = self.apo.is_integrated()
            if integrated:
                self.config_label.setText("Integration Status: ⚡ Active (VolumeBoosterPro.txt linked in config.txt)")
                self.config_label.setStyleSheet("color: #00f0ff; font-size: 11px;")
            else:
                self.config_label.setText("Integration Status: Ready to link on first boost.")
                self.config_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
        else:
            self.status_header.setText("Detection Status: ⚠️ Not Installed")
            self.status_header.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 13px;")
            self.path_label.setText("Install Path: Not found in standard directories or registry.")
            self.config_label.setText("Integration Status: Follow instructions below to enable system-wide boost.")
            self.config_label.setStyleSheet("color: #94a3b8; font-size: 11px;")

    def _open_download(self):
        webbrowser.open(EQUALIZER_APO_DOWNLOAD_URL)
