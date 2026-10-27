"""
Volume Booster Pro - Audio DSP Engine
High-performance vector DSP using NumPy: Biquad IIR filters, gain staging,
dynamics peak compressor, hyperbolic tangent soft-limiter, and FFT spectrum analysis.
"""

import math
import numpy as np
from typing import Tuple, List


def volume_percent_to_db(percent: float) -> float:
    """Convert volume percentage (100% to 300%) to Decibels."""
    gain = max(1.0, percent / 100.0)
    return 20.0 * math.log10(gain)


def db_to_gain(db: float) -> float:
    """Convert Decibels to linear amplitude multiplier."""
    return 10.0 ** (db / 20.0)


def calculate_low_shelf_coeffs(cutoff_hz: float, gain_db: float, sample_rate: int = 48000) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate RBJ Audio EQ Cookbook Low-Shelf filter coefficients."""
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * cutoff_hz / sample_rate
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt(2.0)  # Q = 1/sqrt(2)
    sqrt_A = math.sqrt(A)

    b0 = A * ((A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha)
    b1 = 2.0 * A * ((A - 1.0) - (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha)
    a0 = (A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha
    a1 = -2.0 * ((A - 1.0) + (A + 1.0) * cos_w0)
    a2 = (A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha

    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float32)
    a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float32)
    return b, a


def calculate_peaking_coeffs(center_hz: float, gain_db: float, q: float = 1.0, sample_rate: int = 48000) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate RBJ Audio EQ Cookbook Peaking EQ filter coefficients."""
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * center_hz / sample_rate
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / (2.0 * q)

    b0 = 1.0 + alpha * A
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / A

    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float32)
    a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float32)
    return b, a


def calculate_high_shelf_coeffs(cutoff_hz: float, gain_db: float, sample_rate: int = 48000) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate RBJ Audio EQ Cookbook High-Shelf filter coefficients."""
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * cutoff_hz / sample_rate
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt(2.0)
    sqrt_A = math.sqrt(A)

    b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha)
    b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha)
    a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha
    a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
    a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha

    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float32)
    a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float32)
    return b, a


def apply_soft_limiter(audio: np.ndarray, threshold: float = 0.8) -> np.ndarray:
    """
    Symmetric soft-knee clipping limiter.
    Signals below threshold (0.8 = -1.94 dBFS) remain 100% linear with zero coloration.
    Transients exceeding threshold are smoothly compressed using hyperbolic tangent saturation:
    f(x) = sgn(x) * [threshold + (1 - threshold) * tanh((|x| - threshold) / (1 - threshold))]
    Guaranteed strictly bounded within [-1.0, 1.0] for all finite inputs.
    """
    abs_audio = np.abs(audio)
    out = audio.copy()
    over_mask = abs_audio > threshold
    if np.any(over_mask):
        excess = abs_audio[over_mask] - threshold
        scale = 1.0 - threshold
        compressed = threshold + scale * np.tanh(excess / scale)
        out[over_mask] = np.sign(audio[over_mask]) * compressed
    return np.clip(out, -1.0, 1.0)


class BiquadFilter:
    """Direct Form II Transposed Biquad Filter with state preservation."""

    def __init__(self, channels: int = 2):
        self.channels = channels
        self.b = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.z1 = np.zeros(channels, dtype=np.float32)
        self.z2 = np.zeros(channels, dtype=np.float32)

    def set_coeffs(self, b: np.ndarray, a: np.ndarray):
        self.b = b
        self.a = a

    def process(self, x: np.ndarray) -> np.ndarray:
        """Process chunk x of shape (samples, channels)."""
        samples, channels = x.shape
        y = np.empty_like(x)
        b0, b1, b2 = self.b
        a1, a2 = self.a[1], self.a[2]

        for i in range(samples):
            xi = x[i]
            yi = b0 * xi + self.z1
            self.z1 = b1 * xi - a1 * yi + self.z2
            self.z2 = b2 * xi - a2 * yi
            y[i] = yi
        return y


class DynamicsCompressor:
    """
    Audio Dynamics Peak Compressor.
    Tames sudden volume spikes, explosions, and loud percussion.
    """

    def __init__(self, threshold_db: float = -16.0, knee_db: float = 24.0, ratio: float = 8.0,
                 attack_sec: float = 0.003, release_sec: float = 0.25, sample_rate: int = 48000):
        self.threshold_db = threshold_db
        self.knee_db = knee_db
        self.ratio = ratio
        self.attack_coeff = math.exp(-1.0 / (sample_rate * attack_sec))
        self.release_coeff = math.exp(-1.0 / (sample_rate * release_sec))
        self.envelope = 0.0

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Process audio array (samples, channels)."""
        # Peak amplitude across channels
        abs_val = np.max(np.abs(audio), axis=-1)
        output = np.empty_like(audio)

        for i in range(len(abs_val)):
            target = abs_val[i]
            if target > self.envelope:
                self.envelope = self.attack_coeff * self.envelope + (1.0 - self.attack_coeff) * target
            else:
                self.envelope = self.release_coeff * self.envelope + (1.0 - self.release_coeff) * target

            # Calculate dB gain reduction
            env_db = 20.0 * math.log10(max(1e-6, self.envelope))
            if env_db <= self.threshold_db - self.knee_db / 2.0:
                gain_db = 0.0
            elif env_db >= self.threshold_db + self.knee_db / 2.0:
                gain_db = (self.threshold_db + (env_db - self.threshold_db) / self.ratio) - env_db
            else:
                # Soft knee quadratic transition
                excess = env_db - self.threshold_db + self.knee_db / 2.0
                gain_db = ((1.0 / self.ratio - 1.0) * (excess ** 2)) / (2.0 * self.knee_db)

            gain = 10.0 ** (gain_db / 20.0)
            output[i] = audio[i] * gain

        return output


def compute_spectrum(audio: np.ndarray, num_bins: int = 16, sample_rate: int = 48000) -> Tuple[List[float], float, float]:
    """
    Compute 16-band normalized FFT spectrum and RMS/peak level.
    Returns: (frequency_bars [0..1], rms_level [0..1], peak_level [0..1])
    """
    if audio.size == 0:
        return [0.0] * num_bins, 0.0, 0.0

    # Convert to mono
    mono = audio.mean(axis=-1) if audio.ndim > 1 else audio
    n = len(mono)
    if n < 64:
        return [0.0] * num_bins, 0.0, 0.0

    # Calculate RMS and Peak
    peak = float(np.max(np.abs(mono)))
    rms = float(math.sqrt(np.mean(mono ** 2)))

    # Apply Hann window and FFT
    window = np.hanning(n)
    fft_data = np.abs(np.fft.rfft(mono * window))
    fft_freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)

    # Logarithmically spaced frequency boundaries from 40 Hz to 15 kHz
    bands = np.logspace(math.log10(40.0), math.log10(15000.0), num=num_bins + 1)
    bar_values = []

    for i in range(num_bins):
        low_f = bands[i]
        high_f = bands[i + 1]
        mask = (fft_freqs >= low_f) & (fft_freqs < high_f)
        if np.any(mask):
            val = float(np.mean(fft_data[mask]))
        else:
            val = 0.0
        # Boost upper frequencies for visual balance
        boost = 1.0 + (i / num_bins) * 1.5
        normalized = min(1.0, (val / (n * 0.15)) * boost)
        bar_values.append(round(normalized, 3))

    return bar_values, min(1.0, rms * 2.5), min(1.0, peak)
