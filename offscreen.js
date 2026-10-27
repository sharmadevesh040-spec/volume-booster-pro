/**
 * Volume Booster Pro - Offscreen Web Audio DSP Processing Engine
 *
 * Runs inside the Manifest V3 Offscreen Document to process captured
 * browser tab audio with Web Audio API.
 *
 * Signal Chain:
 * MediaStream -> MediaStreamSource -> Bass Filter (LowShelf)
 *   -> Voice Filter (Peaking) -> Treble Filter (HighShelf)
 *   -> GainNode (100% to 300%) -> DynamicsCompressorNode
 *   -> SoftLimiter (WaveShaper) -> AnalyserNode -> AudioContext.destination
 */

let audioContext = null;
let mediaStream = null;
let sourceNode = null;
let bassFilter = null;
let voiceFilter = null;
let trebleFilter = null;
let gainNode = null;
let compressor = null;
let limiter = null;
let analyser = null;
let activeTabId = null;

// Connected ports for visualizer streaming (active while popup is open)
const activeVisualizerPorts = new Set();
let vizAnimationFrameId = null;

/**
 * Generate a soft-clipping curve using hyperbolic tangent.
 * Provides analog-style saturation and avoids harsh digital square-wave clipping.
 */
function createSoftClipCurve(samples = 4096) {
  const curve = new Float32Array(samples);
  const drive = 1.25;
  const norm = Math.tanh(drive);
  for (let i = 0; i < samples; ++i) {
    const x = (i * 2) / samples - 1;
    curve[i] = Math.tanh(x * drive) / norm;
  }
  return curve;
}

/**
 * Clean up existing audio nodes and release media tracks.
 * Guarantees that audio streams are never connected twice.
 */
function cleanupAudio() {
  if (vizAnimationFrameId) {
    cancelAnimationFrame(vizAnimationFrameId);
    vizAnimationFrameId = null;
  }

  if (mediaStream) {
    try {
      mediaStream.getTracks().forEach((track) => {
        track.onended = null;
        track.stop();
      });
    } catch (e) {
      console.warn('[Offscreen] Error stopping media tracks:', e);
    }
    mediaStream = null;
  }

  if (sourceNode) {
    try {
      sourceNode.disconnect();
    } catch (e) {}
    sourceNode = null;
  }

  if (bassFilter) {
    try { bassFilter.disconnect(); } catch (e) {}
    bassFilter = null;
  }

  if (voiceFilter) {
    try { voiceFilter.disconnect(); } catch (e) {}
    voiceFilter = null;
  }

  if (trebleFilter) {
    try { trebleFilter.disconnect(); } catch (e) {}
    trebleFilter = null;
  }

  if (gainNode) {
    try { gainNode.disconnect(); } catch (e) {}
    gainNode = null;
  }

  if (compressor) {
    try { compressor.disconnect(); } catch (e) {}
    compressor = null;
  }

  if (limiter) {
    try { limiter.disconnect(); } catch (e) {}
    limiter = null;
  }

  if (analyser) {
    try { analyser.disconnect(); } catch (e) {}
    analyser = null;
  }

  if (audioContext && audioContext.state !== 'closed') {
    try {
      audioContext.close();
    } catch (e) {
      console.warn('[Offscreen] Error closing audioContext:', e);
    }
    audioContext = null;
  }

  activeTabId = null;
}

/**
 * Start boosting a tab stream with the given streamId and settings.
 */
