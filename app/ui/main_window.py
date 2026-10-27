"""
Volume Booster Pro - Main Desktop Application Window
Cyber dark glassmorphic interface with real-time spectrum visualizer,
system-wide volume controls, 3-band equalizer, presets, and tray management.
"""

import os
import sys
from typing import Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QComboBox, QCheckBox, QFrame, QScrollArea, QInputDialog,
    QMessageBox, QFileDialog
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QThread, Slot

from app.config import ConfigManager, DEFAULT_PRESETS, APP_DISPLAY_NAME, APP_VERSION
from app.dsp import volume_percent_to_db
from app.apo_engine import EqualizerApoEngine
from app.audio_monitor import AudioMonitorWorker, get_playback_devices, get_default_playback_device_name
from app.ui.styles import CYBER_DARK_STYLESHEET
from app.ui.visualizer import SpectrumVisualizerWidget
from app.ui.apo_dialog import ApoSetupDialog
from app.ui.tray import TrayManager


class MainWindow(QMainWindow):
    """Main application window for Volume Booster Pro."""

    def __init__(self, config: ConfigManager, apo_engine: EqualizerApoEngine):
        super().__init__()
        self.config = config
        self.apo = apo_engine

        self.setWindowTitle(f"{APP_DISPLAY_NAME} — Windows System-Wide Audio Enhancer")
        self.setMinimumSize(490, 760)
        self.resize(520, 820)

        # Set application icon
        icon_path = os.path.abspath("assets/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(CYBER_DARK_STYLESHEET)

        # Audio monitor thread
        self.monitor_thread = QThread(self)
        self.monitor_worker = AudioMonitorWorker()
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.start_monitoring)

        # Initialize Tray Manager
        self.tray = TrayManager(icon_path, self)
        self.tray.restore_requested.connect(self.restore_from_tray)
        self.tray.bypass_toggled.connect(self.set_bypass)
        self.tray.preset_selected.connect(self.apply_preset)
        self.tray.volume_selected.connect(self.set_volume)
        self.tray.exit_requested.connect(self.exit_app)
        self.tray.show()

        self._init_ui()
        self._load_state_into_ui()
        self._apply_audio_dsp(notify_apo=True)

        # Start audio monitoring
        self.monitor_worker.spectrum_updated.connect(self.visualizer.update_audio_data)
        self.monitor_thread.start()

    def _init_ui(self):
        """Construct the complete user interface layout."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # 1. Header (Logo, Title, Engine Status Badge, Master Status Pill)
        header_layout = QHBoxLayout()

        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)

        logo_lbl = QLabel()
        logo_pix = QPixmap("assets/icon.png")
        if not logo_pix.isNull():
            logo_lbl.setPixmap(logo_pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        app_title = QLabel("VOLUME BOOSTER PRO")
        app_title.setStyleSheet("font-size: 14px; font-weight: 900; color: #ffffff; letter-spacing: 0.8px;")
        sub_title = QLabel(f"v{APP_VERSION} • Windows System-Wide")
        sub_title.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: 600;")
        title_box.addWidget(app_title)
        title_box.addWidget(sub_title)
        brand_layout.addLayout(title_box)

        header_layout.addLayout(brand_layout)
        header_layout.addStretch()

        # Engine Badge & Master Status Pill
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        self.apo_badge = QPushButton("APO: CHECKING")
        self.apo_badge.setCursor(Qt.PointingHandCursor)
        self.apo_badge.clicked.connect(self._open_apo_dialog)
        badges_layout.addWidget(self.apo_badge)

        self.status_pill = QLabel("BOOSTING")
        self.status_pill.setProperty("class", "status-pill-active")
        badges_layout.addWidget(self.status_pill)

        header_layout.addLayout(badges_layout)
        main_layout.addLayout(header_layout)

        # 2. Output Device Selection Card
        dev_card = QFrame()
        dev_card.setProperty("class", "glass-card")
        dev_layout = QHBoxLayout(dev_card)
        dev_layout.setContentsMargins(12, 8, 12, 8)
        dev_layout.setSpacing(8)

        dev_icon = QLabel("🔊")
        dev_layout.addWidget(dev_icon)

        self.device_combo = QComboBox()
        self.device_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._populate_audio_devices()
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        dev_layout.addWidget(self.device_combo, 1)

        btn_refresh_dev = QPushButton("🔄")
        btn_refresh_dev.setToolTip("Refresh audio playback devices")
        btn_refresh_dev.setFixedWidth(36)
        btn_refresh_dev.clicked.connect(self._populate_audio_devices)
        dev_layout.addWidget(btn_refresh_dev)

        main_layout.addWidget(dev_card)

        # 3. Real-Time Spectrum Visualizer Card
        viz_card = QFrame()
        viz_card.setProperty("class", "glass-card")
        viz_layout = QVBoxLayout(viz_card)
        viz_layout.setContentsMargins(12, 10, 12, 10)
        viz_layout.setSpacing(6)

        viz_header = QHBoxLayout()
        viz_title = QLabel("REAL-TIME SYSTEM AUDIO SPECTRUM")
        viz_title.setProperty("class", "section-title")
        viz_header.addWidget(viz_title)
        viz_header.addStretch()

        self.rms_readout = QLabel("RMS: 0.0 dB")
        self.rms_readout.setStyleSheet("font-size: 11px; font-weight: 700; color: #a855f7;")
        viz_header.addWidget(self.rms_readout)
        viz_layout.addLayout(viz_header)

        self.visualizer = SpectrumVisualizerWidget(self)
        viz_layout.addWidget(self.visualizer)

        main_layout.addWidget(viz_card)

        # 4. Master Volume Amplification Card
        vol_card = QFrame()
        vol_card.setProperty("class", "glass-card")
        vol_layout = QVBoxLayout(vol_card)
        vol_layout.setContentsMargins(14, 12, 14, 12)
        vol_layout.setSpacing(10)

        vol_header = QHBoxLayout()
        vol_label = QLabel("SYSTEM AMPLIFICATION")
        vol_label.setProperty("class", "section-title")
        vol_header.addWidget(vol_label)
        vol_header.addStretch()

        self.vol_num_lbl = QLabel("125%")
        self.vol_num_lbl.setProperty("class", "volume-num")
        vol_header.addWidget(self.vol_num_lbl)

        self.vol_db_lbl = QLabel("+1.9 dB")
        self.vol_db_lbl.setProperty("class", "volume-db")
        vol_header.addWidget(self.vol_db_lbl)
        vol_layout.addLayout(vol_header)

        # Master Slider
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(100, 300)
        self.vol_slider.setValue(125)
        self.vol_slider.valueChanged.connect(self._on_volume_slider_changed)
        vol_layout.addWidget(self.vol_slider)

        # Snap Tick Buttons (100%, 125%, 150%, 200%, 300%)
        ticks_layout = QHBoxLayout()
        self.tick_buttons = {}
        for vol in [100, 125, 150, 200, 300]:
            btn = QPushButton(f"{vol}%")
            btn.setProperty("class", "tick-btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, v=vol: self.set_volume(v))
            ticks_layout.addWidget(btn)
            self.tick_buttons[vol] = btn
        vol_layout.addLayout(ticks_layout)

        # High Amplification Warning (>200%)
        self.warning_box = QFrame()
        self.warning_box.setProperty("class", "warning-banner")
        warn_layout = QHBoxLayout(self.warning_box)
        warn_layout.setContentsMargins(8, 6, 8, 6)
        warn_icon = QLabel("⚠️")
        warn_layout.addWidget(warn_icon)
        warn_text = QLabel("High Amplification (>200%): Small laptop speakers may distort. Keep audio comfortable.")
        warn_text.setProperty("class", "warning-text")
        warn_text.setWordWrap(True)
        warn_layout.addWidget(warn_text)
        vol_layout.addWidget(self.warning_box)
        self.warning_box.setVisible(False)

        main_layout.addWidget(vol_card)

        # 5. Tuned Presets Card
        preset_card = QFrame()
        preset_card.setProperty("class", "glass-card")
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(12, 10, 12, 10)
        preset_layout.setSpacing(8)

        preset_header = QHBoxLayout()
        preset_title = QLabel("ACOUSTIC PRESETS")
        preset_title.setProperty("class", "section-title")
        preset_header.addWidget(preset_title)
        preset_header.addStretch()
        self.active_preset_lbl = QLabel("Balanced")
        self.active_preset_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #00f0ff;")
        preset_header.addWidget(self.active_preset_lbl)
        preset_layout.addLayout(preset_header)

        # 5 Preset Buttons Grid
        presets_grid = QHBoxLayout()
        presets_grid.setSpacing(6)
        self.preset_btns = {}

        presets_info = [
            ("normal", "Normal", "100% Flat"),
            ("balanced", "Balanced", "125% Default"),
            ("bass_boost", "Bass Boost", "140% Rumble"),
            ("movie", "Movie", "150% Vocals"),
            ("voice", "Voice", "160% Clear")
        ]

        for key, name, sub in presets_info:
            btn = QPushButton(f"{name}\n{sub}")
            btn.setProperty("class", "preset-btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.apply_preset(k))
            presets_grid.addWidget(btn)
            self.preset_btns[key] = btn

        preset_layout.addLayout(presets_grid)
        main_layout.addWidget(preset_card)

        # 6. 3-Band Equalizer Card
        eq_card = QFrame()
        eq_card.setProperty("class", "glass-card")
        eq_layout = QVBoxLayout(eq_card)
        eq_layout.setContentsMargins(14, 10, 14, 10)
        eq_layout.setSpacing(8)

        eq_header = QHBoxLayout()
        eq_title = QLabel("3-BAND PARAMETRIC EQUALIZER")
        eq_title.setProperty("class", "section-title")
        eq_header.addWidget(eq_title)
        eq_header.addStretch()

        btn_reset_eq = QPushButton("Reset EQ")
        btn_reset_eq.setStyleSheet("background: transparent; color: #a855f7; border: none; font-size: 11px; font-weight: 700;")
        btn_reset_eq.setCursor(Qt.PointingHandCursor)
        btn_reset_eq.clicked.connect(self._reset_eq)
        eq_header.addWidget(btn_reset_eq)

        eq_layout.addLayout(eq_header)

        # Bass Band (-6 to +6 dB, 150 Hz)
        self.bass_slider, self.bass_val_lbl = self._create_eq_row("Bass (150 Hz)", -60, 60, 15)
        self.bass_slider.valueChanged.connect(self._on_eq_slider_changed)
        eq_layout.addLayout(self._wrap_eq_row("Bass", "150 Hz", self.bass_slider, self.bass_val_lbl))

        # Voice Clarity Band (-4 to +6 dB, 2.2 kHz)
        self.voice_slider, self.voice_val_lbl = self._create_eq_row("Voice (2.2 kHz)", -40, 60, 20)
        self.voice_slider.valueChanged.connect(self._on_eq_slider_changed)
        eq_layout.addLayout(self._wrap_eq_row("Voice", "2.2 kHz", self.voice_slider, self.voice_val_lbl))

        # Treble Band (-6 to +6 dB, 7.0 kHz)
        self.treble_slider, self.treble_val_lbl = self._create_eq_row("Treble (7.0 kHz)", -60, 60, 10)
        self.treble_slider.valueChanged.connect(self._on_eq_slider_changed)
        eq_layout.addLayout(self._wrap_eq_row("Treble", "7.0 kHz", self.treble_slider, self.treble_val_lbl))

        # Custom Preset Save/Load Actions
        custom_layout = QHBoxLayout()
        btn_save_preset = QPushButton("💾 Save Custom Preset")
        btn_save_preset.clicked.connect(self._save_custom_preset)
        custom_layout.addWidget(btn_save_preset)

        btn_load_preset = QPushButton("📂 Load Preset")
        btn_load_preset.clicked.connect(self._load_custom_preset)
        custom_layout.addWidget(btn_load_preset)
        eq_layout.addLayout(custom_layout)

        main_layout.addWidget(eq_card)

        # 7. Master Actions & Controls
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_bypass = QPushButton("⚡ MASTER BYPASS (DISABLE)")
        self.btn_bypass.setProperty("class", "btn-primary")
        self.btn_bypass.setCursor(Qt.PointingHandCursor)
        self.btn_bypass.clicked.connect(self._toggle_bypass)
        actions_layout.addWidget(self.btn_bypass, 2)

        self.btn_reset_all = QPushButton("Restore Defaults")
        self.btn_reset_all.clicked.connect(self._restore_defaults)
        actions_layout.addWidget(self.btn_reset_all, 1)

        main_layout.addLayout(actions_layout)

        # 8. Settings & Integration Checkboxes
        settings_card = QFrame()
        settings_card.setProperty("class", "glass-card")
        set_layout = QHBoxLayout(settings_card)
        set_layout.setContentsMargins(12, 6, 12, 6)

        self.chk_startup = QCheckBox("Start with Windows")
        self.chk_startup.setChecked(self.config.settings.get("start_with_windows", False))
        self.chk_startup.toggled.connect(self._on_startup_toggled)
        set_layout.addWidget(self.chk_startup)

        self.chk_tray = QCheckBox("Minimize to Tray")
        self.chk_tray.setChecked(self.config.settings.get("minimize_to_tray", True))
        self.chk_tray.toggled.connect(lambda v: self._update_setting("minimize_to_tray", v))
        set_layout.addWidget(self.chk_tray)

        self.chk_close = QCheckBox("Close to Tray")
        self.chk_close.setChecked(self.config.settings.get("close_to_tray", True))
        self.chk_close.toggled.connect(lambda v: self._update_setting("close_to_tray", v))
        set_layout.addWidget(self.chk_close)

        main_layout.addWidget(settings_card)

        # 9. Safety Advisory Footer
        footer_lbl = QLabel(
            "Volume Booster Pro enhances system-wide audio across all Windows applications. "
            "Software amplification cannot guarantee physical speaker hardware safety; please listen at comfortable volumes."
        )
        footer_lbl.setWordWrap(True)
        footer_lbl.setStyleSheet("font-size: 9px; color: #64748b; padding: 2px 4px; line-height: 1.3;")
        main_layout.addWidget(footer_lbl)

    def _create_eq_row(self, label: str, min_v: int, max_v: int, def_v: int):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(def_v)
        val_lbl = QLabel(f"{def_v / 10.0:+.1f} dB")
        val_lbl.setFixedWidth(52)
        val_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #00f0ff;")
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return slider, val_lbl

    def _wrap_eq_row(self, name: str, freq: str, slider: QSlider, val_lbl: QLabel):
        row = QHBoxLayout()
        meta = QVBoxLayout()
        meta.setSpacing(0)
        n_lbl = QLabel(name)
        n_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #fff;")
        f_lbl = QLabel(freq)
        f_lbl.setStyleSheet("font-size: 9px; color: #64748b;")
        meta.addWidget(n_lbl)
        meta.addWidget(f_lbl)
        meta_widget = QWidget()
        meta_widget.setLayout(meta)
        meta_widget.setFixedWidth(64)

        row.addWidget(meta_widget)
        row.addWidget(slider, 1)
        row.addWidget(val_lbl)
        return row

    def _populate_audio_devices(self):
        """Populate the playback devices dropdown."""
        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        devices = get_playback_devices()
        default_dev = get_default_playback_device_name()
        saved_dev = self.config.settings.get("device_name", "")

        select_idx = 0
        for idx, d in enumerate(devices):
            self.device_combo.addItem(f"{d['name']} ({d['channels']} ch)", d["name"])
            if saved_dev and saved_dev.lower() in d["name"].lower():
                select_idx = idx
            elif not saved_dev and default_dev.lower() in d["name"].lower():
                select_idx = idx

        if self.device_combo.count() > select_idx:
            self.device_combo.setCurrentIndex(select_idx)

        self.device_combo.blockSignals(False)

    def _on_device_changed(self, index: int):
        dev_name = self.device_combo.currentData()
        if dev_name:
            self.config.settings["device_name"] = dev_name
            self.config.save_settings()
            self._apply_audio_dsp(notify_apo=True)

    def _load_state_into_ui(self):
        """Synchronize UI with persistent settings."""
        s = self.config.settings
        vol = s.get("volume", 125)
        self.vol_slider.setValue(int(vol))
        self._update_volume_labels(vol)

        self.bass_slider.setValue(int(s.get("bass", 1.5) * 10))
        self.voice_slider.setValue(int(s.get("voice", 2.0) * 10))
        self.treble_slider.setValue(int(s.get("treble", 1.0) * 10))

        bypassed = s.get("bypassed", False)
        self._update_bypass_ui(bypassed)

        preset_key = s.get("preset", "balanced")
        self._highlight_preset(preset_key)
        self._update_apo_status_badge()

    def _update_volume_labels(self, vol: float):
        self.vol_num_lbl.setText(f"{int(vol)}%")
        db = volume_percent_to_db(vol)
        self.vol_db_lbl.setText(f"{db:+.1f} dB")
        self.warning_box.setVisible(vol > 200)

        for v, btn in self.tick_buttons.items():
            if abs(v - vol) < 2:
                btn.setStyleSheet("color: #00f0ff; font-weight: 800;")
            else:
                btn.setStyleSheet("color: #64748b; font-weight: 700;")

    def _highlight_preset(self, preset_key: str):
        self.active_preset_lbl.setText(preset_key.capitalize())
        for k, btn in self.preset_btns.items():
            if k == preset_key:
                btn.setStyleSheet(
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 240, 255, 0.2), stop:1 rgba(168, 85, 247, 0.25)); "
                    "border: 1px solid #00f0ff; color: #00f0ff; border-radius: 8px; font-weight: 700;"
                )
            else:
                btn.setStyleSheet(
                    "background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); "
                    "border-radius: 8px; color: #f8fafc; font-weight: 600;"
                )

    def _update_apo_status_badge(self):
        installed = self.apo.is_installed()
        if installed:
            self.apo_badge.setText("EQUALIZER APO: ACTIVE")
            self.apo_badge.setStyleSheet(
                "background: rgba(0, 240, 255, 0.15); border: 1px solid rgba(0, 240, 255, 0.5); "
                "border-radius: 10px; color: #00f0ff; font-size: 10px; font-weight: 800; padding: 4px 10px;"
            )
        else:
            self.apo_badge.setText("APO: SETUP REQUIRED")
            self.apo_badge.setStyleSheet(
                "background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.5); "
                "border-radius: 10px; color: #fbbf24; font-size: 10px; font-weight: 800; padding: 4px 10px;"
            )

    def _update_bypass_ui(self, bypassed: bool):
        if bypassed:
            self.status_pill.setText("BYPASS (100%)")
            self.status_pill.setStyleSheet(
                "background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.5); "
                "border-radius: 12px; color: #f87171; font-size: 11px; font-weight: 800; padding: 4px 12px;"
            )
            self.btn_bypass.setText("▶️ ENABLE AUDIO BOOST")
            self.btn_bypass.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #00f0ff); "
                "color: #090d16; font-weight: 900; border-radius: 8px; padding: 10px 18px;"
            )
        else:
            vol = self.config.settings.get("volume", 125)
            self.status_pill.setText(f"BOOSTING ({int(vol)}%)")
            self.status_pill.setStyleSheet(
                "background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.5); "
                "border-radius: 12px; color: #34d399; font-size: 11px; font-weight: 800; padding: 4px 12px;"
            )
            self.btn_bypass.setText("⚡ MASTER BYPASS (DISABLE)")
            self.btn_bypass.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7); "
                "color: #090d16; font-weight: 900; border-radius: 8px; padding: 10px 18px;"
            )
        self.tray.set_bypassed(bypassed)

    def _apply_audio_dsp(self, notify_apo: bool = True):
        """Update system-level audio profile."""
        s = self.config.settings
        vol = s.get("volume", 125)
        bass = s.get("bass", 1.5)
        voice = s.get("voice", 2.0)
        treble = s.get("treble", 1.0)
        bypassed = s.get("bypassed", False)
        device = s.get("device_name", "")

        if notify_apo and self.apo.is_installed():
            self.apo.update_profile(vol, bass, voice, treble, bypassed=bypassed, device_name=device)

    def set_volume(self, vol: int):
        """Set volume percentage."""
        self.vol_slider.setValue(vol)

    def _on_volume_slider_changed(self, val: int):
        self.config.settings["volume"] = val
        self.config.settings["preset"] = "custom"
        self._update_volume_labels(val)
        self._highlight_preset("custom")
        self._apply_audio_dsp(notify_apo=True)
        self.config.save_settings()

    def _on_eq_slider_changed(self):
        b = self.bass_slider.value() / 10.0
        v = self.voice_slider.value() / 10.0
        t = self.treble_slider.value() / 10.0

        self.bass_val_lbl.setText(f"{b:+.1f} dB")
        self.voice_val_lbl.setText(f"{v:+.1f} dB")
        self.treble_val_lbl.setText(f"{t:+.1f} dB")

        self.config.settings["bass"] = b
        self.config.settings["voice"] = v
        self.config.settings["treble"] = t
        self.config.settings["preset"] = "custom"
        self._highlight_preset("custom")

        self._apply_audio_dsp(notify_apo=True)
        self.config.save_settings()

    def _reset_eq(self):
        """Reset EQ bands to flat 0 dB."""
        self.bass_slider.setValue(0)
        self.voice_slider.setValue(0)
        self.treble_slider.setValue(0)

    def apply_preset(self, preset_key: str):
        """Apply a named preset."""
        preset = self.config.get_preset(preset_key)
        if not preset:
            return

        self.vol_slider.blockSignals(True)
        self.bass_slider.blockSignals(True)
        self.voice_slider.blockSignals(True)
        self.treble_slider.blockSignals(True)

        vol = preset["volume"]
        b = preset["bass"]
        v = preset["voice"]
        t = preset["treble"]

        self.vol_slider.setValue(int(vol))
        self.bass_slider.setValue(int(b * 10))
        self.voice_slider.setValue(int(v * 10))
        self.treble_slider.setValue(int(t * 10))

        self.bass_val_lbl.setText(f"{b:+.1f} dB")
        self.voice_val_lbl.setText(f"{v:+.1f} dB")
        self.treble_val_lbl.setText(f"{t:+.1f} dB")

        self._update_volume_labels(vol)
        self._highlight_preset(preset_key)

        self.vol_slider.blockSignals(False)
        self.bass_slider.blockSignals(False)
        self.voice_slider.blockSignals(False)
        self.treble_slider.blockSignals(False)

        self.config.settings["volume"] = vol
        self.config.settings["bass"] = b
        self.config.settings["voice"] = v
        self.config.settings["treble"] = t
        self.config.settings["preset"] = preset_key

        self._apply_audio_dsp(notify_apo=True)
        self.config.save_settings()

    def _toggle_bypass(self):
        bypassed = not self.config.settings.get("bypassed", False)
        self.set_bypass(bypassed)

    def set_bypass(self, bypassed: bool):
        self.config.settings["bypassed"] = bypassed
        self._update_bypass_ui(bypassed)
        self._apply_audio_dsp(notify_apo=True)
        self.config.save_settings()

    def _restore_defaults(self):
        self.apply_preset("balanced")
        self.set_bypass(False)

    def _save_custom_preset(self):
        name, ok = QInputDialog.getText(self, "Save Custom Preset", "Enter preset name:")
        if ok and name.strip():
            vol = self.config.settings["volume"]
            b = self.config.settings["bass"]
            v = self.config.settings["voice"]
            t = self.config.settings["treble"]
            if self.config.save_custom_preset(name, vol, b, v, t):
                QMessageBox.information(self, "Preset Saved", f"Preset '{name.strip()}' has been saved.")

    def _load_custom_preset(self):
        presets = self.config.custom_presets
        if not presets:
            QMessageBox.information(self, "No Custom Presets", "No custom presets found. Save one first!")
            return
        items = [p["name"] for p in presets.values()]
        item, ok = QInputDialog.getItem(self, "Load Preset", "Select a preset:", items, 0, False)
        if ok and item:
            for k, p in presets.items():
                if p["name"] == item:
                    self.apply_preset(k)
                    break

    def _open_apo_dialog(self):
        dlg = ApoSetupDialog(self.apo, self)
        dlg.exec()
        self.apo = EqualizerApoEngine()
        self._update_apo_status_badge()
        self._apply_audio_dsp(notify_apo=True)

    def _on_startup_toggled(self, checked: bool):
        self.config.set_start_with_windows(checked)

    def _update_setting(self, key: str, val: Any):
        self.config.settings[key] = val
        self.config.save_settings()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.config.settings.get("minimize_to_tray", True):
                self.hide()
        super().changeEvent(event)

    def closeEvent(self, event):
        if self.config.settings.get("close_to_tray", True):
            event.ignore()
            self.hide()
            self.tray.show_message(
                "Volume Booster Pro",
                "Application is still running in the system tray. Right-click the icon to exit."
            )
        else:
            self.exit_app()

    def exit_app(self):
        """Clean shutdown."""
        self.monitor_worker.stop()
        self.monitor_thread.quit()
        self.monitor_thread.wait(1000)
        self.tray.hide()
        sys.exit(0)
