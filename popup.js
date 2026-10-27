/**
 * Volume Booster Pro - Popup Interface Controller
 *
 * Handles user interactions, preset tuning, real-time Web Audio
 * parameter dispatch, and visualizer rendering.
 */

// Tuned DSP Presets
const PRESETS = {
  normal: {
    volume: 100,
    bass: 0.0,
    voice: 0.0,
    treble: 0.0,
    name: 'Normal'
  },
  balanced: {
    volume: 125,
    bass: 1.5,
    voice: 2.0,
    treble: 1.0,
    name: 'Balanced'
  },
  movie: {
    volume: 150,
    bass: 2.0,
    voice: 3.5,
    treble: 1.5,
    name: 'Movie'
  },
  music: {
    volume: 140,
    bass: 3.0,
    voice: 1.0,
    treble: 2.5,
    name: 'Music'
  },
  voice: {
    volume: 160,
    bass: -2.0,
    voice: 5.0,
    treble: 2.0,
    name: 'Voice'
  }
};

// Current active settings state
let currentSettings = { ...PRESETS.balanced };
let currentTab = null;
let isBoosting = false;
let isCurrentTabBoosted = false;
let visualizerPort = null;
let animFrameId = null;

// Peak meter physics
const barPeaks = new Array(16).fill(0);
const barPeakVelocities = new Array(16).fill(0);
let idleWavePhase = 0;

// DOM Elements
const statusPill = document.getElementById('statusPill');
const statusText = document.getElementById('statusText');
const tabBanner = document.getElementById('tabBanner');
const tabTitle = document.getElementById('tabTitle');
const restrictedNotice = document.getElementById('restrictedNotice');
const restrictedUrl = document.getElementById('restrictedUrl');
const toggleBoostBtn = document.getElementById('toggleBoostBtn');
const toggleBtnIcon = document.getElementById('toggleBtnIcon');
const toggleBtnText = document.getElementById('toggleBtnText');

// Volume Controls
const volumeSlider = document.getElementById('volumeSlider');
const volumePercent = document.getElementById('volumePercent');
const volumeDb = document.getElementById('volumeDb');
const highVolumeAlert = document.getElementById('highVolumeAlert');
const tickButtons = document.querySelectorAll('.tick-btn');

// Preset Controls
const presetChips = document.querySelectorAll('.preset-chip');
const activePresetBadge = document.getElementById('activePresetBadge');

// Equalizer Controls
const bassSlider = document.getElementById('bassSlider');
const bassValue = document.getElementById('bassValue');
const voiceSlider = document.getElementById('voiceSlider');
const voiceValue = document.getElementById('voiceValue');
const trebleSlider = document.getElementById('trebleSlider');
const trebleValue = document.getElementById('trebleValue');
const resetEqBtn = document.getElementById('resetEqBtn');
const resetAllBtn = document.getElementById('resetAllBtn');

// Visualizer Canvas & Meters
const visualizerCanvas = document.getElementById('visualizerCanvas');
const canvasCtx = visualizerCanvas.getContext('2d');
const levelFill = document.getElementById('levelFill');
const rmsText = document.getElementById('rmsText');

/**
 * Format Decibels with proper sign (+ / -)
 */
function formatDb(value) {
  const num = Number(value);
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(1)} dB`;
}

/**
 * Compute Decibels from linear volume percentage
 */
function calcVolumeDb(percentage) {
  const gain = Math.max(1.0, percentage / 100);
  const db = 20 * Math.log10(gain);
  return formatDb(db);
}

/**
 * Update range slider track background fill
 */
function updateSliderTrack(slider, min, max, colorA = '#00f0ff', colorB = '#a855f7') {
  const val = Number(slider.value);
  const percent = ((val - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(to right, ${colorA} 0%, ${colorB} ${percent}%, rgba(255,255,255,0.08) ${percent}%, rgba(255,255,255,0.08) 100%)`;
}

/**
 * Update UI controls to reflect state
 */