async function startAudioProcessing(streamId, tabId, settings) {
  // Always clean up any existing stream first to prevent double-connections
  cleanupAudio();

  try {
    // 1. Obtain captured tab MediaStream via getUserMedia
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId
        }
      },
      video: false
    });

    activeTabId = tabId;

    // Handle stream termination (e.g., tab closed or navigated)
    const audioTrack = mediaStream.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.onended = () => {
        console.log('[Offscreen] Media stream track ended for tab', tabId);
        cleanupAudio();
        chrome.runtime.sendMessage({
          type: 'STREAM_ENDED',
          tabId: tabId
        }).catch(() => {});
      };
    }

    // 2. Initialize Web Audio Context
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContextClass({ latencyHint: 'interactive' });

    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    // 3. Create DSP nodes
    sourceNode = audioContext.createMediaStreamSource(mediaStream);

    // Bass Filter: Low-shelf filter at 150 Hz
    bassFilter = audioContext.createBiquadFilter();
    bassFilter.type = 'lowshelf';
    bassFilter.frequency.setValueAtTime(150, audioContext.currentTime);
    const initialBass = typeof settings.bass === 'number' ? settings.bass : 1.5;
    bassFilter.gain.setValueAtTime(initialBass, audioContext.currentTime);

    // Voice Clarity Filter: Peaking filter at 2200 Hz with Q=1.0 (dialogue intelligibility)
    voiceFilter = audioContext.createBiquadFilter();
    voiceFilter.type = 'peaking';
    voiceFilter.frequency.setValueAtTime(2200, audioContext.currentTime);
    voiceFilter.Q.setValueAtTime(1.0, audioContext.currentTime);
    const initialVoice = typeof settings.voice === 'number' ? settings.voice : 2.0;
    voiceFilter.gain.setValueAtTime(initialVoice, audioContext.currentTime);

    // Treble Filter: High-shelf filter at 7000 Hz (presence & air)
    trebleFilter = audioContext.createBiquadFilter();
    trebleFilter.type = 'highshelf';
    trebleFilter.frequency.setValueAtTime(7000, audioContext.currentTime);
    const initialTreble = typeof settings.treble === 'number' ? settings.treble : 1.0;
    trebleFilter.gain.setValueAtTime(initialTreble, audioContext.currentTime);

    // Master Gain Node: volume is in percentage (100% - 300%) -> gain (1.0 - 3.0)
    gainNode = audioContext.createGain();
    const initialVolume = typeof settings.volume === 'number' ? settings.volume : 125;
    gainNode.gain.setValueAtTime(initialVolume / 100, audioContext.currentTime);

    // Dynamics Compressor Node: controls sudden volume spikes, explosions, & loud transients
    compressor = audioContext.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-16, audioContext.currentTime); // dB
    compressor.knee.setValueAtTime(24, audioContext.currentTime); // soft transition knee
    compressor.ratio.setValueAtTime(8, audioContext.currentTime); // 8:1 compression ratio
    compressor.attack.setValueAtTime(0.003, audioContext.currentTime); // 3ms fast attack
    compressor.release.setValueAtTime(0.25, audioContext.currentTime); // 250ms smooth release

    // Soft Limiter (WaveShaper): smooth saturation curve to eliminate harsh digital clipping
    limiter = audioContext.createWaveShaper();
    limiter.curve = createSoftClipCurve(4096);
    limiter.oversample = '4x';

    // Analyser Node: Real-time frequency analysis for popup visualizer
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 64; // Yields 32 frequency bins
    analyser.smoothingTimeConstant = 0.75;

    // 4. Connect the complete signal graph:
    // source -> bass -> voice -> treble -> gain -> compressor -> limiter -> analyser -> destination
    sourceNode.connect(bassFilter);
    bassFilter.connect(voiceFilter);
    voiceFilter.connect(trebleFilter);
    trebleFilter.connect(gainNode);
    gainNode.connect(compressor);
    compressor.connect(limiter);
    limiter.connect(analyser);
    analyser.connect(audioContext.destination);

    // 5. Start visualizer loop if ports are connected
    if (activeVisualizerPorts.size > 0) {
      startVisualizerStream();
    }

    console.log('[Offscreen] Web Audio DSP chain successfully initialized for tab', tabId);
    return { success: true };
  } catch (err) {
    console.error('[Offscreen] Failed to start audio processing:', err);
    cleanupAudio();
    throw err;
  }
}

/**
 * Apply live audio parameter changes smoothly without restarting the stream.
 */
