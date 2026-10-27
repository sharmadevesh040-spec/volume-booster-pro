"""
Volume Booster Pro - Real-Time Audio Monitor and Device Enumerator
Captures live audio from Windows endpoints to drive the spectrum visualizer and VU meters.
"""

import time
import math
import numpy as np
import sounddevice as sd
from typing import List, Dict, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QThread

from app.dsp import compute_spectrum


class AudioMonitorWorker(QObject):
    """Worker thread running continuous audio capture and FFT analysis."""

    spectrum_updated = Signal(list, float, float, bool)  # (bins, rms, peak, is_playing)

    def __init__(self, target_device_name: str = ""):
        super().__init__()
        self.target_device_name = target_device_name
        self._running = False
        self._stream: Optional[sd.InputStream] = None
        self._latest_buffer = np.zeros((1024, 2), dtype=np.float32)
        self._has_audio_data = False

    def find_best_capture_device(self) -> Optional[int]:
        """Find the best loopback/recording device on the system."""
        devices = sd.query_devices()
        preferred_names = ["stereo mix", "what u hear", "wave out", "loopback", "cable output"]

        # 1. Search for loopback devices
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", "").lower()
                for pref in preferred_names:
                    if pref in name:
                        return idx

        # 2. Search for any valid default input device
        try:
            default_in = sd.default.device[0]
            if default_in is not None and default_in >= 0:
                return default_in
        except Exception:
            pass

        # 3. Fallback to first input device
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                return idx

        return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Low-latency callback from audio capture stream."""
        if status:
            pass
        self._latest_buffer = indata.copy()
        self._has_audio_data = True

    def start_monitoring(self):
        """Start the audio capture loop."""
        self._running = True
        dev_idx = self.find_best_capture_device()

        if dev_idx is not None:
            try:
                # Open 48kHz stereo stream with 1024 samples buffer (~21ms)
                self._stream = sd.InputStream(
                    device=dev_idx,
                    channels=2,
                    samplerate=48000,
                    blocksize=1024,
                    callback=self._audio_callback
                )
                self._stream.start()
            except Exception as e:
                print(f"[AudioMonitor] Could not start hardware capture stream on device {dev_idx}: {e}")
                self._stream = None

        idle_phase = 0.0

        # Processing loop at ~40 FPS (25ms)
        while self._running:
            if self._stream and self._has_audio_data:
                chunk = self._latest_buffer
                bins, rms, peak = compute_spectrum(chunk, num_bins=16, sample_rate=48000)
                is_playing = rms > 0.005
                self.spectrum_updated.emit(bins, rms, peak, is_playing)
            else:
                # Ambient idle wave animation when no audio is flowing
                idle_phase += 0.06
                idle_bins = []
                for i in range(16):
                    val = 0.04 + 0.03 * math.sin(idle_phase + i * 0.45)
                    idle_bins.append(round(max(0.02, val), 3))
                self.spectrum_updated.emit(idle_bins, 0.0, 0.0, False)

            time.sleep(0.025)

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def stop(self):
        """Signal thread to stop monitoring."""
        self._running = False


def get_playback_devices() -> List[Dict[str, Any]]:
    """Enumerate clean list of Windows audio playback endpoints."""
    devices = sd.query_devices()
    seen_names = set()
    playback_list = []

    for idx, d in enumerate(devices):
        if d.get("max_output_channels", 0) > 0:
            name = d.get("name", "").strip()
            # Clean up redundant driver prefixes
            clean_name = name
            if " - Output" in clean_name:
                clean_name = clean_name.replace(" - Output", "")

            # Filter out duplicated sound mapper virtual entries
            if clean_name.startswith("Microsoft Sound Mapper") or clean_name.startswith("Primary Sound Driver"):
                continue

            if clean_name not in seen_names:
                seen_names.add(clean_name)
                playback_list.append({
                    "id": idx,
                    "name": clean_name,
                    "raw_name": name,
                    "channels": d.get("max_output_channels", 2),
                    "sample_rate": int(d.get("default_samplerate", 48000))
                })

    return playback_list


def get_default_playback_device_name() -> str:
    """Retrieve the current default Windows audio playback device name."""
    try:
        default_out = sd.default.device[1]
        if default_out is not None and default_out >= 0:
            info = sd.query_devices(default_out)
            name = info.get("name", "Default Audio Endpoint")
            return name.replace(" - Output", "").strip()
    except Exception:
        pass
    return "Speakers (Default)"
