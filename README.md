# Volume Booster Pro — Premium Chrome Extension

[![Manifest V3](https://img.shields.io/badge/Manifest-V3-cyan.svg)](https://developer.chrome.com/docs/extensions/mv3/intro/)
[![Web Audio API](https://img.shields.io/badge/Web%20Audio%20DSP-Engine-purple.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Volume Booster Pro** is a high-fidelity audio amplification and DSP equalizer extension built with Manifest V3 for Google Chrome on Windows 10 & 11. Engineered specifically for laptop speakers and headphones, it boosts dialogue clarity, rich dynamics, and maximum loudness (up to **300%**) on YouTube, Netflix, Spotify Web, podcasts, and video calls without harsh digital distortion.

---

## Key Features

- ⚡ **300% Smooth Amplification:** Boost tab audio from 100% to 300% with live percentage and decibel (`+0.0 dB` to `+9.5 dB`) readouts.
- 🎚️ **3-Band Precision Equalizer:**
  - **Bass (150 Hz Low-Shelf):** `-6 dB` to `+6 dB` — Warm low-end without speaker rattle.
  - **Voice Clarity (2.2 kHz Peaking):** `-4 dB` to `+6 dB` — Crisp vocal intelligibility for movies and podcasts.
  - **Treble (7.0 kHz High-Shelf):** `-6 dB` to `+6 dB` — Sparkling presence and consonant articulation.
- 🎛️ **5 Tuned DSP Presets:**
  - **Normal (100%):** Completely flat response, zero coloration.
  - **Balanced (125% - Default):** Ideal sweet spot for laptop speakers — warm bass, articulate vocals, comfortable lift.
  - **Movie (150%):** Dialogue-forward tuning with cinematic ambient presence for films and streams.
  - **Music (140%):** Vibrant V-curve response with punchy lows and sparkling highs.
  - **Voice (160%):** Cuts muddy boominess and emphasizes spoken frequencies for podcasts and tutorials.
- 🛡️ **Dual-Stage Peak Protection:**
  - **DynamicsCompressorNode:** Automatically clamps sudden transients and explosions before they stress compact speakers.
  - **Hyperbolic Tangent Soft Limiter:** Smooth `tanh` saturation wave-shaper that eliminates harsh square-wave digital clipping.
  - **Click-Free Transitions:** Smooth 35ms exponential parameter ramps prevent pops when moving sliders.
- 📊 **Real-Time Spectrum Visualizer:** 16-band gradient visualizer with falling peak caps and stereo VU level meter.
- 💾 **Persistent Settings:** Remembers your volume, custom EQ bands, and active preset via `chrome.storage.local`.
- 🔌 **Instant Start/Stop & Auto Cleanup:** Automatically restores original unmuted tab audio when stopped or when tabs close.

---

## Audio DSP Architecture

```
[ Captured Tab Audio ]
          │ (chrome.tabCapture.getMediaStreamId)
          ▼
[ Offscreen Document: getUserMedia ]
          │
          ▼
[ MediaStreamAudioSourceNode ]
          │
          ▼
[ Bass Filter (150 Hz Low-Shelf, ±6 dB) ]
          │
          ▼
[ Voice Clarity Filter (2.2 kHz Peaking, Q=1.0, -4 to +6 dB) ]
          │
          ▼
[ Treble Filter (7.0 kHz High-Shelf, ±6 dB) ]
          │
          ▼
[ Master GainNode (1.0x to 3.0x Amplification) ]
          │
          ▼
[ DynamicsCompressorNode ]
  ├─ Threshold: -16 dB
  ├─ Knee: 24 dB
  ├─ Ratio: 8:1
  ├─ Attack: 3 ms
  └─ Release: 250 ms
          │
          ▼
[ Soft Limiter WaveShaperNode ]
  ├─ Curve: f(x) = tanh(1.25x) / tanh(1.25)
  └─ Oversampling: 4x
          │
          ├───────────────────────────────┐
          ▼                               ▼
[ AnalyserNode (FFT 64) ]        [ AudioContext.destination ]
  └─ Streams to Popup               └─ Output to Laptop Speakers/Headphones
     Visualizer & VU Meter
```

---

## Project Structure

```
volume-booster-pro/
├── manifest.json          # Manifest V3 extension configuration
├── popup.html             # Glassmorphic dark cyber UI popup
├── popup.css              # Styling, animations, custom sliders & visualizer
├── popup.js               # UI interaction, presets, live settings & visualizer loop
├── service-worker.js      # Background coordinator, tab lifecycle & storage
├── offscreen.html         # Offscreen Document host for Web Audio API
├── offscreen.js           # Web Audio DSP pipeline, filters, compressor, soft-limiter
├── generate-icons.js      # Icon generation script
├── test-extension.js      # Automated unit tests for DSP math & manifest validation
├── icons/                 # High-DPI extension icons
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
├── volume-booster-pro.zip # Ready-to-distribute ZIP package
└── README.md              # Documentation and user manual
```

---

## Installation Guide (Step-by-Step)

Follow these simple steps to load **Volume Booster Pro** into Google Chrome:

### 1. Open Chrome Extensions
- Open Google Chrome.
- In the address bar, type `chrome://extensions` and press **Enter**.

### 2. Enable Developer Mode
- In the top-right corner of the Extensions page, toggle the **Developer mode** switch to **ON**.

### 3. Load the Unpacked Extension
- Click the **Load unpacked** button in the top-left toolbar.
- In the file picker dialog, navigate to and select the folder:
  ```
  c:\myproject\volume booster
  ```
- Click **Select Folder**.

### 4. Pin to Toolbar
- Click the puzzle icon (Extensions menu) in the Chrome toolbar.
- Find **Volume Booster Pro** and click the **Pin** icon so it remains easily accessible.

---

## How to Use

1. **Open Any Media Tab:** Navigate to YouTube, Netflix, Spotify, or any website playing sound.
2. **Open Volume Booster Pro:** Click the extension icon in your Chrome toolbar.
3. **Start Amplification:** Click the **⚡ START BOOST** button.
   - The status pill will turn **BOOSTING**.
   - The real-time spectrum visualizer will dance to the audio.
   - The extension badge will display the live boost level (e.g. `125%`).
4. **Choose a Preset or Customize:**
   - Tap **Balanced** (default), **Movie**, **Music**, or **Voice**.
   - Or drag the **Amplification Slider** anywhere between **100%** and **300%**.
   - Fine-tune the **Bass**, **Voice**, and **Treble** sliders to match your laptop speakers.
5. **Stop Boost:** Click **⏹️ STOP BOOST** at any time to instantly restore normal unmuted tab audio.

---

## Safety and Speaker Protection Philosophy

- **No Software Magic Bullet:** While our dual-stage dynamics compressor and tanh soft-limiter effectively eliminate digital distortion and square-wave spikes, **no software can guarantee physical speaker hardware protection against thermal overload or excessive mechanical excursion**.
- **Listen Responsibly:** High amplification (>200%) should be used thoughtfully, especially on ultra-thin laptop speakers. If audio starts sounding raspy or muffled, lower the gain to keep sound comfortable and clear.

---

## Known Limitations

1. **Browser Tab Scope:** Chrome's `tabCapture` API captures audio originating within the active browser tab only. It does not amplify Windows desktop applications (e.g. Spotify desktop app, Zoom desktop client, or PC system sounds).
2. **Internal Chrome Pages:** For browser security, Chrome strictly disallows extensions from capturing audio on `chrome://`, `chrome-extension://`, `devtools://`, and `chromewebstore.google.com` pages. The extension gracefully detects these pages and displays an informative notification.
3. **Single Active Tab Capture:** To prevent hardware feedback loops and excessive CPU overhead, one browser tab is boosted at a time. Switching to another tab allows you to transfer boost seamlessly.

---

## Verification & Testing

To run the automated DSP and manifest verification tests:

```bash
node test-extension.js
```

All 5 core test suites validate:
- Manifest V3 structure and permission requirements
- Icon integrity across all 4 resolutions
- Soft-clipping limiter symmetry and monotonicity
- Preset frequency boundaries and default gains
- Decibel calculation precision
