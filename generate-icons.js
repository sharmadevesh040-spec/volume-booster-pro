const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// CRC32 implementation for PNG chunks
const crcTable = [];
for (let n = 0; n < 256; n++) {
  let c = n;
  for (let k = 0; k < 8; k++) {
    c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
  }
  crcTable[n] = c;
}

function crc32(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = crcTable[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function createPNG(width, height, pixelBuffer) {
  // pixelBuffer: width * height * 4 (RGBA)
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  // IHDR chunk
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8; // bit depth
  ihdrData[9] = 6; // color type RGBA
  ihdrData[10] = 0; // compression
  ihdrData[11] = 0; // filter
  ihdrData[12] = 0; // interlace

  const ihdrChunk = Buffer.alloc(4 + 4 + 13 + 4);
  ihdrChunk.writeUInt32BE(13, 0);
  ihdrChunk.write('IHDR', 4);
  ihdrData.copy(ihdrChunk, 8);
  const ihdrCrc = crc32(ihdrChunk.subarray(4, 21));
  ihdrChunk.writeUInt32BE(ihdrCrc, 21);

  // IDAT chunk: filter byte (0) + row bytes
  const scanlines = Buffer.alloc(height * (1 + width * 4));
  for (let y = 0; y < height; y++) {
    const rowOffset = y * (1 + width * 4);
    scanlines[rowOffset] = 0; // None filter
    const pixelOffset = y * width * 4;
    pixelBuffer.copy(scanlines, rowOffset + 1, pixelOffset, pixelOffset + width * 4);
  }

  const compressedData = zlib.deflateSync(scanlines, { level: 9 });
  const idatChunk = Buffer.alloc(4 + 4 + compressedData.length + 4);
  idatChunk.writeUInt32BE(compressedData.length, 0);
  idatChunk.write('IDAT', 4);
  compressedData.copy(idatChunk, 8);
  const idatCrc = crc32(idatChunk.subarray(4, 8 + compressedData.length));
  idatChunk.writeUInt32BE(idatCrc, 8 + compressedData.length);

  // IEND chunk
  const iendChunk = Buffer.alloc(12);
  iendChunk.writeUInt32BE(0, 0);
  iendChunk.write('IEND', 4);
  const iendCrc = crc32(Buffer.from('IEND'));
  iendChunk.writeUInt32BE(iendCrc, 8);

  return Buffer.concat([signature, ihdrChunk, idatChunk, iendChunk]);
}

// Distance to line segment
function distToSegment(px, py, x1, y1, x2, y2) {
  const l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2;
  if (l2 === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
}

// Draw procedural icon
function renderIcon(size) {
  const buf = Buffer.alloc(size * size * 4);

  // Render with 2x2 super-sampling for anti-aliasing
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      let rSum = 0, gSum = 0, bSum = 0, aSum = 0;
      const samples = 2;
      for (let sy = 0; sy < samples; sy++) {
        for (let sx = 0; sx < samples; sx++) {
          const px = (x + (sx + 0.5) / samples) / size; // 0..1
          const py = (y + (sy + 0.5) / samples) / size; // 0..1

          // Background rounded badge
          const cx = 0.5, cy = 0.5;
          const cornerRadius = 0.24;
          const dx = Math.max(Math.abs(px - cx) - (0.46 - cornerRadius), 0);
          const dy = Math.max(Math.abs(py - cy) - (0.46 - cornerRadius), 0);
          const distFromCorner = Math.hypot(dx, dy);
          const inBadge = distFromCorner <= cornerRadius;

          let r = 0, g = 0, b = 0, a = 0;

          if (inBadge) {
            // Dark futuristic metallic gradient background
            const bgGrad = 0.08 + 0.06 * (1.0 - py) + 0.04 * (px);
            r = Math.floor(13 + bgGrad * 15);
            g = Math.floor(18 + bgGrad * 25);
            b = Math.floor(32 + bgGrad * 45);
            a = 255;

            // Border glow
            const borderDist = cornerRadius - distFromCorner;
            if (borderDist < 0.04 && borderDist >= 0) {
              const borderAlpha = (1 - borderDist / 0.04) * 0.7;
              r = Math.floor(r * (1 - borderAlpha) + 0 * borderAlpha);
              g = Math.floor(g * (1 - borderAlpha) + 240 * borderAlpha);
              b = Math.floor(b * (1 - borderAlpha) + 255 * borderAlpha);
            }

            // Draw Speaker Cone
            // Base rectangle: x in [0.20, 0.32], y in [0.38, 0.62]
            const inSpkBase = (px >= 0.20 && px <= 0.32 && py >= 0.38 && py <= 0.62);

            // Trapezoid cone: from x=0.32 (y in [0.38, 0.62]) to x=0.48 (y in [0.22, 0.78])
            let inSpkCone = false;
            if (px >= 0.32 && px <= 0.48) {
              const t = (px - 0.32) / (0.48 - 0.32);
              const topY = 0.38 - t * (0.38 - 0.22);
              const botY = 0.62 + t * (0.78 - 0.62);
              if (py >= topY && py <= botY) {
                inSpkCone = true;
              }
            }

            if (inSpkBase || inSpkCone) {
              // Vibrant cyan to purple gradient for speaker body
              const spkGrad = (px - 0.20) / 0.28;
              r = Math.floor(0 * (1 - spkGrad) + 168 * spkGrad);
              g = Math.floor(229 * (1 - spkGrad) + 85 * spkGrad);
              b = Math.floor(255 * (1 - spkGrad) + 247 * spkGrad);
              a = 255;
            }

            // Sound waves / lightning energy arcs
            // Arc 1: radius ~0.20 centered at (0.36, 0.50), angle -45 to +45 deg
            // Arc 2: radius ~0.32
            // Arc 3: radius ~0.44
            const arcCx = 0.36, arcCy = 0.50;
            const arcDist = Math.hypot(px - arcCx, py - arcCy);
            const arcAngle = Math.atan2(py - arcCy, px - arcCx); // in radians

            if (Math.abs(arcAngle) < 0.85 && px > arcCx + 0.10) {
              // Check proximity to wave rings
              const waves = [
                { r: 0.21, w: 0.032, cr: 0, cg: 240, cb: 255 },
                { r: 0.33, w: 0.036, cr: 139, cg: 92, cb: 246 },
                { r: 0.45, w: 0.040, cr: 217, cg: 70, cb: 239 }
              ];

              for (const wave of waves) {
                const d = Math.abs(arcDist - wave.r);
                if (d < wave.w) {
                  const edgeFactor = 1 - (d / wave.w);
                  const angleFade = Math.cos((arcAngle / 0.85) * (Math.PI / 2));
                  const strength = edgeFactor * angleFade;
                  r = Math.floor(r * (1 - strength) + wave.cr * strength);
                  g = Math.floor(g * (1 - strength) + wave.cg * strength);
                  b = Math.floor(b * (1 - strength) + wave.cb * strength);
                }
              }
            }

            // Lightning boost spark over the speaker
            // A subtle electric cyan line accentuating "Pro"
            const sparkD = distToSegment(px, py, 0.30, 0.44, 0.42, 0.56);
            if (sparkD < 0.02) {
              const sparkStrength = (1 - sparkD / 0.02) * 0.9;
              r = Math.floor(r * (1 - sparkStrength) + 255 * sparkStrength);
              g = Math.floor(g * (1 - sparkStrength) + 255 * sparkStrength);
              b = Math.floor(b * (1 - sparkStrength) + 255 * sparkStrength);
            }
          }

          rSum += r;
          gSum += g;
          bSum += b;
          aSum += a;
        }
      }

      const total = samples * samples;
      const idx = (y * size + x) * 4;
      buf[idx] = Math.round(rSum / total);
      buf[idx + 1] = Math.round(gSum / total);
      buf[idx + 2] = Math.round(bSum / total);
      buf[idx + 3] = Math.round(aSum / total);
    }
  }

  return createPNG(size, size, buf);
}

const iconsDir = path.join(__dirname, 'icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

[16, 32, 48, 128].forEach(size => {
  const pngBuf = renderIcon(size);
  const outPath = path.join(iconsDir, `icon${size}.png`);
  fs.writeFileSync(outPath, pngBuf);
  console.log(`Generated ${outPath} (${pngBuf.length} bytes)`);
});
