# Volume Booster Pro — Windows System-Wide Audio Enhancer & DSP Equalizer

[![Windows 10 / 11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)]()
[![Equalizer APO](https://img.shields.io/badge/Audio%20Engine-Equalizer%20APO%20%26%20WASAPI-purple.svg)]()
[![Python & Qt 6](https://img.shields.io/badge/GUI-PySide6%20%28Qt%206%29-00f0ff.svg)]()
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Volume Booster Pro** is a high-performance Windows desktop application designed to amplify and equalize audio across the **entire operating system**. It enhances sound from **Google Chrome, YouTube, Spotify, VLC Media Player, Netflix, Discord, PC games, and Windows system audio** with crystal-clear vocal articulation, controlled low-end, and peak protection.

---

## 1. System-Wide Architecture

### The Windows Audio Engineering Challenge
In Windows Vista through Windows 11, the Windows Audio Engine (`audiodg.exe`) mixes audio from all applications before sending it to the sound driver/DAC. 
> [!IMPORTANT]
> Standard **WASAPI Loopback Capture** can only *listen* to the audio output; it **cannot** intercept, modify, or boost system sound in-place on that same endpoint without either an **Audio Processing Object (APO)** or a **Virtual Audio Device**.

To solve this properly, Volume Booster Pro implements a **Dual-Engine Architecture**:

```
                              [ Windows Applications ]
                  (Chrome, Spotify, VLC, Games, Netflix, Discord)
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         [ Engine A: Equalizer APO ]              [ Engine B: Virtual Cable ]
     (Direct audiodg.exe LFX/GFX Filter)       (VB-CABLE / Virtual Audio Device)
                    │                                         │
                    │ Zero Latency                            ▼
                    │ Zero CPU Overhead          [ Low-Latency Capture Stream ]
                    │ Real-Time Profile Sync                  │
                    │                                         ▼
                    │                         [ Real-Time Vector DSP Engine ]
                    │                          ├─ 3-Band Parametric Biquad EQ
                    │                          ├─ 100% - 300% Master Gain Stage
                    │                          ├─ Dynamics Peak Compressor
                    │                          └─ Tanh Soft-Knee Limiter
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         ▼
                       [ Hardware Output Endpoint ]
                  (Speakers / Headphones / Realtek DAC)
                                         │
                                         ▼
                       [ Live WASAPI Audio Monitor ]
                                         │
                                         ▼
             [ Real-Time 16-Band Spectrum Visualizer & VU Meter ]
```

### Engine A: Equalizer APO Native System Engine (Recommended)
- **Zero latency, zero CPU overhead, no virtual drivers required.**
- Volume Booster Pro dynamically manages `VolumeBoosterPro.txt` and links it into Equalizer APO's `config.txt`.
- Safe atomic updates: Every volume or EQ adjustment updates the audio filter in real-time inside `audiodg.exe` without dropping a single sample.
- Built-in Setup & Diagnostics dialog guides you through 1-click device configuration.

### Engine B: Virtual Audio Device / Passthrough Engine
- For systems without Equalizer APO: integrates seamlessly with VB-CABLE or Virtual Audio Cable.
- Windows Default Output is set to the Virtual Cable; Volume Booster Pro captures the stream, processes it with its real-time DSP pipeline, and outputs boosted audio to physical speakers.
- Built-in feedback-loop protector guarantees input and output devices can never be the same.

---

## 2. Audio DSP Pipeline & Signal Staging

1. **3-Band Parametric Equalizer (Biquad Direct Form II Transposed):**
   - **Bass (150 Hz Low-Shelf):** `-6 dB` to `+6 dB` — Warm, rich low-end without speaker rattle.
   - **Voice Clarity (2.2 kHz Peaking, Q=1.0):** `-4 dB` to `+6 dB` — Dialogue clarity for movies, podcasts, and calls.
   - **Treble (7.0 kHz High-Shelf):** `-6 dB` to `+6 dB` — Air, presence, and consonant articulation.
2. **Master Amplification Stage:**
   - Smooth gain scaling from **100% to 300%** (`+0.0 dB` to `+9.54 dB`).
   - Default sweet spot: **Balanced at 125%** (`+1.94 dB`).
3. **Dynamics Peak Compressor:**
   - Threshold: `-16 dB`, Knee: `24 dB`, Ratio: `8:1`, Attack: `3 ms`, Release: `250 ms`.
   - Clamps sudden explosions, transients, and loud spikes.
4. **Symmetric Soft-Knee Tanh Limiter:**
   - Signals below `0.8` (`-1.94 dBFS`) remain 100% linear with zero coloration.
   - Peaks exceeding `0.8` are smoothly saturated using hyperbolic tangent compression:
     $$f(x) = \text{sgn}(x) \cdot \left[ 0.8 + 0.2 \cdot \tanh\left(\frac{|x| - 0.8}{0.2}\right) \right]$$
   - Mathematically guarantees audio is strictly bounded within `[-1.0, 1.0]` (0 dBFS), completely eliminating harsh digital square-wave clipping.

---

## 3. Tuned Acoustic Presets

| Preset | Volume | Bass (150 Hz) | Voice (2.2 kHz) | Treble (7.0 kHz) | Tuning Target |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Normal** | `100%` (`0.0 dB`) | `0.0 dB` | `0.0 dB` | `0.0 dB` | Bit-perfect flat reference sound. |
| **Balanced** *(Default)* | **`125%`** (`+1.9 dB`) | **`+1.5 dB`** | **`+2.0 dB`** | **`+1.0 dB`** | Recommended laptop speaker sweet spot. Warm bass, articulate speech. |
| **Bass Boost** | `140%` (`+2.9 dB`) | `+4.5 dB` | `+1.0 dB` | `+1.5 dB` | Deep low-end punch for EDM, hip-hop, and action scenes. |
| **Movie** | `150%` (`+3.5 dB`) | `+2.0 dB` | `+3.5 dB` | `+1.5 dB` | Dialogue intelligibility with cinematic presence. |
| **Voice** | `160%` (`+4.1 dB`) | `-2.0 dB` | `+5.0 dB` | `+2.0 dB` | Cuts muddy room boom; sharpens podcasts, YouTube tutorials, and Discord voice. |

---

## 4. How to Run

### Option A: 1-Click Batch Launcher (Quickest)
Double-click [`run_app.bat`](file:///c:/myproject/volume%20booster/run_app.bat) in the project root folder.

### Option B: Run from Python Source
```bash
python main.py
```

### Option C: Run Standalone Executable
```bash
dist\VolumeBoosterPro\VolumeBoosterPro.exe
```

---

## 5. Equalizer APO Setup (3-Minute Guide)

For native kernel-level zero-latency system enhancement:
1. Open Volume Booster Pro and click the **APO: SETUP REQUIRED** badge or button.
2. Click **Download Equalizer APO** (opens official [SourceForge](https://sourceforge.net/projects/equalizerapo/)).
3. Run the installer. In the **Configurator** window, check the box next to your audio output device (e.g. `Speakers (Realtek(R) Audio)`).
4. Restart your Windows PC.
5. Launch Volume Booster Pro — the badge will turn **EQUALIZER APO: ACTIVE** and all system audio will be amplified in real-time!

---

## 6. Windows System Integration

- **Minimize to Tray:** Minimizes to the Windows taskbar notification area to stay out of your way.
- **System Tray Menu:** Right-click the tray icon to switch presets, adjust volume, toggle Master Bypass, or restore the window.
- **Start with Windows:** Easily toggled via checkbox (manages `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- **Device Switcher:** Automatically enumerates and switches between Speakers, Headphones, and external audio DACs.
- **Settings Persistence:** Remembers your volume, custom EQ curves, and active device in `%LOCALAPPDATA%\VolumeBoosterPro\settings.json`.

---

## 7. Speaker & Hearing Safety Notice

- **No Software Guarantees Hardware Safety:** While our dynamics compressor and soft-limiter prevent digital distortion and square-wave clipping, **software cannot physically guarantee speaker hardware protection against continuous thermal overload**.
- **Listen Responsibly:** High amplification (>200%) should be used cautiously on thin laptop speakers. If audio starts sounding strained, lower the gain to keep sound comfortable.