function syncUiState() {
  // Volume controls
  volumeSlider.value = currentSettings.volume;
  volumePercent.textContent = `${Math.round(currentSettings.volume)}%`;
  volumeDb.textContent = calcVolumeDb(currentSettings.volume);
  updateSliderTrack(volumeSlider, 100, 300);

  // High amplification alert (>200%)
  if (currentSettings.volume > 200) {
    highVolumeAlert.classList.remove('hidden');
  } else {
    highVolumeAlert.classList.add('hidden');
  }

  // Active snap tick buttons
  tickButtons.forEach((btn) => {
    const tickVol = Number(btn.getAttribute('data-vol'));
    if (Math.abs(tickVol - currentSettings.volume) < 2) {
      btn.classList.add('active-tick');
    } else {
      btn.classList.remove('active-tick');
    }
  });

  // Equalizer controls
  bassSlider.value = currentSettings.bass;
  bassValue.textContent = formatDb(currentSettings.bass);
  updateSliderTrack(bassSlider, -6, 6, '#8b5cf6', '#00f0ff');

  voiceSlider.value = currentSettings.voice;
  voiceValue.textContent = formatDb(currentSettings.voice);
  updateSliderTrack(voiceSlider, -4, 6, '#8b5cf6', '#00f0ff');

  trebleSlider.value = currentSettings.treble;
  trebleValue.textContent = formatDb(currentSettings.treble);
  updateSliderTrack(trebleSlider, -6, 6, '#8b5cf6', '#00f0ff');

  // Active Preset Badge & Chips
  const activePresetKey = currentSettings.preset || 'custom';
  activePresetBadge.textContent = activePresetKey.charAt(0).toUpperCase() + activePresetKey.slice(1);

  presetChips.forEach((chip) => {
    if (chip.getAttribute('data-preset') === activePresetKey) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });

  // Master Boost button & Status Pill
  if (isCurrentTabBoosted) {
    statusPill.className = 'status-pill active';
    statusText.textContent = 'BOOSTING';
    toggleBoostBtn.className = 'btn btn-boost active-boosting';
    toggleBtnIcon.textContent = '⏹️';
    toggleBtnText.textContent = 'STOP BOOST';
  } else {
    statusPill.className = 'status-pill inactive';
    statusText.textContent = 'OFF';
    toggleBoostBtn.className = 'btn btn-boost';
    toggleBtnIcon.textContent = '⚡';
    toggleBtnText.textContent = 'START BOOST';
  }
}

/**
 * Send updated settings to service worker and offscreen processor
 */
function dispatchSettingsUpdate() {
  chrome.runtime.sendMessage({
    type: 'UPDATE_SETTINGS',
    settings: currentSettings
  }).catch(() => {});
}

/**
 * Apply a preset by name
 */
function applyPreset(presetKey) {
  const preset = PRESETS[presetKey];
  if (!preset) return;

  currentSettings = {
    ...currentSettings,
    volume: preset.volume,
    bass: preset.bass,
    voice: preset.voice,
    treble: preset.treble,
    preset: presetKey
  };

  syncUiState();
  dispatchSettingsUpdate();
}

/**
 * Check if the given URL is restricted by Chrome security policy
 */
function isRestrictedUrl(url) {
  if (!url) return true;
  const restrictedProtocols = ['chrome:', 'edge:', 'devtools:', 'chrome-extension:', 'about:', 'view-source:'];
  const restrictedDomains = ['chromewebstore.google.com', 'chrome.google.com/webstore'];

  try {
    const parsed = new URL(url);
    if (restrictedProtocols.includes(parsed.protocol)) return true;
    if (restrictedDomains.some((d) => parsed.hostname.includes(d))) return true;
  } catch (e) {
    return true;
  }
  return false;
}

/**
 * Connect to offscreen document port for real-time visualizer data
 */
function connectVisualizerStream() {
  if (visualizerPort) {
    try { visualizerPort.disconnect(); } catch (e) {}
    visualizerPort = null;
  }

  try {
    visualizerPort = chrome.runtime.connect({ name: 'visualizer_stream' });

    visualizerPort.onMessage.addListener((msg) => {
      if (msg.type === 'VIZ_DATA') {
        renderVisualizer(msg.bins, msg.rms, msg.isAudioPlaying);
      }
    });

    visualizerPort.onDisconnect.addListener(() => {
      visualizerPort = null;
    });
  } catch (e) {
    visualizerPort = null;
  }
}

/**
 * Render spectrum visualizer on Canvas
 */
