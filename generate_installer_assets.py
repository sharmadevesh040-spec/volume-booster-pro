"""
Generate professional wizard branding images and multi-resolution icons
for Volume Booster Pro installer.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

def create_multi_res_icon():
    """Create a high-quality multi-size .ico from icon.png."""
    src_png = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(src_png):
        img = Image.open(src_png).convert("RGBA")
    else:
        # Create fresh icon
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([10, 10, 246, 246], fill=(15, 23, 42), outline=(0, 240, 255), width=8)
        d.polygon([(90, 60), (190, 128), (90, 196)], fill=(0, 240, 255))
    
    # Save multi-size ico
    ico_path = os.path.join(ASSETS_DIR, "icon.ico")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"[+] Generated multi-resolution icon: {ico_path}")

def create_wizard_large_bmp():
    """
    Generate Inno Setup WizardImageFile (164 x 314 pixels, 24-bit RGB BMP).
    Modern cyber-dark gaming / audio theme with cyan glow & equalizer bars.
    """
    width, height = 164, 314
    img = Image.new("RGB", (width, height), (10, 15, 26))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(height):
        ratio = y / height
        r = int(10 * (1 - ratio) + 16 * ratio)
        g = int(15 * (1 - ratio) + 24 * ratio)
        b = int(26 * (1 - ratio) + 45 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Glow aura behind logo
    center_x = width // 2
    logo_y = 75
    for radius in range(50, 10, -5):
        alpha = int(25 * (1.0 - radius / 50))
        draw.ellipse([center_x - radius, logo_y - radius, center_x + radius, logo_y + radius],
                     outline=(0, int(180 + alpha), 255))

    # Equalizer Visualizer Bars at the bottom
    num_bars = 16
    bar_width = 6
    spacing = 3
    start_x = (width - (num_bars * (bar_width + spacing) - spacing)) // 2
    base_y = 285

    bar_heights = [22, 38, 55, 78, 92, 115, 84, 68, 95, 120, 105, 82, 60, 45, 30, 18]

    for i, h in enumerate(bar_heights):
        bx = start_x + i * (bar_width + spacing)
        by = base_y - h
        
        # Draw gradient bar
        for seg_y in range(by, base_y, 4):
            intensity = (base_y - seg_y) / h
            if intensity > 0.8:
                col = (255, 60, 120) # Red/Magenta peak
            elif intensity > 0.5:
                col = (255, 180, 0)  # Orange/Yellow mid
            else:
                col = (0, 240, 255)  # Cyan low
            draw.rectangle([bx, seg_y, bx + bar_width - 1, min(base_y, seg_y + 2)], fill=col)

    # Draw Audio Waveform lines across the center
    wave_points = []
    for x in range(0, width, 4):
        wy = 180 + int(math.sin(x * 0.08) * 16 * math.cos(x * 0.03))
        wave_points.append((x, wy))
    for i in range(len(wave_points) - 1):
        draw.line([wave_points[i], wave_points[i+1]], fill=(0, 240, 255), width=2)

    # Overlay Volume Booster Pro Emblem/Logo
    src_png = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(src_png):
        icon = Image.open(src_png).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        img.paste(icon, (center_x - 32, logo_y - 32), icon)

    # Frame Accent
    draw.rectangle([0, 0, width - 1, height - 1], outline=(0, 200, 240), width=1)

    out_path = os.path.join(ASSETS_DIR, "wizard_large.bmp")
    img.save(out_path, format="BMP")
    print(f"[+] Generated WizardImageFile: {out_path}")

def create_wizard_small_bmp():
    """
    Generate Inno Setup WizardSmallImageFile (55 x 55 pixels, 24-bit RGB BMP).
    Header logo on top right of setup wizard pages.
    """
    width, height = 55, 55
    img = Image.new("RGB", (width, height), (240, 240, 240)) # Matches wizard header bg

    src_png = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(src_png):
        icon = Image.open(src_png).convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
        # Paste centered
        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bg.paste(icon, (4, 4), icon)
        # Composite onto white/light background
        composed = Image.alpha_composite(Image.new("RGBA", (width, height), (255, 255, 255, 255)), bg)
        img = composed.convert("RGB")

    out_path = os.path.join(ASSETS_DIR, "wizard_small.bmp")
    img.save(out_path, format="BMP")
    print(f"[+] Generated WizardSmallImageFile: {out_path}")

if __name__ == "__main__":
    create_multi_res_icon()
    create_wizard_large_bmp()
    create_wizard_small_bmp()
