"""Generate AXIOMATA logo assets (SVG + PNG + multi-size ICO) using Pillow.

The logo is a stylised atom (three elliptical orbits + nucleus) in the AXIOMATA
cyan accent, on a dark rounded-square badge. Outputs go to packaging/assets/:

    logo.svg   - scalable vector master
    logo.png   - 512x512 transparent-background render
    logo.ico   - multi-resolution Windows icon (16..256)
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# AXIOMATA palette
BG = (8, 13, 22, 255)          # #080D16
BADGE = (17, 27, 42, 255)      # #111B2A
ACCENT = (54, 197, 232, 255)   # #36C5E8
ACCENT_2 = (120, 139, 255, 255)  # #788BFF
TEXT = (232, 240, 250, 255)    # #E8F0FA

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#36C5E8"/>
      <stop offset="1" stop-color="#788BFF"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="480" height="480" rx="112" fill="#111B2A"/>
  <rect x="16" y="16" width="480" height="480" rx="112" fill="none" stroke="#24344A" stroke-width="6"/>
  <g fill="none" stroke="url(#g)" stroke-width="18">
    <ellipse cx="256" cy="256" rx="176" ry="74"/>
    <ellipse cx="256" cy="256" rx="176" ry="74" transform="rotate(60 256 256)"/>
    <ellipse cx="256" cy="256" rx="176" ry="74" transform="rotate(120 256 256)"/>
  </g>
  <circle cx="256" cy="256" r="34" fill="#36C5E8"/>
  <circle cx="408" cy="212" r="20" fill="#788BFF"/>
</svg>
"""


def _rounded_badge(draw: ImageDraw.ImageDraw, size: int) -> None:
    m = int(size * 0.03)
    draw.rounded_rectangle(
        [m, m, size - m, size - m],
        radius=int(size * 0.22),
        fill=BADGE,
        outline=(36, 52, 74, 255),
        width=max(1, size // 128),
    )


def _orbit(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float,
           angle_deg: float, color, width: float, steps: int = 240) -> None:
    pts = []
    a = math.radians(angle_deg)
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        xr = x * math.cos(a) - y * math.sin(a)
        yr = x * math.sin(a) + y * math.cos(a)
        pts.append((cx + xr, cy + yr))
    draw.line(pts, fill=color, width=int(width), joint="curve")


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _rounded_badge(d, size)
    cx = cy = size / 2
    rx = size * 0.345
    ry = size * 0.145
    lw = max(2, size * 0.035)
    for ang in (0, 60, 120):
        _orbit(d, cx, cy, rx, ry, ang, ACCENT, lw)
    # nucleus
    nr = size * 0.066
    d.ellipse([cx - nr, cy - nr, cx + nr, cy + nr], fill=ACCENT)
    # electron
    er = size * 0.039
    ex, ey = size * 0.797, size * 0.414
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=ACCENT_2)
    return img


def main() -> None:
    (ASSETS / "logo.svg").write_text(SVG, encoding="utf-8")
    master = render(512)
    master.save(ASSETS / "logo.png")
    # Multi-resolution ICO for the Windows executable + installer.
    master.save(
        ASSETS / "logo.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
               (128, 128), (256, 256)],
    )
    print(f"Assets written to {ASSETS}")
    for p in sorted(ASSETS.iterdir()):
        print(f"  {p.name}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()