function renderVisualizer(bins = null, rms = 0, isAudioPlaying = false) {
  const width = visualizerCanvas.width;
  const height = visualizerCanvas.height;

  canvasCtx.clearRect(0, 0, width, height);

  const numBars = 16;
  const spacing = 4;
  const totalSpacing = spacing * (numBars - 1);
  const barWidth = (width - 16 - totalSpacing) / numBars;
  const startX = 8;

  // If tab is not boosted or no audio is actively flowing, render idle wave
  if (!isCurrentTabBoosted || !isAudioPlaying || !bins) {
    idleWavePhase += 0.04;
    canvasCtx.beginPath();
    canvasCtx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
    canvasCtx.lineWidth = 1.5;

    for (let x = 0; x < width; x += 2) {
      const y = height / 2 + Math.sin(x * 0.05 + idleWavePhase) * 6 * Math.sin(x / width * Math.PI);
      if (x === 0) canvasCtx.moveTo(x, y);
      else canvasCtx.lineTo(x, y);
    }
    canvasCtx.stroke();

    // Subtle idle baseline bars
    for (let i = 0; i < numBars; i++) {
      const x = startX + i * (barWidth + spacing);
      const idleHeight = 3 + Math.sin(idleWavePhase + i * 0.4) * 2;
      const y = height - idleHeight;

      canvasCtx.fillStyle = 'rgba(255, 255, 255, 0.08)';
      canvasCtx.fillRect(x, y, barWidth, idleHeight);
    }

    levelFill.style.width = '0%';
    rmsText.textContent = '-inf dB';
    return;
  }

  // Update VU meter fill & text
  const levelPercent = Math.min(100, Math.round(rms * 100));
  levelFill.style.width = `${levelPercent}%`;
  const rmsDb = rms > 0.001 ? (20 * Math.log10(rms)).toFixed(1) : '-inf';
  rmsText.textContent = `${rmsDb} dB`;

  // Gradient for bars
  const barGrad = canvasCtx.createLinearGradient(0, height, 0, 0);
  barGrad.addColorStop(0, '#00f0ff');
  barGrad.addColorStop(0.65, '#a855f7');
  barGrad.addColorStop(1, '#ec4899');

  // Draw 16 frequency bars with peak decay
  for (let i = 0; i < numBars; i++) {
    const rawVal = bins[i] || 0;
    // Boost visual punch of upper bands
    const scaledVal = Math.min(1.0, rawVal * (1.0 + (i / numBars) * 0.8));
    const barHeight = Math.max(3, scaledVal * (height - 6));
    const x = startX + i * (barWidth + spacing);
    const y = height - barHeight;

    // Draw main frequency bar
    canvasCtx.fillStyle = barGrad;
    canvasCtx.fillRect(x, y, barWidth, barHeight);

    // Peak cap physics (gravity drop)
    if (barHeight >= barPeaks[i]) {
      barPeaks[i] = barHeight;
      barPeakVelocities[i] = 0;
    } else {
      barPeakVelocities[i] += 0.25;
      barPeaks[i] = Math.max(0, barPeaks[i] - barPeakVelocities[i]);
    }

    // Draw peak cap dot
    const peakY = height - barPeaks[i] - 2;
    if (peakY >= 0 && peakY < height) {
      canvasCtx.fillStyle = '#ffffff';
      canvasCtx.fillRect(x, peakY, barWidth, 2);
    }
  }
}

/**
 * Idle animation loop for when audio is not streaming
 */
function startIdleAnimationLoop() {
  function loop() {
    if (!visualizerPort || !isCurrentTabBoosted) {
      renderVisualizer(null, 0, false);
    }
    animFrameId = requestAnimationFrame(loop);
  }
  loop();
}

/**
 * Initialize Popup and load settings
 */
async function initializePopup() {
  // Query active tab in the current window
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tabs[0] || null;

  if (!currentTab) {
    tabTitle.textContent = 'No active tab found';
    toggleBoostBtn.disabled = true;
    return;
  }

  // Display tab title
  tabTitle.textContent = currentTab.title || currentTab.url || 'Active Tab';

  // Check for restricted URLs (chrome://, webstore, etc.)
  if (isRestrictedUrl(currentTab.url)) {
    restrictedNotice.classList.remove('hidden');
    if (restrictedUrl) {
      try {
        restrictedUrl.textContent = new URL(currentTab.url).protocol + '//';
      } catch (e) {
        restrictedUrl.textContent = 'chrome://';
      }
    }
    toggleBoostBtn.disabled = true;
    toggleBoostBtn.title = 'Cannot capture audio on internal browser pages.';
  } else {
    restrictedNotice.classList.add('hidden');
    toggleBoostBtn.disabled = false;
  }

  // Query background service worker for current state
  chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response) => {
    if (response && response.state) {
      const state = response.state;
      isBoosting = state.isBoosting;
      isCurrentTabBoosted = isBoosting && state.boostingTabId === currentTab.id;

      if (state.settings) {
        currentSettings = { ...currentSettings, ...state.settings };
      }

      // If another tab is boosted, notify the user
      if (isBoosting && state.boostingTabId !== currentTab.id) {
        tabTitle.textContent = `Boosted Tab: ${state.boostingTabTitle || 'Other Tab'}`;
      }
    }

    syncUiState();
    connectVisualizerStream();
    startIdleAnimationLoop();
  });
}

