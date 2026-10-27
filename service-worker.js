/**
 * Volume Booster Pro - Background Service Worker (Manifest V3)
 *
 * Coordinates extension lifecycle, tab capture authorization,
 * offscreen document management, and persistent storage.
 */

const DEFAULT_SETTINGS = {
  volume: 125, // Default Balanced mode at 125%
  preset: 'balanced',
  bass: 1.5,
  voice: 2.0,
  treble: 1.0
};

// Runtime session state
let sessionState = {
  isBoosting: false,
  boostingTabId: null,
  boostingTabTitle: '',
  settings: { ...DEFAULT_SETTINGS }
};

// Initialize settings from chrome.storage.local
chrome.storage.local.get(['settings'], (result) => {
  if (result && result.settings) {
    sessionState.settings = { ...DEFAULT_SETTINGS, ...result.settings };
  } else {
    chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
  }
});

/**
 * Check if the offscreen document is currently active.
 */
async function hasOffscreenDocument() {
  if ('hasDocument' in chrome.offscreen) {
    return await chrome.offscreen.hasDocument();
  }
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });
  return contexts && contexts.length > 0;
}

/**
 * Ensure an offscreen document is open and ready.
 */
async function ensureOffscreenDocument() {
  const exists = await hasOffscreenDocument();
  if (exists) return;

  try {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA', 'AUDIO_PLAYBACK'],
      justification: 'Capture tab audio stream and apply Web Audio API processing and amplification.'
    });
    // Brief settle time to ensure offscreen script has initialized
    await new Promise((resolve) => setTimeout(resolve, 60));
  } catch (err) {
    // Check if error was just that document already exists (race condition)
    if (!err.message || !err.message.includes('Only a single offscreen document may be created')) {
      console.error('[ServiceWorker] Failed to create offscreen document:', err);
      throw err;
    }
  }
}

/**
 * Close the offscreen document to conserve resources when not boosting.
 */
async function closeOffscreenDocument() {
  const exists = await hasOffscreenDocument();
  if (!exists) return;

  try {
    await chrome.offscreen.closeDocument();
  } catch (err) {
    console.warn('[ServiceWorker] Error closing offscreen document:', err);
  }
}

/**
 * Update the extension icon badge text and color based on current volume.
 */
function updateBadge(volume, isBoosting) {
  if (!isBoosting) {
    chrome.action.setBadgeText({ text: '' });
    return;
  }
  const text = `${Math.round(volume)}%`;
  chrome.action.setBadgeText({ text });
  // Purple / Cyan tone for badge
  chrome.action.setBadgeBackgroundColor({ color: volume > 200 ? '#f59e0b' : '#7c3aed' });
}

/**
 * Obtain a streamId for tab capture.
 */
function getMediaStreamId(tabId) {
  return new Promise((resolve, reject) => {
    chrome.tabCapture.getMediaStreamId({ targetTabId: tabId }, (streamId) => {
      if (chrome.runtime.lastError) {
        return reject(new Error(chrome.runtime.lastError.message));
      }
      if (!streamId) {
        return reject(new Error('Failed to obtain audio capture stream ID for this tab.'));
      }
      resolve(streamId);
    });
  });
}

/**
 * Start boosting audio for a specific tab.
 */
async function startBoosting(tabId, providedStreamId, tabTitle) {
  // If already boosting another tab, stop it first
  if (sessionState.isBoosting && sessionState.boostingTabId !== tabId) {
    await stopBoosting();
  }

  // Obtain stream ID if not provided by popup
  let streamId = providedStreamId;
  if (!streamId) {
    streamId = await getMediaStreamId(tabId);
  }

  // Ensure offscreen document is running
  await ensureOffscreenDocument();

  // Send start command to offscreen document
  const response = await new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        target: 'offscreen',
        type: 'START_AUDIO',
        streamId: streamId,
        tabId: tabId,
        settings: sessionState.settings
      },
      (res) => {
        if (chrome.runtime.lastError) {
          return reject(new Error(chrome.runtime.lastError.message));
        }
        if (res && res.success) {
          resolve(res);
        } else {
          reject(new Error(res ? res.error : 'Offscreen failed to start audio.'));
        }
      }
    );
  });

  // Update session state
  sessionState.isBoosting = true;
  sessionState.boostingTabId = tabId;
  sessionState.boostingTabTitle = tabTitle || 'Browser Tab';

  updateBadge(sessionState.settings.volume, true);

  return { success: true };
}

/**
 * Stop boosting audio and restore default tab output.
 */
async function stopBoosting() {
  const exists = await hasOffscreenDocument();
  if (exists) {
    try {
      await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          { target: 'offscreen', type: 'STOP_AUDIO' },
          () => resolve()
        );
      });
    } catch (e) {}
    await closeOffscreenDocument();
  }

  sessionState.isBoosting = false;
  sessionState.boostingTabId = null;
  sessionState.boostingTabTitle = '';
  updateBadge(0, false);

  return { success: true };
}

// Runtime message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Ignore messages meant specifically for offscreen
  if (message.target === 'offscreen') {
    return false;
  }

  switch (message.type) {
    case 'GET_STATE': {
      sendResponse({
        success: true,
        state: {
          isBoosting: sessionState.isBoosting,
          boostingTabId: sessionState.boostingTabId,
          boostingTabTitle: sessionState.boostingTabTitle,
          settings: sessionState.settings
        }
      });
      return false;
    }

    case 'START_BOOST': {
      startBoosting(message.tabId, message.streamId, message.tabTitle)
        .then(() => sendResponse({ success: true }))
        .catch((err) => sendResponse({ success: false, error: err.message }));
      return true; // Keep channel open for async response
    }

    case 'STOP_BOOST': {
      stopBoosting()
        .then(() => sendResponse({ success: true }))
        .catch((err) => sendResponse({ success: false, error: err.message }));
      return true;
    }

    case 'UPDATE_SETTINGS': {
      sessionState.settings = { ...sessionState.settings, ...message.settings };
      chrome.storage.local.set({ settings: sessionState.settings });

      if (sessionState.isBoosting) {
        updateBadge(sessionState.settings.volume, true);
        // Forward settings directly to offscreen processor
        chrome.runtime.sendMessage({
          target: 'offscreen',
          type: 'UPDATE_AUDIO_SETTINGS',
          settings: sessionState.settings
        }).catch(() => {});
      }

      sendResponse({ success: true, settings: sessionState.settings });
      return false;
    }

    case 'STREAM_ENDED': {
      if (sessionState.boostingTabId === message.tabId) {
        console.log('[ServiceWorker] Stream ended for tab', message.tabId);
        stopBoosting();
      }
      sendResponse({ success: true });
      return false;
    }
  }
});

// Tab event: handle closed tabs
chrome.tabs.onRemoved.addListener((tabId) => {
  if (sessionState.isBoosting && sessionState.boostingTabId === tabId) {
    console.log('[ServiceWorker] Boosted tab closed, stopping boost for tab', tabId);
    stopBoosting();
  }
});

// Clean up stale badges on install/startup
chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({ text: '' });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.action.setBadgeText({ text: '' });
});
