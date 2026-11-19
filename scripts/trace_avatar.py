#!/usr/bin/env python3
"""Trace a black-and-white line drawing (PNG/JPG, white background) into scripts/efe_avatar.json.

The footer draws it as two paths: a paper-coloured silhouette (so the walking crowd passes behind the
figure) and the black ink on top. Run once per new drawing; the image itself is never committed.

Optional --regions JSON ({"dark": [[[x, y], ...], ...], "light": [...]}, source-pixel polygons) paints
clothing solid black like the reference GIF: inside "dark" (minus "light", e.g. hands) the drawing's own
fold lines turn into soft highlights.

usage: py -3 scripts/trace_avatar.py <drawing.png> [--regions regions.json] [--threshold 128] [--height 800]
needs: pip install opencv-python numpy
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def smooth_path(contours, eps):
    """Closed contours → one SVG path; corners are rounded with quadratic curves through edge midpoints."""
    out = []
    for c in contours:
        c = cv2.approxPolyDP(c, eps, True).reshape(-1, 2).astype(float)
        if len(c) < 3:
            continue
        mids = (c + np.roll(c, -1, axis=0)) / 2
        seg = [f"M{mids[-1][0]:.1f} {mids[-1][1]:.1f}"]
        for p, m in zip(c, mids):
            seg.append(f"Q{p[0]:.1f} {p[1]:.1f} {m[0]:.1f} {m[1]:.1f}")
        out.append("".join(seg) + "Z")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--regions")
    ap.add_argument("--gap-from", type=float, default=0.5, help="look for see-through gaps below this height fraction")
    ap.add_argument("--min-line", type=int, default=10, help="drop ink specks smaller than this (px²)")
    ap.add_argument("--out", default=str(ROOT / "scripts" / "efe_avatar.json"))
    a = ap.parse_args()

    img = cv2.imread(a.image, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"can't read {a.image}")
    if img.ndim == 3 and img.shape[2] == 4:            # transparent PNG: alpha is the silhouette
        alpha = img[:, :, 3]
        rgb = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
        gray = np.where(alpha > 10, rgb, 255).astype(np.uint8)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

    ink = (cv2.GaussianBlur(gray, (0, 0), 0.8) < a.threshold).astype(np.uint8) * 255
    dark, bgm = np.zeros_like(ink), np.zeros_like(ink)
    if a.regions:
        reg = json.loads(Path(a.regions).read_text(encoding="utf-8"))
        for poly in reg.get("dark", []):
            cv2.fillPoly(dark, [np.array(poly, np.int32)], 255)
        for poly in reg.get("light", []):
            cv2.fillPoly(dark, [np.array(poly, np.int32)], 0)
        for poly in reg.get("bg", []):                  # see-through gaps (e.g. between the legs)
            cv2.fillPoly(bgm, [np.array(poly, np.int32)], 255)
    ys, xs = np.where(ink > 0)
    pad = 4
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, ink.shape[0] - 1)
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, ink.shape[1] - 1)
    ink, dark, bgm = ink[y0:y1 + 1, x0:x1 + 1], dark[y0:y1 + 1, x0:x1 + 1], bgm[y0:y1 + 1, x0:x1 + 1]
    dark_src = dark.copy()
    s = a.height / ink.shape[0]
    ink = cv2.resize(ink, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    ink = ((ink > 127) * 255).astype(np.uint8)
    dark = ((cv2.resize(dark, (ink.shape[1], ink.shape[0]), interpolation=cv2.INTER_AREA) > 127) * 255).astype(np.uint8)
    bgm = ((cv2.resize(bgm, (ink.shape[1], ink.shape[0]), interpolation=cv2.INTER_AREA) > 127) * 255).astype(np.uint8)
    h, w = ink.shape

    # silhouette: every non-white pixel, sealed with a wide close so gaps in the outline can't leak,
    # holes filled, largest blob kept (computed on the cropped source, then scaled like the ink)
    src = gray[y0:y1 + 1, x0:x1 + 1]
    nonwhite = ((src < 242) * 255).astype(np.uint8)
    k = max(9, int(round(src.shape[0] / 60)) | 1)
    nonwhite = cv2.morphologyEx(nonwhite, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    flood = np.pad(255 - nonwhite, 1, constant_values=255)
    ffmask = np.zeros((flood.shape[0] + 2, flood.shape[1] + 2), np.uint8)
    cv2.floodFill(flood, ffmask, (0, 0), 128)
    sil = ((flood[1:-1, 1:-1] != 128) * 255).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(sil)
    if n > 1:
        sil = ((lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])) * 255).astype(np.uint8)
    # see-through gaps the close sealed (between the legs, arm and torso): big patches of clean paper white
    f32 = src.astype(np.float32)
    mean = cv2.blur(f32, (9, 9))
    std = np.sqrt(np.maximum(cv2.blur(f32 * f32, (9, 9)) - mean * mean, 0))
    paper_bg = float(np.median(src[:8, :]))              # the drawing's own background tone
    gaps = (((mean >= paper_bg - 6) & (std <= 3.5)) * 255).astype(np.uint8) & sil & cv2.bitwise_not(dark_src)
    gaps[: int(src.shape[0] * a.gap_from), :] = 0         # skin highlights up top are not gaps
    gaps = cv2.morphologyEx(gaps, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(gaps)
    min_gap = src.shape[0] * src.shape[1] * 0.0012
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_gap:
            sil[lab == i] = 0
    # trim thin spikes (stray curls) from the paper fill, keep the main body only
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k // 2 | 1, k // 2 | 1)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(sil, connectivity=4)
    if n > 1:
        sil = ((lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])) * 255).astype(np.uint8)
    sil = ((cv2.resize(sil, (w, h), interpolation=cv2.INTER_AREA) > 127) * 255).astype(np.uint8)
    sil = cv2.bitwise_and(sil, cv2.bitwise_not(bgm))

    dark = cv2.bitwise_and(dark, sil)
    ink = cv2.bitwise_and(ink, cv2.dilate(sil, np.ones((7, 7), np.uint8)))   # no floating strokes

    def clean(m, min_area):
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        out = np.zeros_like(m)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= min_area:
                out[lab == i] = 255
        return out

    line_out = clean(cv2.bitwise_and(ink, cv2.bitwise_not(dark)), a.min_line)
    # inside the black clothing, the drawing's folds become thin highlights (eroded so they stay delicate)
    hl = cv2.erode(cv2.bitwise_and(ink, dark), np.ones((2, 2), np.uint8))
    hl = clean(cv2.bitwise_and(hl, cv2.erode(dark, np.ones((5, 5), np.uint8))), a.min_line * 3)

    def path(m, eps, mode=cv2.RETR_CCOMP):
        c, _ = cv2.findContours(m, mode, cv2.CHAIN_APPROX_NONE)
        return smooth_path(c, eps)

    data = {
        "_source": "Efe's own drawing, traced by scripts/trace_avatar.py",
        "w": w, "h": h,
        "paper": path(sil, 1.2),
        "dark": path(dark, 1.0) if dark.any() else "",
        "hl": path(hl, 0.8) if hl.any() else "",
        "ink": path(line_out, 0.8),
    }
    Path(a.out).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    kb = " - ".join(f"{k} {len(data[k]) // 1024} KB" for k in ("paper", "dark", "hl", "ink"))
    print(f"{w}x{h} - {kb} -> {a.out}")


if __name__ == "__main__":
    main()