function updateAudioSettings(settings) {
  if (!audioContext || audioContext.state === 'closed') {
    return;
  }

  const now = audioContext.currentTime;
  const timeConstant = 0.035; // ~35ms smooth exponential transition

  // Update volume gain
  if (gainNode && typeof settings.volume === 'number') {
    const targetGain = Math.max(1.0, Math.min(3.0, settings.volume / 100));
    gainNode.gain.cancelScheduledValues(now);
    gainNode.gain.setTargetAtTime(targetGain, now, timeConstant);
  }

  // Update Bass EQ
  if (bassFilter && typeof settings.bass === 'number') {
    const targetBass = Math.max(-6, Math.min(6, settings.bass));
    bassFilter.gain.cancelScheduledValues(now);
    bassFilter.gain.setTargetAtTime(targetBass, now, timeConstant);
  }

  // Update Voice Clarity EQ
  if (voiceFilter && typeof settings.voice === 'number') {
    const targetVoice = Math.max(-4, Math.min(6, settings.voice));
    voiceFilter.gain.cancelScheduledValues(now);
    voiceFilter.gain.setTargetAtTime(targetVoice, now, timeConstant);
  }

  // Update Treble EQ
  if (trebleFilter && typeof settings.treble === 'number') {
    const targetTreble = Math.max(-6, Math.min(6, settings.treble));
    trebleFilter.gain.cancelScheduledValues(now);
    trebleFilter.gain.setTargetAtTime(targetTreble, now, timeConstant);
  }
}

/**
 * Real-time visualizer streaming loop.
 * Only runs while the extension popup is open and connected.
 */
function startVisualizerStream() {
  if (vizAnimationFrameId) return;

  const freqData = new Uint8Array(32);
  const timeData = new Uint8Array(32);

  function broadcastFrame() {
    if (activeVisualizerPorts.size === 0) {
      vizAnimationFrameId = null;
      return;
    }

    if (analyser && audioContext && audioContext.state !== 'closed') {
      analyser.getByteFrequencyData(freqData);
      analyser.getByteTimeDomainData(timeData);

      // Downsample 32 bins to 16 display bars
      const bins = [];
      for (let i = 0; i < 16; i++) {
        const val = Math.max(freqData[i * 2], freqData[i * 2 + 1] || 0) / 255;
        bins.push(Number(val.toFixed(3)));
      }

      // Calculate RMS power
      let sumSquares = 0;
      for (let i = 0; i < timeData.length; i++) {
        const normalized = (timeData[i] - 128) / 128;
        sumSquares += normalized * normalized;
      }
      const rms = Math.min(1.0, Math.sqrt(sumSquares / timeData.length) * 2.2);

      const payload = {
        type: 'VIZ_DATA',
        bins: bins,
        rms: Number(rms.toFixed(3)),
        isAudioPlaying: rms > 0.02
      };

      for (const port of activeVisualizerPorts) {
        try {
          port.postMessage(payload);
        } catch (e) {
          activeVisualizerPorts.delete(port);
        }
      }
    }

    vizAnimationFrameId = requestAnimationFrame(broadcastFrame);
  }

  vizAnimationFrameId = requestAnimationFrame(broadcastFrame);
}

// Runtime message listener for service worker communication
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.target !== 'offscreen') {
    return false;
  }

  switch (message.type) {
    case 'START_AUDIO':
      startAudioProcessing(message.streamId, message.tabId, message.settings || {})
        .then(() => sendResponse({ success: true }))
        .catch((err) => sendResponse({ success: false, error: err.message }));
      return true; // Keep channel open for async response

    case 'UPDATE_AUDIO_SETTINGS':
      updateAudioSettings(message.settings || {});
      sendResponse({ success: true });
      return false;

    case 'STOP_AUDIO':
      cleanupAudio();
      sendResponse({ success: true });
      return false;

    case 'GET_AUDIO_STATUS':
      sendResponse({
        isActive: !!(audioContext && audioContext.state === 'running'),
        activeTabId: activeTabId
      });
      return false;
  }
});

// Port connection listener for visualizer streaming
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'visualizer_stream') {
    activeVisualizerPorts.add(port);

    port.onDisconnect.addListener(() => {
      activeVisualizerPorts.delete(port);
      if (activeVisualizerPorts.size === 0 && vizAnimationFrameId) {
        cancelAnimationFrame(vizAnimationFrameId);
        vizAnimationFrameId = null;
      }
    });

    if (analyser) {
      startVisualizerStream();
    }
  }
});
