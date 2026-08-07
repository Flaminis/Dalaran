#!/usr/bin/env python3
"""Generate Dalaran's raster branding assets from the geometric mark definition.

The marks are original artwork built from geometric primitives (see
docs/assets/BRANDING.md). This script is the single source of truth for every
derived PNG/ICO in the tree, so the icons can be regenerated instead of being
opaque binaries nobody can edit:

    python3 scripts/generate_branding_assets.py

Requires Pillow. Run it after changing the mark, and commit the result.
"""

from PIL import Image, ImageDraw, ImageFilter

VIOLET = (108, 76, 241)
LEY = (43, 184, 217)
GOLD = (232, 180, 74)
MIST = (245, 246, 250)
VOID = (11, 13, 20)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c0, c1):
    """Diagonal gradient."""
    g = Image.new("RGB", (size, size))
    px = g.load()
    for y in range(size):
        for x in range(size):
            t = x / size * 0.45 + y / size * 0.55
            px[x, y] = lerp(c0, c1, t)
    return g


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def draw_mark(size, ring_col=MIST, orbit_col=LEY, lens_col=VIOLET, core_col=GOLD, glow=True, simple=False):
    """The Dalaran mark: observatory ring, two ley-line orbits, arcane lens."""
    S = 4
    n = size * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = n / 2
    R = n * 0.40  # outer ring radius
    lw = max(2, int(n * 0.052))  # ring weight
    # orbits: rotated ellipses, clipped to the inside of the ring so the mark stays contained
    if not simple:
        orb = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        for ang in (-32, 32):
            lay = Image.new("RGBA", (n, n), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            rx, ry = R * 0.94, R * 0.36
            ld.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=orbit_col + (255,), width=max(2, int(lw * 0.62)))
            orb.alpha_composite(lay.rotate(ang, resample=Image.BICUBIC, center=(cx, cy)))
        clip = Image.new("L", (n, n), 0)
        ImageDraw.Draw(clip).ellipse([cx - R + lw / 2, cy - R + lw / 2, cx + R - lw / 2, cy + R - lw / 2], fill=255)
        orb.putalpha(Image.composite(orb.getchannel("A"), Image.new("L", (n, n), 0), clip))
        img.alpha_composite(orb)
    # outer ring
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=ring_col + (255,), width=lw)
    # arcane lens (diamond) - filled, sits above the orbits
    h, w = R * 0.62, R * 0.34
    d.polygon([(cx, cy - h), (cx + w, cy), (cx, cy + h), (cx - w, cy)], fill=lens_col + (255,))
    # gold core
    h2, w2 = h * 0.46, w * 0.46
    d.polygon([(cx, cy - h2), (cx + w2, cy), (cx, cy + h2), (cx - w2, cy)], fill=core_col + (255,))
    # horizon anchor nodes
    if not simple:
        r = n * 0.037
        for x in (cx - R, cx + R):
            d.ellipse([x - r, cy - r, x + r, cy + r], fill=orbit_col + (255,))
    out = img.resize((size, size), Image.LANCZOS)
    if glow:
        gl = out.filter(ImageFilter.GaussianBlur(size * 0.02))
        base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        base.alpha_composite(gl)
        base.alpha_composite(out)
        out = base
    return out


def app_icon(size, pad_ratio, radius_ratio, simple=False):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * (1 - 2 * pad_ratio))
    grad = gradient(inner, (86, 58, 214), (26, 40, 96))
    tile = Image.new("RGBA", (inner, inner))
    tile.paste(grad, (0, 0))
    tile.putalpha(rounded_mask(inner, int(inner * radius_ratio)))
    mark = draw_mark(int(inner * 0.80), simple=simple)
    tile.alpha_composite(mark, (int((inner - mark.width) / 2), int((inner - mark.height) / 2)))
    canvas.alpha_composite(tile, (int(size * pad_ratio), int(size * pad_ratio)))
    return canvas


from pathlib import Path

R = str(Path(__file__).resolve().parent.parent)

# --- viewer app icons -------------------------------------------------------
app_icon(1024, 0.098, 0.225).save(f"{R}/crates/viewer/dl_viewer/data/app_icon_mac.png")
app_icon(512, 0.0, 0.16).save(f"{R}/crates/viewer/dl_viewer/data/app_icon.png")

# --- in-app logo (transparent, shown on dark backgrounds) -------------------
draw_mark(256).save(f"{R}/crates/viewer/dl_ui/data/icons/dalaran_logo.png")

# --- web viewer -------------------------------------------------------------
web = f"{R}/crates/viewer/dl_web_viewer_server/web_viewer"
app_icon(180, 0.0, 0.20).save(f"{web}/apple-touch-icon.png")
ico = [app_icon(s, 0.0, 0.16, simple=(s <= 32)).convert("RGBA") for s in (16, 32, 48, 64, 128, 256)]
ico[0].save(f"{web}/favicon.ico", format="ICO", sizes=[(i.width, i.height) for i in ico], append_images=ico[1:])
print("wrote viewer + web assets")