// -----------------------------------------------------------------------------
// Event Listeners
// -----------------------------------------------------------------------------

// Toggle Boost Button
toggleBoostBtn.addEventListener('click', async () => {
  if (!currentTab || isRestrictedUrl(currentTab.url)) return;

  toggleBoostBtn.disabled = true;

  try {
    if (isCurrentTabBoosted) {
      // Stop Boost
      await new Promise((resolve) => {
        chrome.runtime.sendMessage({ type: 'STOP_BOOST' }, resolve);
      });
      isCurrentTabBoosted = false;
      isBoosting = false;
    } else {
      // Start Boost: Obtain streamId via user gesture in popup context
      const streamId = await new Promise((resolve, reject) => {
        chrome.tabCapture.getMediaStreamId({ targetTabId: currentTab.id }, (id) => {
          if (chrome.runtime.lastError) {
            return reject(new Error(chrome.runtime.lastError.message));
          }
          if (!id) {
            return reject(new Error('Failed to get stream ID for this tab.'));
          }
          resolve(id);
        });
      });

      // Send to background coordinator
      const result = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          {
            type: 'START_BOOST',
            tabId: currentTab.id,
            streamId: streamId,
            tabTitle: currentTab.title
          },
          (res) => {
            if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
            resolve(res);
          }
        );
      });

      if (result && result.success) {
        isCurrentTabBoosted = true;
        isBoosting = true;
        connectVisualizerStream();
      } else {
        alert(result ? result.error : 'Failed to start volume booster.');
      }
    }
  } catch (err) {
    console.error('Error toggling volume boost:', err);
    alert(`Could not boost tab: ${err.message}`);
  } finally {
    toggleBoostBtn.disabled = false;
    syncUiState();
  }
});

// Volume Slider
volumeSlider.addEventListener('input', (e) => {
  const vol = Number(e.target.value);
  currentSettings.volume = vol;
  currentSettings.preset = 'custom';
  syncUiState();
  dispatchSettingsUpdate();
});

// Quick Volume Snap Ticks
tickButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const vol = Number(btn.getAttribute('data-vol'));
    currentSettings.volume = vol;
    currentSettings.preset = 'custom';
    syncUiState();
    dispatchSettingsUpdate();
  });
});

// Preset Chips
presetChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    const presetKey = chip.getAttribute('data-preset');
    applyPreset(presetKey);
  });
});

// EQ Sliders
bassSlider.addEventListener('input', (e) => {
  currentSettings.bass = Number(e.target.value);
  currentSettings.preset = 'custom';
  syncUiState();
  dispatchSettingsUpdate();
});

voiceSlider.addEventListener('input', (e) => {
  currentSettings.voice = Number(e.target.value);
  currentSettings.preset = 'custom';
  syncUiState();
  dispatchSettingsUpdate();
});

trebleSlider.addEventListener('input', (e) => {
  currentSettings.treble = Number(e.target.value);
  currentSettings.preset = 'custom';
  syncUiState();
  dispatchSettingsUpdate();
});

// Reset EQ Button
resetEqBtn.addEventListener('click', () => {
  currentSettings.bass = 0.0;
  currentSettings.voice = 0.0;
  currentSettings.treble = 0.0;
  currentSettings.preset = 'custom';
  syncUiState();
  dispatchSettingsUpdate();
});

// Reset All Defaults Button
resetAllBtn.addEventListener('click', () => {
  applyPreset('balanced');
});

// Cleanup when popup closes
window.addEventListener('unload', () => {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId);
  }
  if (visualizerPort) {
    visualizerPort.disconnect();
  }
});

// Run initialization
document.addEventListener('DOMContentLoaded', initializePopup);
