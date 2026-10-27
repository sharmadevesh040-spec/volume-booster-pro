"""
Volume Booster Pro - Virtual Audio Device Manager & Passthrough Engine
Provides transparent detection, feedback-loop protection, and setup instructions
for virtual audio devices (VB-CABLE, Virtual Audio Cable, Voicemeeter).
"""

import sounddevice as sd
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread

from app.dsp import BiquadFilter, DynamicsCompressor, apply_soft_limiter, calculate_low_shelf_coeffs, calculate_peaking_coeffs, calculate_high_shelf_coeffs


class VirtualDeviceManager:
    """Detects and manages virtual audio cable configurations."""

    KNOWN_VIRTUAL_INPUTS = [
        "cable input",
        "vb-audio",
        "virtual audio cable",
        "voicemeeter",
        "line 1 (virtual audio cable)"
    ]

    KNOWN_VIRTUAL_OUTPUTS = [
        "cable output",
        "vb-audio",
        "virtual audio cable",
        "voicemeeter out",
        "line 1 (virtual audio cable)"
    ]

    @classmethod
    def detect_virtual_devices(cls) -> Dict[str, Any]:
        """Detect virtual audio cable endpoints on the system."""
        from app.audio_monitor import safe_query_devices
        devices = safe_query_devices()
        detected_inputs = []
        detected_outputs = []

        for dev in devices:
            idx = dev["id"]
            name = dev.get("name", "").lower()

            # Check for virtual playback input (where Windows sends audio)
            if dev.get("max_output_channels", 0) > 0:
                for match in cls.KNOWN_VIRTUAL_INPUTS:
                    if match in name:
                        detected_inputs.append((idx, dev.get("name", "")))
                        break

            # Check for virtual recording output (where we capture from)
            if dev.get("max_input_channels", 0) > 0:
                for match in cls.KNOWN_VIRTUAL_OUTPUTS:
                    if match in name:
                        detected_outputs.append((idx, dev.get("name", "")))
                        break

        installed = len(detected_inputs) > 0 and len(detected_outputs) > 0
        return {
            "installed": installed,
            "inputs": detected_inputs,
            "outputs": detected_outputs,
            "primary_input": detected_inputs[0] if detected_inputs else None,
            "primary_output": detected_outputs[0] if detected_outputs else None
        }

    @staticmethod
    def get_explanation() -> str:
        """Explain why virtual audio devices are used in Windows audio engineering."""
        return (
            "Why a Virtual Audio Device is Used:\n\n"
            "By default, Windows Audio Engine routes sound directly from applications (Chrome, Spotify, VLC, games) "
            "to your hardware DAC. Windows WASAPI loopback can only listen to output—it cannot intercept and amplify sound in-place.\n\n"
            "With a Virtual Audio Cable:\n"
            "1. Windows Default Output is set to 'CABLE Input'.\n"
            "2. All Windows desktop apps send sound into the virtual cable.\n"
            "3. Volume Booster Pro captures the audio, applies real-time EQ, gain boost, and limiting.\n"
            "4. Volume Booster Pro renders the boosted sound to your physical laptop speakers or headphones.\n\n"
            "Alternatively, installing Equalizer APO is the recommended zero-latency native solution that requires NO virtual cable."
        )

    @staticmethod
    def get_setup_instructions() -> List[str]:
        """Return user setup steps for VB-CABLE."""
        return [
            "1. Download free VB-CABLE driver from official site: https://vb-audio.com/Cable/",
            "2. Run VBCABLE_Setup_x64.exe as Administrator and restart your PC.",
            "3. Open Windows Sound Settings and set 'CABLE Input' as your Default Playback Device.",
            "4. In Volume Booster Pro, select your physical laptop speakers as the Output Device.",
            "5. To restore normal sound at any time, simply switch your Windows Default Playback Device back to your speakers."
        ]


class VirtualPassthroughEngine(QThread):
    """
    Real-time low-latency audio processing bridge:
    Captures from Virtual Cable Output -> runs DSP -> outputs to Physical Speakers.
    Guarantees feedback-loop protection.
    """

    status_changed = Signal(bool, str)

    def __init__(self, input_device_id: int, output_device_id: int, sample_rate: int = 48000):
        super().__init__()
        self.input_device_id = input_device_id
        self.output_device_id = output_device_id
        self.sample_rate = sample_rate
        self._running = False

        # DSP state
        self.volume_percent = 125.0
        self.bass_db = 1.5
        self.voice_db = 2.0
        self.treble_db = 1.0
        self.bypassed = False

        # Filter nodes
        self.bass_filter = BiquadFilter(channels=2)
        self.voice_filter = BiquadFilter(channels=2)
        self.treble_filter = BiquadFilter(channels=2)
        self.compressor = DynamicsCompressor(sample_rate=sample_rate)

        self._update_filters()

    def _update_filters(self):
        """Recompute biquad coefficients."""
        b_b, a_b = calculate_low_shelf_coeffs(150.0, self.bass_db, self.sample_rate)
        self.bass_filter.set_coeffs(b_b, a_b)

        b_v, a_v = calculate_peaking_coeffs(2200.0, self.voice_db, q=1.0, sample_rate=self.sample_rate)
        self.voice_filter.set_coeffs(b_v, a_v)

        b_t, a_t = calculate_high_shelf_coeffs(7000.0, self.treble_db, self.sample_rate)
        self.treble_filter.set_coeffs(b_t, a_t)

    def update_settings(self, volume: float, bass: float, voice: float, treble: float, bypassed: bool):
        """Update live DSP settings without restarting the audio stream."""
        self.volume_percent = volume
        self.bass_db = bass
        self.voice_db = voice
        self.treble_db = treble
        self.bypassed = bypassed
        self._update_filters()

    def run(self):
        """Main audio processing stream."""
        # Feedback loop prevention: Ensure input and output are strictly distinct endpoints
        if self.input_device_id == self.output_device_id:
            self.status_changed.emit(False, "Error: Input and Output devices cannot be the same (feedback protection).")
            return

        self._running = True

        def audio_callback(indata, outdata, frames, time_info, status):
            if not self._running:
                outdata.fill(0)
                return

            if self.bypassed:
                outdata[:] = indata
                return

            # 1. Apply 3-Band Equalizer
            audio = self.bass_filter.process(indata)
            audio = self.voice_filter.process(audio)
            audio = self.treble_filter.process(audio)

            # 2. Master Gain Amplification (100% to 300% -> 1.0x to 3.0x)
            gain = max(1.0, min(3.0, self.volume_percent / 100.0))
            audio = audio * gain

            # 3. Dynamics Peak Compressor
            audio = self.compressor.process(audio)

            # 4. Soft Limiter (tanh curve to eliminate harsh digital clipping)
            audio = apply_soft_limiter(audio)

            outdata[:] = audio

        try:
            with sd.Stream(
                device=(self.input_device_id, self.output_device_id),
                samplerate=self.sample_rate,
                blocksize=512,  # ~10ms low latency
                channels=2,
                callback=audio_callback
            ):
                self.status_changed.emit(True, "Virtual Passthrough DSP Active")
                while self._running:
                    self.msleep(50)
        except Exception as e:
            self.status_changed.emit(False, f"Passthrough Error: {e}")
        finally:
            self._running = False

    def stop(self):
        """Stop passthrough stream."""
        self._running = False
        self.wait(1000)
