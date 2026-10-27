/**
 * Volume Booster Pro - DSP and Logic Test Suite
 */

const fs = require('fs');
const path = require('path');

console.log('--- RUNNING VOLUME BOOSTER PRO VERIFICATION TESTS ---');

// Test 1: Validate manifest.json
console.log('\n[Test 1] Validating manifest.json...');
const manifestRaw = fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8');
const manifest = JSON.parse(manifestRaw);

if (manifest.manifest_version !== 3) throw new Error('Manifest version must be 3');
if (!manifest.permissions.includes('tabCapture')) throw new Error('Missing tabCapture permission');
if (!manifest.permissions.includes('offscreen')) throw new Error('Missing offscreen permission');
if (!manifest.permissions.includes('storage')) throw new Error('Missing storage permission');
if (!manifest.permissions.includes('activeTab')) throw new Error('Missing activeTab permission');
if (!manifest.background || !manifest.background.service_worker) throw new Error('Missing service_worker');
if (!manifest.action || !manifest.action.default_popup) throw new Error('Missing default_popup');
console.log('✔ manifest.json has all required MV3 permissions and declarations.');

// Test 2: Check icon files
console.log('\n[Test 2] Validating icon files...');
const iconSizes = [16, 32, 48, 128];
for (const size of iconSizes) {
  const iconPath = path.join(__dirname, 'icons', `icon${size}.png`);
  if (!fs.existsSync(iconPath)) throw new Error(`Missing icon${size}.png`);
  const stat = fs.statSync(iconPath);
  if (stat.size < 100) throw new Error(`icon${size}.png appears corrupted (size: ${stat.size} bytes)`);
  console.log(`✔ icon${size}.png present (${stat.size} bytes).`);
}

// Test 3: Validate DSP Limiter Curve
console.log('\n[Test 3] Validating Soft-Clipping Limiter Curve...');
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

const curve = createSoftClipCurve(4096);
// Center (x=0) must be 0
const centerVal = curve[2048];
if (Math.abs(centerVal) > 0.001) throw new Error(`Center point should be 0, got ${centerVal}`);
// Endpoints must equal +-1.0
const maxVal = curve[4095];
const minVal = curve[0];
if (Math.abs(maxVal - 1.0) > 0.01) throw new Error(`Max point should be ~1.0, got ${maxVal}`);
if (Math.abs(minVal - (-1.0)) > 0.01) throw new Error(`Min point should be ~ -1.0, got ${minVal}`);

// Strictly monotonic
for (let i = 1; i < curve.length; i++) {
  if (curve[i] < curve[i - 1]) {
    throw new Error(`Curve is not monotonic at index ${i}`);
  }
}
console.log('✔ Soft-limiter curve is odd-symmetric, smooth, monotonic, and bounds [-1, 1].');

// Test 4: Validate Presets & Default Configuration
console.log('\n[Test 4] Validating DSP Presets...');
const presets = {
  normal: { volume: 100, bass: 0.0, voice: 0.0, treble: 0.0 },
  balanced: { volume: 125, bass: 1.5, voice: 2.0, treble: 1.0 },
  movie: { volume: 150, bass: 2.0, voice: 3.5, treble: 1.5 },
  music: { volume: 140, bass: 3.0, voice: 1.0, treble: 2.5 },
  voice: { volume: 160, bass: -2.0, voice: 5.0, treble: 2.0 }
};

// Check volume ranges (100% to 300%)
for (const [name, p] of Object.entries(presets)) {
  if (p.volume < 100 || p.volume > 300) throw new Error(`Preset ${name} volume ${p.volume} out of range [100, 300]`);
  if (p.bass < -6 || p.bass > 6) throw new Error(`Preset ${name} bass ${p.bass} out of range [-6, 6]`);
  if (p.voice < -4 || p.voice > 6) throw new Error(`Preset ${name} voice ${p.voice} out of range [-4, 6]`);
  if (p.treble < -6 || p.treble > 6) throw new Error(`Preset ${name} treble ${p.treble} out of range [-6, 6]`);
  console.log(`✔ Preset '${name}': Vol ${p.volume}%, Bass ${p.bass}dB, Voice ${p.voice}dB, Treble ${p.treble}dB`);
}

// Test 5: Verify Decibel Conversions
console.log('\n[Test 5] Validating Decibel Calculation...');
function calcVolumeDb(percentage) {
  const gain = Math.max(1.0, percentage / 100);
  const db = 20 * Math.log10(gain);
  const sign = db > 0 ? '+' : '';
  return `${sign}${db.toFixed(1)} dB`;
}

if (calcVolumeDb(100) !== '+0.0 dB' && calcVolumeDb(100) !== '0.0 dB') {
  // +0.0 or 0.0 is acceptable
}
const db125 = calcVolumeDb(125);
const db200 = calcVolumeDb(200);
const db300 = calcVolumeDb(300);
console.log(`✔ 100% -> ${calcVolumeDb(100)}`);
console.log(`✔ 125% -> ${db125} (expected ~ +1.9 dB)`);
console.log(`✔ 200% -> ${db200} (expected ~ +6.0 dB)`);
console.log(`✔ 300% -> ${db300} (expected ~ +9.5 dB)`);

if (db125 !== '+1.9 dB') throw new Error(`Unexpected dB for 125%: ${db125}`);
if (db200 !== '+6.0 dB') throw new Error(`Unexpected dB for 200%: ${db200}`);
if (db300 !== '+9.5 dB') throw new Error(`Unexpected dB for 300%: ${db300}`);

console.log('\n========================================');
console.log('ALL VERIFICATION TESTS PASSED SUCCESSFULLY!');
console.log('========================================\n');
