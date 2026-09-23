"""Turn the downloaded institution logos into hero-ready web assets.

The originals are stock-site grabs that live outside the repo (see SRC).  Three
of the four have a checkerboard *baked into the pixels* rather than real
transparency, so a plain background-removal would leave a gray grid behind.

Each logo is therefore:

  1. flattened onto white and white-point corrected, which lifts the baked
     checker gray to pure white and leaves the dark ink alone;
  2. keyed to transparency, with the ink recoloured to white -- the hero video
     behind the row is dark, so the original inks (black, dark gray, crimson,
     blue) would all disappear.  Monochrome white also makes the four read as
     one set instead of four unrelated brand assets;
  3. trimmed tight to the ink, so that one shared CSS height gives all four the
     same optical height;
  4. downsampled to HEIGHT, which is 4x the size they are displayed at.

Re-run after replacing any source file:

    python3 tools/build_logos.py
"""
import collections
import os

from PIL import Image, ImageChops

SRC = os.path.expanduser("~/Downloads")
DST = os.path.join(os.path.dirname(__file__), "..", "static", "images", "logos")
HEIGHT = 152          # 4x the 38px the logos are displayed at
INK_GAIN = 255 / 205  # firms up mid-gray ink (ETH) and antialiased edges

JOBS = [
    ("usc-logo.png", "usc.png"),
    ("eth-logo2.png", "eth.png"),
    ("Logo-nvidia-transparent-PNG.png", "nvidia.png"),
    ("zhaw-zurich-university-of-applied-sciences-vector-logo.png", "zhaw.png"),
]


def checker_gray(im):
    """The gray of a baked-in checkerboard, or None for a clean white margin.

    Read off the top and bottom edge bands, which are background in all four
    files; a real logo contributes no mid-gray there.
    """
    gray, (w, h) = im.convert("L"), im.size
    band = [gray.getpixel((x, y))
            for y in list(range(6)) + list(range(h - 6, h))
            for x in range(0, w, 2)]
    counts = collections.Counter(v for v in band if 190 <= v < 252)
    if not counts:
        return None
    value, n = counts.most_common(1)[0]
    return value if n > len(band) * 0.05 else None


os.makedirs(DST, exist_ok=True)

for src, out in JOBS:
    im = Image.open(os.path.join(SRC, src))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255,) * 4), im)
    im = im.convert("RGB")

    checker = checker_gray(im)
    if checker:
        # Stretch so the checker gray lands on pure white; dark ink is untouched.
        im = im.point([min(255, round(v * 255 / checker)) for v in range(256)] * 3)

    # Opacity from the darkest channel (see module docstring): white background -> 0, any ink -> opaque.
    r, g, b = im.split()
    darkest = ImageChops.darker(ImageChops.darker(r, g), b)
    alpha = darkest.point(lambda v: min(255, round((255 - v) * INK_GAIN)))

    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(alpha)

    box = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    if box:
        white = white.crop(box)

    w = round(white.width * HEIGHT / white.height)
    white = white.resize((w, HEIGHT), Image.LANCZOS)
    white.save(os.path.join(DST, out), optimize=True)
    size = os.path.getsize(os.path.join(DST, out)) / 1024
    print(f"{out:12} checker={str(checker):4} {white.size}  {size:.1f} KB")
