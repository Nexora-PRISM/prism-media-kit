#!/usr/bin/env python3
"""Gera o kit de divulgação da Nexora Prism a partir da logo definitiva."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

ROOT = Path("/workspace")
SRC_PRISM = ROOT / "assets/3dfb3e0d-2c48-4516-b703-dddfa0dd2327.png"
SRC_LOCKUP = ROOT / "assets/359074ef-387f-4f03-81d0-379b2a2470d0.png"
OUT = ROOT / "divulgacao"

FONT_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
FONT_REG = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
FONT_SEM = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"

SITE = "nexoraprism.com.br"
HANDLE = "@nexoraprism_"
EMAIL = "contato@nexoraprism.com.br"

INK = (232, 238, 246, 255)
MUTED = (168, 182, 200, 255)
CYAN = (90, 214, 255, 255)
VIOLET = (188, 92, 255, 255)


def smoothstep(x, e0, e1):
    t = np.clip((x - e0) / max(e1 - e0, 1e-6), 0, 1)
    return t * t * (3 - 2 * t)


def trim(im: Image.Image, pad: int = 2, threshold: int = 8) -> Image.Image:
    arr = np.asarray(im)
    if arr.ndim == 2:
        ys, xs = np.where(arr > threshold)
    else:
        ys, xs = np.where(arr[:, :, 3] > threshold)
    if len(xs) == 0:
        return im
    h, w = arr.shape[:2]
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(w, int(xs.max()) + 1 + pad)
    y1 = min(h, int(ys.max()) + 1 + pad)
    return im.crop((x0, y0, x1, y1))


def extract_prism() -> Image.Image:
    src = np.asarray(Image.open(SRC_PRISM).convert("RGB")).astype(np.float32)
    h, w, _ = src.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy, rx, ry = 450, 800, 310, 250
    d = np.abs(xx - cx) / rx + np.abs(yy - cy) / ry
    lum = 0.2126 * src[:, :, 0] + 0.7152 * src[:, :, 1] + 0.0722 * src[:, :, 2]
    mx = src.max(2)
    mn = src.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    inside = np.clip(1 - d / 0.92, 0, 1)
    glow = smoothstep(lum, 16, 55) * smoothstep(sat, 0.08, 0.35)
    hot = smoothstep(lum, 80, 160)
    feather = np.clip((0.35 - (d - 0.85)) / 0.35, 0, 1)
    alpha = np.clip(np.maximum(inside, (glow * 0.85 + hot * 0.5) * feather), 0, 1)
    alpha = np.where(d > 1.22, 0, alpha)
    firm = alpha > 0.12
    lab, n = ndimage.label(firm)
    if n:
        sizes = ndimage.sum(firm, lab, range(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[1 + int(np.argmax(sizes))] = True
        alpha = np.where(keep[lab], alpha, 0)
    # Corta o brilho solto abaixo da ponta.
    tip = np.where((lum > 170) & (alpha > 0.85))
    if len(tip[0]):
        cut = int(tip[0].max()) + 14
        alpha[cut:, :] = 0
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[:, :, :3] = np.clip(src, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return trim(Image.fromarray(rgba, "RGBA"), pad=4)


def extract_wordmark() -> Image.Image:
    src = np.asarray(Image.open(SRC_LOCKUP).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = 520, 498, 1208, 748
    crop = src[y0:y1, x0:x1]
    lum = 0.2126 * crop[:, :, 0] + 0.7152 * crop[:, :, 1] + 0.0722 * crop[:, :, 2]
    dark = np.minimum(lum, 36)
    bg = np.asarray(
        Image.fromarray(dark.astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))
    ).astype(np.float32)
    delta = lum - bg
    r = crop[:, :, 0]
    b = crop[:, :, 2]
    core = delta > 36
    lab, n = ndimage.label(core)
    sizes = ndimage.sum(core, lab, range(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    for i, size in enumerate(sizes, start=1):
        ys, xs = np.where(lab == i)
        if size < 80:
            continue
        if (b[ys, xs] - r[ys, xs]).mean() > 80 and xs.mean() < crop.shape[1] * 0.2:
            continue
        if lum[ys, xs].max() < 150:
            continue
        keep[i] = True
    mask = keep[lab]
    mask = ndimage.binary_dilation(mask, iterations=1) & (delta > 10)
    eroded = ndimage.binary_erosion(mask, iterations=1)
    alpha = np.where(eroded, 1.0, np.where(mask, 0.6, 0.0))
    alpha = (
        np.asarray(
            Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(0.45)
            )
        ).astype(np.float32)
        / 255.0
    )
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w]
    bright = ndimage.binary_dilation(lum > 160, iterations=2)
    smudge = (lum < 95) & (alpha > 0.03) & (yy < int(h * 0.24)) & (xx > int(w * 0.84)) & ~bright
    alpha = np.where(smudge, 0, alpha)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[:, :, :3] = np.clip(crop, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return trim(Image.fromarray(rgba, "RGBA"), pad=2)


def fit(im: Image.Image, height: int) -> Image.Image:
    height = max(1, int(height))
    width = max(1, int(round(im.width * height / im.height)))
    return im.resize((width, height), Image.Resampling.LANCZOS)


def screen_blend(base: np.ndarray, layer: np.ndarray) -> np.ndarray:
    b = base.astype(np.float32) / 255.0
    layer = layer.astype(np.float32) / 255.0
    return np.clip((1 - (1 - b) * (1 - layer)) * 255.0, 0, 255)


def dist_segment(xx, yy, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    wx, wy = xx - x0, yy - y0
    t = np.clip((wx * vx + wy * vy) / (vx * vx + vy * vy + 1e-8), 0, 1)
    px, py = x0 + t * vx, y0 + t * vy
    return np.hypot(xx - px, yy - py)


def paint_scene(w: int, h: int, anchor=(0.36, 0.5), beams=None, calm: bool = False) -> Image.Image:
    rng = np.random.default_rng(11)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    void = np.array([5, 6, 10], np.float32)
    navy = np.array([13, 18, 32], np.float32)
    lift = np.clip(1 - np.abs(yy - 0.42) * 1.35, 0, 1)  # (h, 1)
    img = np.empty((h, w, 3), np.float32)
    img[:] = void + (navy - void) * lift[..., None]

    # Fumaça larga e suave, no tom da arte original.
    smoke = np.zeros((h, w), np.float32)
    for cell, amp in ((max(24, min(h, w) // 10), 0.7), (max(48, min(h, w) // 5), 0.4)):
        small = rng.random((max(2, h // cell), max(2, w // cell))).astype(np.float32)
        tile = np.asarray(
            Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
        ).astype(np.float32) / 255.0
        smoke += (tile - 0.5) * amp
    smoke_u8 = np.clip((smoke - smoke.min()) / (np.ptp(smoke) + 1e-6) * 255, 0, 255).astype(np.uint8)
    smoke = np.asarray(Image.fromarray(smoke_u8).filter(ImageFilter.GaussianBlur(max(8, min(h, w) // 50)))).astype(np.float32) / 255.0
    smoke = smoke - 0.5
    mist = np.array([14, 18, 26], np.float32) * (0.45 if calm else 1.0)
    img += smoke[..., None] * mist

    ax, ay = anchor
    d = np.hypot((xx - ax) * (1.15 if w > h * 1.6 else 1.0), (yy - ay) * (0.85 if h > w else 1.0))
    glow = np.exp(-((d / 0.42) ** 2))
    img += np.array([16, 48, 82], np.float32) * glow[..., None]
    violet = np.exp(-((np.hypot(xx - ax, (yy - min(0.98, ay + 0.16)) / 0.9) / 0.28) ** 2))
    img += np.array([28, 6, 42], np.float32) * violet[..., None] * (0.35 if calm else 0.7)

    if not calm:
        beams = beams or [
            ((0.0, 0.16), (0.30, 0.0), 0.016, (170, 220, 255), 0.42),
            ((0.68, 1.02), (1.0, 0.62), 0.014, (220, 232, 255), 0.34),
        ]
        layer = np.zeros((h, w, 3), np.float32)
        for (x0, y0), (x1, y1), width, color, gain in beams:
            dist = dist_segment(xx, yy, x0, y0, x1, y1)
            core = np.exp(-((dist / max(width * 0.28, 0.0015)) ** 2))
            halo = np.exp(-((dist / width) ** 2))
            col = np.array(color, np.float32)
            layer += (halo[..., None] * 0.55 + core[..., None]) * col * gain
        img = screen_blend(img, np.clip(layer, 0, 255))

    vig = (np.abs(xx - 0.5) * 1.15) ** 2 + (np.abs(yy - 0.5) * 1.05) ** 2
    img *= np.clip(1 - vig * (0.28 if calm else 0.38), 0.62, 1)[..., None]
    grain = rng.normal(0, 0.55 if calm else 0.85, (h, w, 1)).astype(np.float32)
    img = np.clip(img + grain, 0, 255)
    return Image.fromarray(img.astype(np.uint8), "RGB")


def text_size(text: str, font: ImageFont.FreeTypeFont, tracking: float) -> float:
    if not text:
        return 0
    return sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)


def render_text(text: str, font_path: str, size: int, fill, tracking_em: float = 0.04) -> Image.Image:
    scale = 2
    font = ImageFont.truetype(font_path, size * scale)
    tracking = tracking_em * size * scale
    ascent, descent = font.getmetrics()
    width = int(text_size(text, font, tracking)) + 8
    height = ascent + descent + 8
    layer = Image.new("RGBA", (max(width, 1), height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = 2
    for ch in text:
        draw.text((x, 2), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return layer.resize((max(1, layer.width // scale), max(1, layer.height // scale)), Image.Resampling.LANCZOS)


def gradient_rule(length: int, thickness: int = 2, vertical: bool = False) -> Image.Image:
    length = max(2, int(length))
    thickness = max(1, int(thickness))
    if vertical:
        arr = np.zeros((length, thickness, 4), np.uint8)
        for i in range(length):
            t = i / (length - 1)
            col = (
                int(90 + (188 - 90) * t),
                int(214 + (92 - 214) * t),
                int(255 + (255 - 255) * t),
                230,
            )
            arr[i, :, :] = col
        im = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.4))
        return im
    arr = np.zeros((thickness, length, 4), np.uint8)
    for i in range(length):
        t = i / (length - 1)
        arr[:, i, :] = (
            int(90 + (188 - 90) * t),
            int(214 + (92 - 214) * t),
            255,
            230,
        )
    return Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.4))


def paste(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    base.paste(overlay, (int(xy[0]), int(xy[1])), overlay)


def with_shadow(im: Image.Image, radius: int = 10, dy: int = 6, opacity: float = 0.45) -> Image.Image:
    alpha = im.split()[-1]
    shadow = Image.new("RGBA", im.size, (0, 0, 0, int(255 * opacity)))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
    canvas = Image.new("RGBA", (im.width, im.height + dy + radius), (0, 0, 0, 0))
    canvas.paste(shadow, (0, dy), shadow)
    canvas.paste(im, (0, 0), im)
    return trim(canvas, pad=0)


def lockup(prism: Image.Image, word: Image.Image, prism_h: int, gap: int | None = None) -> Image.Image:
    p = fit(prism, prism_h)
    w = fit(word, int(prism_h * 0.46))
    w = with_shadow(w, radius=max(4, prism_h // 32), dy=max(2, prism_h // 55), opacity=0.28)
    gap = int(prism_h * 0.07) if gap is None else gap
    height = max(p.height, w.height)
    canvas = Image.new("RGBA", (p.width + gap + w.width, height), (0, 0, 0, 0))
    paste(canvas, p, (0, (height - p.height) // 2))
    paste(canvas, w, (p.width + gap, (height - w.height) // 2 - int(prism_h * 0.02)))
    return canvas


def stack_mark(prism: Image.Image, word: Image.Image, prism_h: int, gap: int | None = None) -> Image.Image:
    p = fit(prism, prism_h)
    w = fit(word, int(prism_h * 0.34))
    w = with_shadow(w, radius=max(4, prism_h // 34), dy=max(2, prism_h // 60), opacity=0.28)
    gap = int(prism_h * 0.06) if gap is None else gap
    width = max(p.width, w.width)
    canvas = Image.new("RGBA", (width, p.height + gap + w.height), (0, 0, 0, 0))
    paste(canvas, p, ((width - p.width) // 2, 0))
    paste(canvas, w, ((width - w.width) // 2, p.height + gap))
    return canvas


def meta_block(lines: list[tuple[str, str, int, float]], align: str = "left") -> Image.Image:
    rendered = []
    for text, font, size, tracking in lines:
        face = FONT_MED if font == "med" else FONT_REG if font == "reg" else FONT_SEM
        fill = INK if font != "reg" else MUTED
        rendered.append(render_text(text, face, size, fill, tracking))
    if not rendered:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    gap = max(6, rendered[0].height // 5)
    width = max(r.width for r in rendered)
    height = sum(r.height for r in rendered) + gap * (len(rendered) - 1)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    y = 0
    for r in rendered:
        x = 0 if align == "left" else (width - r.width) // 2
        paste(canvas, r, (x, y))
        y += r.height + gap
    return canvas


def compose(bg: Image.Image, layer: Image.Image, xy: tuple[int, int]) -> Image.Image:
    out = bg.convert("RGBA")
    paste(out, layer, xy)
    return out


def save_pair(im: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = im.convert("RGB") if im.mode != "RGB" else im
    rgb.save(path.with_suffix(".png"), optimize=True)
    rgb.save(path.with_suffix(".jpg"), quality=92, subsampling=0, optimize=True)


def downscale(im: Image.Image, w: int, h: int) -> Image.Image:
    if im.size == (w, h):
        return im
    return im.resize((w, h), Image.Resampling.LANCZOS)


def render_at(w: int, h: int, draw_fn, scale: int = 2) -> Image.Image:
    hi = draw_fn(w * scale, h * scale)
    return downscale(hi, w, h)


def wide_piece(w, h, prism, word, lines, safe_left=0.0, safe_right=0.06, anchor=None, calm=False):
    def scaled_lines(H):
        return [(text, font, max(13, int(size * H / h)), tracking) for text, font, size, tracking in lines]

    def draw(W, H):
        ax = 0.28 + safe_left * 0.35
        bg = paint_scene(W, H, anchor=anchor or (ax, 0.5), calm=calm)
        left = int(W * safe_left)
        right = int(W * safe_right)
        footer = H / W > 0.42
        block = meta_block(scaled_lines(H), align="center" if footer else "left")
        if footer:
            group = lockup(prism, word, int(H * 0.56))
            max_w = int((W - left - right) * 0.94)
            if group.width > max_w:
                group = fit(group, int(group.height * max_w / group.width))
            gap = int(H * 0.05)
            total_h = group.height + gap + block.height
            limit = int(H * 0.84)
            if total_h > limit:
                group = fit(group, max(1, group.height - (total_h - limit)))
                total_h = group.height + gap + block.height
            y = (H - total_h) // 2
            out = compose(bg, group, ((W - group.width) // 2, y))
            paste(out, block, ((W - block.width) // 2, y + group.height + gap))
            return out.convert("RGB")

        prism_h = int(H * 0.72)
        group = lockup(prism, word, prism_h)
        if group.height > int(H * 0.86):
            group = fit(group, int(H * 0.84))
        gap = int(W * 0.028)
        rule = gradient_rule(int(group.height * 0.42), thickness=max(2, H // 180), vertical=True)
        avail = W - left - right
        max_group = avail - gap - rule.width - gap - block.width
        if max_group > 40 and group.width > max_group:
            group = fit(group, int(group.height * max_group / group.width))
            rule = gradient_rule(int(group.height * 0.42), thickness=max(2, H // 180), vertical=True)
        total = group.width + gap + rule.width + gap + block.width
        x = left if safe_left >= 0.16 else left + max(0, (avail - total) // 2)
        y = (H - group.height) // 2
        out = compose(bg, group, (x, y))
        rx = x + group.width + gap
        paste(out, rule, (rx, y + (group.height - rule.height) // 2))
        paste(out, block, (rx + rule.width + gap, y + (group.height - block.height) // 2))
        return out.convert("RGB")

    return render_at(w, h, draw, scale=2 if w * h < 2_200_000 else 1)


def stack_piece(w, h, prism, word, lines, top_safe=0.08, bottom_safe=0.08):
    def draw(W, H):
        bg = paint_scene(
            W,
            H,
            anchor=(0.5, 0.40),
            beams=[
                ((0.0, 0.14), (0.38, 0.0), 0.018, (160, 215, 255), 0.38),
                ((0.62, 1.02), (1.0, 0.74), 0.016, (210, 225, 255), 0.32),
            ],
        )
        prism_h = int(H * (0.46 if H > W * 1.4 else 0.50 if H > W else 0.46))
        mark = stack_mark(prism, word, prism_h)
        block = meta_block(
            [(text, font, max(14, int(size * min(W, H) / 1080)), tracking) for text, font, size, tracking in lines],
            align="center",
        )
        rule_w = int(min(W, mark.width) * 0.28)
        rule = gradient_rule(rule_w, thickness=max(2, min(W, H) // 400))
        gap1 = int(prism_h * 0.07)
        gap2 = int(prism_h * 0.055)
        total_h = mark.height + gap1 + rule.height + gap2 + block.height
        max_h = int(H * (1 - top_safe - bottom_safe))
        if total_h > max_h:
            scale = max_h / total_h
            mark = mark.resize((max(1, int(mark.width * scale)), max(1, int(mark.height * scale))), Image.Resampling.LANCZOS)
            total_h = mark.height + gap1 + rule.height + gap2 + block.height
        y = int(H * top_safe) + max(0, (int(H * (1 - bottom_safe)) - int(H * top_safe) - total_h) // 2)
        out = compose(bg, mark, ((W - mark.width) // 2, y))
        y += mark.height + gap1
        paste(out, rule, ((W - rule.width) // 2, y))
        y += rule.height + gap2
        paste(out, block, ((W - block.width) // 2, y))
        return out.convert("RGB")

    return render_at(w, h, draw, scale=2 if w * h < 2_200_000 else 1)


def avatar_piece(size: int, prism: Image.Image, ring: bool = False) -> Image.Image:
    def draw(S, _h):
        bg = paint_scene(S, S, anchor=(0.5, 0.48), calm=True)
        # O recorte circular das redes usa o círculo inscrito. A largura do prisma é o limite.
        p = fit(prism, int(S * 0.60))
        if p.width > int(S * 0.66):
            p = p.resize((int(S * 0.66), max(1, int(p.height * S * 0.66 / p.width))), Image.Resampling.LANCZOS)
        # Halo extra, só cor, atrás do cristal.
        glow = p.resize((int(p.width * 1.35), int(p.height * 1.35)), Image.Resampling.LANCZOS)
        glow = glow.filter(ImageFilter.GaussianBlur(max(8, S // 40)))
        out = bg.convert("RGBA")
        paste(out, glow, ((S - glow.width) // 2, (S - glow.height) // 2 + int(S * 0.02)))
        paste(out, p, ((S - p.width) // 2, (S - p.height) // 2))
        if ring:
            overlay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            d = ImageDraw.Draw(overlay)
            inset = int(S * 0.045)
            d.ellipse((inset, inset, S - inset, S - inset), outline=(120, 210, 255, 210), width=max(2, S // 180))
            out = Image.alpha_composite(out, overlay)
        return out.convert("RGB")

    return render_at(size, size, draw, scale=2 if size <= 1080 else 1)


def circle_mask(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    mask = Image.new("L", rgba.size, 0)
    ImageDraw.Draw(mask).ellipse((1, 1, rgba.width - 2, rgba.height - 2), fill=255)
    rgba.putalpha(mask)
    return rgba


def signature_piece(w, h, prism, word) -> Image.Image:
    def draw(W, H):
        bg = paint_scene(W, H, anchor=(0.16, 0.5), calm=True, beams=[
            ((0.0, 0.0), (0.28, 0.15), 0.02, (140, 210, 255), 0.45),
        ])
        group = lockup(prism, word, int(H * 0.72))
        lines = meta_block(
            [
                (SITE, "med", max(15, H // 11), 0.045),
                (HANDLE, "reg", max(13, H // 13), 0.06),
                (EMAIL, "reg", max(13, H // 13), 0.04),
            ]
        )
        gap = int(W * 0.03)
        rule = gradient_rule(int(H * 0.46), thickness=max(2, H // 90), vertical=True)
        x = int(W * 0.05)
        out = compose(bg, group, (x, (H - group.height) // 2))
        rx = x + group.width + gap
        paste(out, rule, (rx, (H - rule.height) // 2))
        paste(out, lines, (rx + rule.width + gap, (H - lines.height) // 2))
        return out.convert("RGB")

    return render_at(w, h, draw, scale=2)


def youtube_piece(prism, word) -> Image.Image:
    w, h = 2560, 1440
    bg = paint_scene(
        w,
        h,
        anchor=(0.5, 0.5),
        beams=[
            ((0.0, 0.2), (0.26, 0.0), 0.012, (160, 215, 255), 0.4),
            ((0.74, 1.0), (1.0, 0.66), 0.011, (220, 230, 255), 0.34),
        ],
    )
    # Área segura visível em TV, desktop e celular.
    safe_w, safe_h = 1500, 400
    group = lockup(prism, word, int(safe_h * 0.78))
    block = meta_block(
        [
            (SITE, "med", 28, 0.08),
            (HANDLE, "reg", 22, 0.1),
            (EMAIL, "reg", 22, 0.06),
        ]
    )
    gap = 36
    rule = gradient_rule(int(group.height * 0.46), thickness=3, vertical=True)
    total = group.width + gap + rule.width + gap + block.width
    if total > safe_w:
        group = fit(group, int(group.height * safe_w * 0.62 / group.width))
        total = group.width + gap + rule.width + gap + block.width
    x = (w - total) // 2
    y = (h - group.height) // 2
    out = compose(bg, group, (x, y))
    rx = x + group.width + gap
    paste(out, rule, (rx, y + (group.height - rule.height) // 2))
    paste(out, block, (rx + rule.width + gap, y + (group.height - block.height) // 2))
    return out.convert("RGB")


def horizontal_master(prism, word) -> Image.Image:
    return lockup(prism, word, 900)


def vertical_master(prism, word) -> Image.Image:
    return stack_mark(prism, word, 900)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    prism = extract_prism()
    word = extract_wordmark()
    (OUT / "marca").mkdir()
    prism.save(OUT / "marca/prisma.png")
    word.save(OUT / "marca/wordmark-nexora-prism.png")
    horizontal_master(prism, word).save(OUT / "marca/assinatura-horizontal.png")
    vertical_master(prism, word).save(OUT / "marca/assinatura-vertical.png")
    originais = OUT / "marca/originais"
    originais.mkdir()
    shutil.copy(SRC_PRISM, originais / "prisma-original-900x1600.png")
    shutil.copy(SRC_LOCKUP, originais / "assinatura-original-1254.png")

    manifesto = []

    def add(group, title, filename, image, uso, transparent=False):
        path = OUT / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if transparent:
            image.save(path, optimize=True)
            kind = "png"
        else:
            save_pair(image, path)
            kind = "png+jpg"
        manifesto.append(
            {
                "grupo": group,
                "titulo": title,
                "arquivo": filename.replace("\\", "/"),
                "largura": image.width,
                "altura": image.height,
                "uso": uso,
                "formato": kind,
            }
        )

    # Avatares — só o prisma, folga para o recorte circular.
    for size, name, uso in [
        (1080, "avatar-prisma-1080.png", "Arquivo principal para foto de perfil. O prisma já fica dentro do círculo."),
        (640, "avatar-prisma-640.png", "Perfil do WhatsApp e usos médios."),
        (400, "avatar-prisma-400.png", "Foto de perfil do LinkedIn."),
        (320, "avatar-prisma-320.png", "Foto de perfil do Instagram."),
    ]:
        add("avatares", "Avatares", f"avatares/{name}", avatar_piece(size, prism), uso)

    add(
        "avatares",
        "Avatares",
        "avatares/avatar-prisma-circular-1080.png",
        circle_mask(avatar_piece(1080, prism)),
        "Versão com o fundo já recortado em círculo, para peças e slides.",
        transparent=True,
    )
    add(
        "avatares",
        "Avatares",
        "avatares/destaque-instagram-1080.png",
        avatar_piece(1080, prism, ring=True),
        "Capa de destaque do Instagram. O anel fica visível no círculo.",
    )
    add("avatares", "Avatares", "avatares/favicon-512.png", avatar_piece(512, prism), "Ícone do site e atalho de app.")
    add("avatares", "Avatares", "avatares/apple-touch-180.png", avatar_piece(180, prism), "Ícone para a tela de início do celular.")

    site_handle = [
        (SITE, "med", 26, 0.09),
        (HANDLE, "reg", 20, 0.11),
    ]
    site_email = [
        (SITE, "med", 26, 0.09),
        (EMAIL, "reg", 20, 0.06),
    ]
    all_three = [
        (SITE, "med", 26, 0.09),
        (HANDLE, "reg", 20, 0.11),
        (EMAIL, "reg", 20, 0.05),
    ]
    stack_simple = [
        (SITE, "med", 34, 0.12),
        (HANDLE, "reg", 26, 0.14),
    ]
    stack_full = [
        (SITE, "med", 34, 0.12),
        (HANDLE, "reg", 26, 0.14),
        (EMAIL, "reg", 24, 0.06),
    ]

    add(
        "linkedin",
        "LinkedIn",
        "linkedin/capa-pessoal-1584x396.png",
        wide_piece(1584, 396, prism, word, site_handle, safe_left=0.22, safe_right=0.055),
        "Capa do perfil pessoal. A foto redonda cobre o canto inferior esquerdo, então a marca fica mais à direita.",
    )
    add(
        "linkedin",
        "LinkedIn",
        "linkedin/capa-pessoal-contato-1584x396.png",
        wide_piece(1584, 396, prism, word, site_email, safe_left=0.22, safe_right=0.05),
        "Mesma capa, com o e-mail no lugar do @.",
    )
    add(
        "linkedin",
        "LinkedIn",
        "linkedin/capa-empresa-1128x191.png",
        wide_piece(1128, 191, prism, word, [(SITE, "med", 18, 0.08), (HANDLE, "reg", 15, 0.08)], safe_left=0.16, safe_right=0.04),
        "Capa da página da empresa. O logotipo da página cobre a esquerda.",
    )
    add(
        "linkedin",
        "LinkedIn",
        "linkedin/post-paisagem-1200x627.png",
        wide_piece(1200, 627, prism, word, all_three, safe_left=0.06, safe_right=0.06, anchor=(0.32, 0.48)),
        "Imagem de post horizontal.",
    )
    add(
        "linkedin",
        "LinkedIn",
        "linkedin/post-quadrado-1200x1200.png",
        stack_piece(1200, 1200, prism, word, stack_full),
        "Post quadrado.",
    )
    add(
        "linkedin",
        "LinkedIn",
        "linkedin/artigo-1920x1080.png",
        wide_piece(1920, 1080, prism, word, all_three, safe_left=0.08, safe_right=0.08, anchor=(0.3, 0.5)),
        "Capa de artigo e apresentações 16:9.",
    )

    add(
        "instagram",
        "Instagram",
        "instagram/feed-quadrado-1080x1080.png",
        stack_piece(1080, 1080, prism, word, stack_simple),
        "Post do feed, quadrado, com site e @.",
    )
    add(
        "instagram",
        "Instagram",
        "instagram/feed-quadrado-contato-1080x1080.png",
        stack_piece(1080, 1080, prism, word, stack_full),
        "Post do feed com site, @ e e-mail.",
    )
    add(
        "instagram",
        "Instagram",
        "instagram/feed-retrato-1080x1350.png",
        stack_piece(1080, 1350, prism, word, stack_full, top_safe=0.09, bottom_safe=0.08),
        "Post vertical do feed, o formato que ocupa mais tela.",
    )
    add(
        "instagram",
        "Instagram",
        "instagram/story-1080x1920.png",
        stack_piece(1080, 1920, prism, word, stack_simple, top_safe=0.16, bottom_safe=0.18),
        "Story e capa de Reel. O conteúdo fica fora da área da interface.",
    )
    add(
        "instagram",
        "Instagram",
        "instagram/story-contato-1080x1920.png",
        stack_piece(1080, 1920, prism, word, stack_full, top_safe=0.16, bottom_safe=0.18),
        "Story com site, @nexoraprism_ e e-mail.",
    )

    add(
        "outras-redes",
        "Outras redes",
        "outras-redes/x-capa-1500x500.png",
        wide_piece(1500, 500, prism, word, all_three, safe_left=0.18, safe_right=0.05, anchor=(0.34, 0.46)),
        "Capa do X. A foto de perfil cobre o canto inferior esquerdo.",
    )
    add(
        "outras-redes",
        "Outras redes",
        "outras-redes/facebook-capa-1640x624.png",
        wide_piece(1640, 624, prism, word, all_three, safe_left=0.2, safe_right=0.05),
        "Capa do Facebook em dobro da medida clássica, para ficar nítida.",
    )
    add(
        "outras-redes",
        "Outras redes",
        "outras-redes/youtube-capa-2560x1440.png",
        youtube_piece(prism, word),
        "Capa do YouTube. A marca fica na faixa central que aparece em TV e celular.",
    )

    add(
        "web",
        "Site e e-mail",
        "web/compartilhamento-1200x630.png",
        wide_piece(1200, 630, prism, word, site_handle, safe_left=0.07, safe_right=0.06, anchor=(0.3, 0.5)),
        "Imagem de compartilhamento do link nexoraprism.com.br (Open Graph).",
    )
    add(
        "web",
        "Site e e-mail",
        "web/assinatura-email-840x220.png",
        signature_piece(840, 220, prism, word),
        "Faixa para assinatura de e-mail. Use como imagem.",
    )

    # Mestres transparentes entram no manifesto sem jpg.
    marca = []
    for filename, uso, im in [
        ("marca/prisma.png", "Prisma isolado, fundo transparente.", prism),
        ("marca/wordmark-nexora-prism.png", "Lettering original isolado, fundo transparente.", word),
        ("marca/assinatura-horizontal.png", "Prisma e lettering lado a lado, fundo transparente.", horizontal_master(prism, word)),
        ("marca/assinatura-vertical.png", "Prisma e lettering empilhados, fundo transparente.", vertical_master(prism, word)),
    ]:
        marca.append(
            {
                "grupo": "marca",
                "titulo": "Marca",
                "arquivo": filename,
                "largura": im.width,
                "altura": im.height,
                "uso": uso,
                "formato": "png",
            }
        )
    manifesto = marca + manifesto

    (OUT / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"peças: {len(manifesto)}")
    for item in manifesto:
        print(f"  {item['arquivo']:48} {item['largura']}x{item['altura']}")


if __name__ == "__main__":
    main()
