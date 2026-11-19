#!/usr/bin/env python3
"""Builds the animated SVG panels for github.com/efebiskin.

- Every word is drawn as a vector path from the brand fonts (Archivo,
  Instrument Serif, JetBrains Mono; all SIL OFL, see scripts/fonts/OFL-*.txt),
  so the panels look the same in every browser and need no web fonts.
- Every number comes from the GitHub API at build time. Nothing is typed in.
- Runs locally or in .github/workflows/profile.yml (daily).

needs: pip install fonttools pillow     env: GITHUB_TOKEN
"""
import datetime as dt
import html
import io
import json
import math
import os
import random
import sys
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
USER = os.environ.get("PROFILE_USER", "efebiskin")

# Biskin Studio palette
BG, BAR, EDGE = "#0A0A0A", "#101209", "#22271A"
LIME, LIME2, LIME3, LIME4 = "#C8FF00", "#9CCC00", "#6E8F00", "#3F5200"
CREAM, MUTED, DIM, RED = "#F5F1E8", "#8C8F80", "#4A4E40", "#FF4F36"
W = 1000


def num(v):
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


def esc(s):
    return html.escape(s, quote=True)


# ───────────────────────────── fonts → paths ─────────────────────────────
class Face:
    def __init__(self, file, axes=None):
        f = TTFont(FONTS / file)
        if axes and "fvar" in f:
            f = instancer.instantiateVariableFont(f, axes)
        self.gs = f.getGlyphSet()
        self.cmap = f.getBestCmap()
        self.upm = f["head"].unitsPerEm
        self.hmtx = f["hmtx"]
        self.fallback = self.cmap.get(ord("?"))

    def _g(self, ch):
        return self.cmap.get(ord(ch), self.fallback)

    def width(self, text, size, track=0.0):
        s = size / self.upm
        return sum(self.hmtx[self._g(c)][0] * s + track for c in text) - (track if text else 0)

    def path(self, text, size, x, y, track=0.0, anchor="start"):
        w = self.width(text, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upm
        pen = SVGPathPen(self.gs, ntos=num)
        cx = x
        for c in text:
            g = self._g(c)
            if c != " ":
                self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            cx += self.hmtx[g][0] * s + track
        return pen.getCommands(), w

    def fit(self, text, size, maxw, track=0.0):
        while size > 8 and self.width(text, size, track) > maxw:
            size -= 0.5
        return size


print("loading fonts …", flush=True)
DISPLAY = Face("Archivo.ttf", {"wght": 900, "wdth": 125})
HEAVY = Face("Archivo.ttf", {"wght": 800, "wdth": 100})
SERIF = Face("InstrumentSerif-Italic.ttf")
MONO = Face("JetBrainsMono.ttf", {"wght": 400})
MONOB = Face("JetBrainsMono.ttf", {"wght": 700})


def P(face, text, size, x, y, fill, track=0.0, anchor="start", cls="", extra=""):
    d, w = face.path(text, size, x, y, track, anchor)
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{d}" fill="{fill}"{extra}/>', w


def segs(face, parts, size, x, y, track=0.0):
    """parts = [(text, color), …] laid out left to right. Returns (svg, total width)."""
    out, cx = [], x
    for text, color in parts:
        p, w = P(face, text, size, cx, y, color, track)
        out.append(p)
        cx += w + (track if text else 0)
    return "".join(out), cx - x


class Ids:
    def __init__(self, prefix):
        self.p, self.n = prefix, 0

    def __call__(self):
        self.n += 1
        return f"{self.p}{self.n}"


def typed(ids, parts, size, x, y, begin, cps=32.0, face=None):
    """A terminal line that types itself (SMIL clip reveal, monospace steps)."""
    face = face or MONO
    body, w = segs(face, parts, size, x, y)
    n = max(1, sum(len(t) for t, _ in parts))
    cw = w / n
    dur = n / cps
    vals = ";".join(num(i * cw + (3 if i == n else 0)) for i in range(n + 1))
    kts = ";".join(f"{i / n:.4f}" for i in range(n + 1))
    cid = ids()
    clip = (f'<clipPath id="{cid}"><rect x="{num(x - 1)}" y="{num(y - size * 1.05)}" width="0" height="{num(size * 1.5)}">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kts}" dur="{dur:.2f}s" begin="{begin:.2f}s" '
            f'fill="freeze" calcMode="discrete"/></rect></clipPath>')
    return clip, f'<g clip-path="url(#{cid})">{body}</g>', begin + dur, x + w


def cursor(x, y, size, begin):
    h = size * 1.15
    return (f'<rect class="cur" x="{num(x + 3)}" y="{num(y - size * 0.92)}" width="{num(size * 0.58)}" height="{num(h)}" '
            f'fill="{LIME}" style="animation-delay:{begin:.2f}s"/>')


BASE_CSS = f"""
.cur{{opacity:0;animation:blink 1.06s steps(1) infinite}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
.scan{{animation:scan 7s linear infinite}}
@keyframes scan{{from{{transform:translateY(-120px)}}to{{transform:translateY(var(--h))}}}}
.fade{{opacity:0;animation:fade .7s ease-out forwards}}
@keyframes fade{{to{{opacity:1}}}}
.up{{opacity:0;animation:up .8s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes up{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:none}}}}
"""


def window(w, h, title, inner, css="", uid="w"):
    """Terminal window chrome around a panel."""
    t, _ = P(MONO, title, 12, w / 2, 23, MUTED, anchor="middle")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>{BASE_CSS}{css}</style>
<defs>
<clipPath id="{uid}clip"><rect width="{w}" height="{h}" rx="14"/></clipPath>
<pattern id="{uid}dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="{LIME}" fill-opacity=".07"/></pattern>
<linearGradient id="{uid}scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{LIME}" stop-opacity="0"/><stop offset=".5" stop-color="{LIME}" stop-opacity=".055"/><stop offset="1" stop-color="{LIME}" stop-opacity="0"/></linearGradient>
</defs>
<g clip-path="url(#{uid}clip)">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect y="36" width="{w}" height="{h - 36}" fill="url(#{uid}dots)"/>
<rect width="{w}" height="36" fill="{BAR}"/><rect y="36" width="{w}" height="1" fill="{EDGE}"/>
<circle cx="22" cy="18" r="6" fill="{RED}"/><circle cx="42" cy="18" r="6" fill="{CREAM}" fill-opacity=".85"/><circle cx="62" cy="18" r="6" fill="{LIME}"/>
{t}
{inner}
<rect class="scan" style="--h:{h + 120}px" width="{w}" height="120" fill="url(#{uid}scan)"/>
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{EDGE}"/>
</svg>
"""


# ───────────────────────────── GitHub data ─────────────────────────────
def gql(query, variables):
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not tok:
        sys.exit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {tok}", "User-Agent": "profile-builder"},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    if data.get("errors"):
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]


Q = """query($login:String!){ user(login:$login){
  avatarUrl(size:460)
  contributionsCollection{ contributionCalendar{ totalContributions
    weeks{ contributionDays{ date weekday contributionCount } } } }
  repositories(first:100, privacy:PUBLIC, ownerAffiliations:OWNER, isFork:false){
    nodes{ name stargazerCount isArchived primaryLanguage{ name } } } } }"""


def load_stats():
    u = gql(Q, {"login": USER})["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = [w["contributionDays"] for w in cal["weeks"]]
    days = [d for w in weeks for d in w]
    best = max(days, key=lambda d: d["contributionCount"])
    # streaks
    longest = run = 0
    lstart = lend = cur_start = None
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            cur_start = cur_start if run > 1 else d["date"]
            if run > longest:
                longest, lstart, lend = run, cur_start, d["date"]
        else:
            run = 0
    tail = list(reversed(days))
    if tail and tail[0]["contributionCount"] == 0:
        tail = tail[1:]  # today not counted yet
    current = 0
    for d in tail:
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
    repos = [r for r in u["repositories"]["nodes"] if r["name"].lower() != USER.lower() and not r["isArchived"]]
    langs = Counter(r["primaryLanguage"]["name"] for r in repos if r["primaryLanguage"])
    return {
        "avatar": u["avatarUrl"], "weeks": weeks, "total": cal["totalContributions"], "best": best,
        "active": sum(1 for d in days if d["contributionCount"] > 0), "longest": longest,
        "lrange": (lstart, lend), "current": current, "months": months,
        "repos": len(repos), "stars": sum(r["stargazerCount"] for r in repos),
        "repo_stars": {r["name"]: r["stargazerCount"] for r in repos},
        "langs": langs.most_common(), "today": days[-1]["date"],
    }


def fmt_date(s):
    d = dt.date.fromisoformat(s)
    return d.strftime("%b ") + str(d.day)


# ───────────────────────────── hero ─────────────────────────────
def _rdp(pts, eps):
    """Ramer-Douglas-Peucker: drop points that sit on a straight run."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-9
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)


def _band(xs, yc, ts):
    top = _rdp([(x, yc - t / 2) for x, t in zip(xs, ts)], 0.12)
    bot = _rdp([(x, yc + t / 2) for x, t in zip(xs, ts)], 0.12)[::-1]
    pts = top + bot
    return "M" + "L".join(f"{num(a)} {num(b)}" for a, b in pts) + "Z"


def engraving(avatar_bytes, x, y, w, h, rows=72, samples=150):
    """Line-engraving portrait: one lime band per scanline, thickness = light."""
    im = Image.open(io.BytesIO(avatar_bytes)).convert("L")
    sw, sh = im.size
    # tight crop on the face (tuned on the current avatar; still sane if it changes)
    box = (int(sw * .05), int(sh * .17), int(sw * .80), int(sh * .77))
    im = ImageOps.autocontrast(im.crop(box), cutoff=2).filter(ImageFilter.GaussianBlur(1.0))
    im = im.resize((samples, rows), Image.LANCZOS)
    px = im.load()
    sp = h / rows
    maxt = sp * 0.74
    xs = [x + c * w / (samples - 1) for c in range(samples)]
    out = []
    for r in range(rows):
        fy = r / (rows - 1)
        yc = y + (r + .5) * sp
        ts, hi = [], []
        for c in range(samples):
            fx = c / (samples - 1)
            m = 1.0
            if fy > .72:
                m *= max(.25, 1 - (fy - .72) / .28 * .75)
            if fx > .82:
                m *= max(.45, 1 - (fx - .82) / .18 * .55)
            v = ((px[c, r] / 255) * m) ** 1.8
            ts.append(.12 + maxt * v)
            hi.append(max(0.0, (v - .62) / .38) * maxt * .55)
        lime = _band(xs, yc, ts)
        cream = ""
        if max(hi) > .25:
            cream = f'<path d="{_band(xs, yc, [max(0.0, t) for t in hi])}" fill="{CREAM}"/>'
        cls = "ln gl" if r in (14, 31, 47) else "ln"
        side = -1 if r % 2 else 1
        out.append(f'<g class="{cls}" style="--sx:{side * 26}px;animation-delay:{.25 + r * .018:.3f}s">'
                   f'<path d="{lime}" fill="{LIME}"/>{cream}</g>')
    return "\n".join(out)


def build_hero(stats, avatar):
    H = 420
    ids = Ids("h")
    defs, body = [], []
    c1, t1, end1, x1 = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED), ("cat ./hello.md", CREAM)], 15, 40, 84, 0.35, cps=26)
    defs.append(c1); body.append(t1)
    # name with glitch copies
    for i, (word, base) in enumerate([("EFECAN", 190), ("BISKIN", 286)]):
        d, _ = DISPLAY.path(word, 96, 38, base, track=1)
        delay = end1 + 0.1 + i * 0.16
        body.append(
            f'<g class="up" style="animation-delay:{delay:.2f}s">'
            f'<path class="gr" d="{d}" fill="{RED}"/><path class="gl2" d="{d}" fill="{LIME}"/>'
            f'<path d="{d}" fill="{CREAM}"/></g>')
    tag, tw = segs(SERIF, [("full-stack engineer ", CREAM), ("with ML chops.", LIME)], 36, 40, 338)
    body.append(f'<g class="up" style="animation-delay:{end1 + 0.5:.2f}s">{tag}</g>')

    # cycling roles (type → hold → erase), 4 lines, 16s loop
    roles = ["founder @ Biskin Studio", "game dev @ BEF Games, shipped on Steam",
             "B.S. Computer Science, Cal Lutheran '26", "Python · TypeScript · Three.js · Unity"]
    pre, pw = P(MONOB, ">", 14, 40, 372, LIME)
    body.append(f'<g class="fade" style="animation-delay:{end1 + 0.6:.2f}s">{pre}')
    loop, slot = 16.0, 4.0
    rx = 40 + pw + 10
    for k, role in enumerate(roles):
        d, w = MONO.path(role, 14, rx, 372)
        n = len(role)
        cw = w / n
        t_type, t_hold, t_erase = 0.035 * n, 2.2, 0.012 * n
        pts = []  # (time, width)
        s0 = k * slot
        pts.append((0, 0))
        for i in range(n + 1):
            pts.append((s0 + i * (t_type / n), i * cw + (3 if i == n else 0)))
        pts.append((s0 + t_type + t_hold, w + 3))
        for i in range(n, -1, -4):
            pts.append((s0 + t_type + t_hold + (n - i) * (t_erase / n), max(0, i * cw)))
        pts.append((s0 + t_type + t_hold + t_erase + 0.01, 0))
        pts.append((loop, 0))
        pts = sorted({round(t, 3): v for t, v in pts}.items())
        vals = ";".join(num(v) for _, v in pts)
        kts = ";".join(f"{min(1, t / loop):.4f}" for t, _ in pts)
        cid = ids()
        defs.append(f'<clipPath id="{cid}"><rect x="{num(rx - 1)}" y="356" width="0" height="22">'
                    f'<animate attributeName="width" values="{vals}" keyTimes="{kts}" dur="{loop}s" '
                    f'begin="{end1 + 0.7:.2f}s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath>')
        body.append(f'<g clip-path="url(#{cid})"><path d="{d}" fill="{CREAM if k % 2 == 0 else LIME}"/></g>')
    body.append("</g>")

    # portrait
    px_, py_, pw_, ph_ = 586, 58, 376, 300
    art = engraving(avatar, px_, py_, pw_, ph_)
    br = []
    L = 16
    for (cx, cy, sx, sy) in [(px_ - 10, py_ - 8, 1, 1), (px_ + pw_ + 10, py_ - 8, -1, 1),
                             (px_ - 10, py_ + ph_ + 8, 1, -1), (px_ + pw_ + 10, py_ + ph_ + 8, -1, -1)]:
        br.append(f'<path d="M{cx} {cy + sy * L}V{cy}H{cx + sx * L}" fill="none" stroke="{LIME}" stroke-width="2"/>')
    lab, _ = P(MONO, "avatar → 72 scanlines", 10, px_ + pw_ + 10, py_ + ph_ + 26, DIM, anchor="end")
    rec, _ = P(MONOB, "REC", 10, px_ + 6, py_ + ph_ + 26, RED)
    body.append(f"<g>{art}</g>")
    body.append(f'<g class="fade" style="animation-delay:.2s">{"".join(br)}{lab}'
                f'<circle class="rec" cx="{px_ - 4}" cy="{py_ + ph_ + 22.5}" r="3.5" fill="{RED}"/>{rec}</g>')
    body.append(f'<rect class="pscan" x="{px_ - 10}" y="{py_}" width="{pw_ + 20}" height="2" fill="{LIME}" fill-opacity=".55"/>')

    # marquee
    words = ["FULL-STACK", "MACHINE LEARNING", "WEBGL", "GAME DEV", "SHIPPED ON STEAM", "BISKIN STUDIO",
             "PYTHON", "TYPESCRIPT", "UNITY", "THREE.JS"]
    my, mh = 388, 32
    parts, cx = [], 0.0
    for wd in words:
        p, w = P(HEAVY, wd, 15, cx, my + 21.5, BG, track=1.2)
        parts.append(p)
        cx += w + 18
        parts.append(f'<rect x="{num(cx - 4)}" y="{my + 12}" width="8" height="8" transform="rotate(45 {num(cx)} {my + 16})" fill="{BG}"/>')
        cx += 22
    Lm = cx
    strip = "".join(parts)
    body.append(f'<rect y="{my}" width="{W}" height="{mh}" fill="{LIME}"/>'
                f'<g class="mq" style="--L:-{num(Lm)}px"><g>{strip}</g><g transform="translate({num(Lm)} 0)">{strip}</g>'
                f'<g transform="translate({num(2 * Lm)} 0)">{strip}</g></g>')

    css = f"""
.ln{{opacity:0;animation:lnin .6s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes lnin{{from{{opacity:0;transform:translateX(var(--sx))}}to{{opacity:1;transform:none}}}}
.gl{{animation:lnin .6s cubic-bezier(.2,.8,.2,1) forwards, jit 5.5s steps(1) 2s infinite}}
@keyframes jit{{0%,90%{{transform:none}}91%{{transform:translateX(-9px)}}93%{{transform:translateX(6px)}}95%{{transform:none}}}}
.gr{{animation:gr 4.8s steps(1) infinite}}.gl2{{animation:gl2 4.8s steps(1) infinite}}
@keyframes gr{{0%,86%{{transform:none;opacity:0}}87%{{transform:translate(-5px,2px);opacity:1}}89%{{transform:translate(4px,-1px);opacity:1}}91%{{transform:none;opacity:0}}}}
@keyframes gl2{{0%,86%{{transform:none;opacity:0}}87%{{transform:translate(5px,-2px);opacity:1}}89%{{transform:translate(-3px,1px);opacity:1}}91%{{transform:none;opacity:0}}}}
.pscan{{animation:ps 3.6s cubic-bezier(.4,0,.6,1) infinite alternate}}
@keyframes ps{{from{{transform:translateY(0)}}to{{transform:translateY(298px)}}}}
.rec{{animation:blink 1.4s steps(1) infinite}}
.mq{{animation:mq 26s linear infinite}}
@keyframes mq{{to{{transform:translateX(var(--L))}}}}
"""
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@biskin: ~ — zsh", inner, css, "h")


# ───────────────────────────── activity skyline ─────────────────────────────
def build_activity(st):
    H = 370
    ids = Ids("a")
    defs, body = [], []
    c, t, end, xe = typed(ids, [("efe@github", LIME), (" ~ $ ", MUTED), ("./contributions.sh --last 12mo", CREAM)], 15, 32, 78, 0.3)
    defs.append(c); body.append(t)
    weeks = st["weeks"]
    mx = max(1, st["best"]["contributionCount"])
    ox, oy, sx, dxr, dyr = 92, 214, 15.0, 6.6, 7.4
    fw, fdx, fdy = 12.4, 5.3, 5.9
    tiles, towers = [], []
    best_pt = None
    for wi, wk in enumerate(weeks):
        for day in wk:
            d = day["weekday"]
            n = day["contributionCount"]
            bx, by = ox + wi * sx + d * dxr, oy + d * dyr
            if n == 0:
                tiles.append(f"M{num(bx)} {num(by)}h{num(fw)}l{num(fdx)} {num(fdy)}h-{num(fw)}z")
                continue
            q = n / mx
            lvl = 0 if q < .25 else 1 if q < .5 else 2 if q < .75 else 3
            top = [LIME4, LIME3, LIME2, LIME][lvl]
            front = ["#2C3A00", "#4D6400", "#6D8F00", "#8DB800"][lvl]
            side = ["#1F2900", "#374800", "#4F6700", "#668500"][lvl]
            h = 7 + 96 * math.sqrt(q)
            T0 = (bx, by - h)
            T1 = (bx + fw, by - h)
            T2 = (bx + fw + fdx, by - h + fdy)
            T3 = (bx + fdx, by - h + fdy)
            poly = lambda pts, f: f'<path d="M{"L".join(num(a) + " " + num(b) for a, b in pts)}Z" fill="{f}"/>'
            g = (poly([T3, T2, (T2[0], T2[1] + h), (T3[0], T3[1] + h)], front)
                 + poly([T1, T2, (T2[0], T2[1] + h), (T1[0], T1[1] + h)], side)
                 + poly([T0, T1, T2, T3], top))
            towers.append(f'<g class="tw" style="animation-delay:{end + 0.15 + wi * 0.022:.3f}s">{g}</g>')
            if day is st["best"] or (day["date"] == st["best"]["date"]):
                best_pt = (T0[0] + fw / 2 + fdx / 2, T0[1] - 8, end + 0.15 + wi * 0.022 + 0.9)
    body.append(f'<path d="{"".join(tiles)}" fill="#171A10"/>')
    body.append("".join(towers))
    if best_pt:
        lb, _ = P(MONOB, str(mx), 11, best_pt[0], best_pt[1], LIME, anchor="middle")
        body.append(f'<g class="fade" style="animation-delay:{best_pt[2]:.2f}s">{lb}</g>')
    # month + day labels
    lastm, lastw = None, -9
    for wi, wk in enumerate(weeks):
        m = wk[0]["date"][:7]
        if m != lastm and wi - lastw >= 3:
            name = dt.date.fromisoformat(wk[0]["date"]).strftime("%b")
            p, _ = P(MONO, name, 11, ox + wi * sx + 6 * dxr + 2, oy + 6 * dyr + 30, MUTED)
            body.append(p)
            lastw = wi
        lastm = m
    for d, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p, _ = P(MONO, name, 10, ox + d * dxr - 8, oy + d * dyr + 5, DIM, anchor="end")
        body.append(p)
    # numbers
    yl = 314
    big, bw = P(HEAVY, f"{st['total']:,}", 30, 32, yl + 4, LIME)
    lab, _ = P(MONO, "contributions in the last 12 months", 13, 32 + bw + 12, yl, CREAM)
    rw = MONO.width(f"best day {mx} · {fmt_date(st['best']['date'])}   active days {st['active']}", 12)
    rt, _ = segs(MONO, [("best day ", MUTED), (f"{mx}", LIME), (f" · {fmt_date(st['best']['date'])}", MUTED),
                        ("   active days ", MUTED), (f"{st['active']}", LIME)], 12, W - 32 - rw, yl)
    body.append(f'<g class="fade" style="animation-delay:{end + 0.4:.2f}s">{big}{lab}{rt}</g>')
    foot, _ = P(MONO, f"auto-built from the GitHub API · updated {st['today']}", 10, 32, 346, DIM)
    # legend
    lg = []
    lx = W - 32 - 5 * 15 - 70
    p, _ = P(MONO, "less", 10, lx, 346, DIM, anchor="end"); lg.append(p)
    for i, col in enumerate(["#171A10", LIME4, LIME3, LIME2, LIME]):
        lg.append(f'<rect x="{lx + 8 + i * 15}" y="337" width="11" height="11" rx="2" fill="{col}"/>')
    p, _ = P(MONO, "more", 10, lx + 8 + 5 * 15 + 4, 346, DIM); lg.append(p)
    body.append(foot + "".join(lg))
    css = """.tw{transform-box:fill-box;transform-origin:50% 100%;animation:rise 1s cubic-bezier(.2,.9,.25,1.15) both}
@keyframes rise{from{transform:scaleY(0)}to{transform:scaleY(1)}}"""
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@github: ~/activity", inner, css, "a")


# ───────────────────────────── stats ─────────────────────────────
def build_stats(st):
    H = 318
    ids = Ids("s")
    defs, body = [], []
    c, t, end, _ = typed(ids, [("efe@github", LIME), (" ~ $ ", MUTED), ("gh stats --me", CREAM)], 15, 32, 78, 0.3)
    defs.append(c); body.append(t)
    lr = st["lrange"]
    tiles = [
        ("CONTRIBUTIONS · 12 MO", f"{st['total']:,}", f"{st['active']} active days"),
        ("PUBLIC REPOS", str(st["repos"]), f"{st['stars']} stars earned"),
        ("BEST DAY", str(st["best"]["contributionCount"]), fmt_date(st["best"]["date"])),
        ("LONGEST STREAK", f"{st['longest']}d",
         f"{fmt_date(lr[0])} → {fmt_date(lr[1])}" if lr[0] else "—"),
    ]
    tw_, th_, gap = 222, 92, 13
    for i, (lab, val, sub) in enumerate(tiles):
        x, y = 32 + i * (tw_ + gap), 100
        l, _ = P(MONO, lab, 10.5, x + 18, y + 26, MUTED, track=0.8)
        v, _ = P(HEAVY, val, 38, x + 17, y + 66, LIME if i == 0 else CREAM)
        s, _ = P(MONO, sub, 11, x + 18, y + 84, DIM)
        body.append(f'<g class="up" style="animation-delay:{end + 0.1 + i * 0.12:.2f}s">'
                    f'<rect x="{x}" y="{y}" width="{tw_}" height="{th_ + 8}" rx="10" fill="#0F110A" stroke="{EDGE}"/>'
                    f'<rect x="{x}" y="{y}" width="3" height="{th_ + 8}" rx="1.5" fill="{LIME if i == 0 else EDGE}"/>{l}{v}{s}</g>')
    # monthly bars
    months = list(st["months"].items())[-13:]
    mmax = max(1, max(v for _, v in months))
    bx0, base, bw, bg = 32, 290, 26, 8.6
    hd, _ = P(MONO, "contributions / month", 10.5, bx0, 226, MUTED, track=0.4)
    body.append(hd)
    for i, (m, v) in enumerate(months):
        x = bx0 + i * (bw + bg)
        h = 2 if v == 0 else 4 + 44 * v / mmax
        col = LIME if v == mmax and v > 0 else (LIME3 if v > 0 else "#1C2013")
        body.append(f'<rect class="bar" style="animation-delay:{end + 0.5 + i * 0.05:.2f}s" x="{num(x)}" y="{num(base - h)}" '
                    f'width="{bw}" height="{num(h)}" rx="3" fill="{col}"/>')
        ml, _ = P(MONO, dt.date.fromisoformat(m + "-01").strftime("%b")[0], 10, x + bw / 2, base + 15, DIM, anchor="middle")
        body.append(ml)
        if v == mmax and v > 0:
            vl, _ = P(MONOB, str(v), 10.5, x + bw / 2, base - h - 6, LIME, anchor="middle")
            body.append(f'<g class="fade" style="animation-delay:{end + 1.2:.2f}s">{vl}</g>')
    # language mix
    lx0, lx1 = 520, W - 32
    hd, _ = P(MONO, "primary language · public repos", 10.5, lx0, 226, MUTED, track=0.4)
    body.append(hd)
    langs = st["langs"][:5]
    tot = max(1, sum(n for _, n in langs))
    cols = [LIME, LIME2, CREAM, LIME3, MUTED]
    cx = lx0
    barw = lx1 - lx0
    segs_ = []
    for i, (name, n) in enumerate(langs):
        w = barw * n / tot
        segs_.append(f'<rect x="{num(cx)}" y="240" width="{num(max(0, w - 3))}" height="12" rx="3" fill="{cols[i]}"/>')
        cx += w
    body.append(f'<g class="grow" style="animation-delay:{end + 0.6:.2f}s">{"".join(segs_)}</g>')
    lx, ly = lx0, 280
    for i, (name, n) in enumerate(langs):
        label = f"{name} {n}"
        lw = MONO.width(label, 11.5)
        if lx + 16 + lw > lx1:
            lx, ly = lx0, ly + 20
        body.append(f'<rect x="{num(lx)}" y="{ly - 9}" width="9" height="9" rx="2" fill="{cols[i]}"/>')
        p, _ = segs(MONO, [(name + " ", CREAM), (str(n), MUTED)], 11.5, lx + 15, ly)
        body.append(p)
        lx += 15 + lw + 18
    css = """.bar{transform-box:fill-box;transform-origin:50% 100%;animation:rise .9s cubic-bezier(.2,.9,.25,1.1) both}
@keyframes rise{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.grow{transform-box:fill-box;transform-origin:0 50%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"""
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@github: ~/stats", inner, css, "s")


# ───────────────────────────── project cards ─────────────────────────────
CARDS = [
    ("biskin-studio", "LIVE", "Biskin Studio",
     "Design + engineering studio. A WebGL front door and a store of Claude Code agent packs.",
     "biskin.studio", "Three.js · Vercel", None),
    ("boss-gangster", "ON STEAM", "The Boss Gangster: Criminal Empire",
     "Game dev + business relations at BEF Games. Brokered the Tripwire Presents publishing deal; EN/TR/ES localization.",
     "store.steampowered.com", "Early Access · 2026", None),
    ("olympiq", "LIVE", "Olympiq",
     "Personalized fitness web app, my CS capstone. Runs on a hand-rolled React-like runtime, zero frameworks.",
     "olympiq.biskin.studio", "Capstone · CLU '26", None),
    ("mini-react", "OPEN SOURCE", "mini-react",
     "React's core in ~220 lines: virtual DOM, hooks and a reconciling diff. Zero dependencies.",
     "github.com/efebiskin/mini-react", "JavaScript", "mini-react"),
    ("sec-form4-parser", "OPEN SOURCE", "sec-form4-parser",
     "Typed Python parser for SEC Form 4 insider filings, with a rate-limited EDGAR fetcher and a CLI.",
     "github.com/efebiskin/sec-form4-parser", "Python", "sec-form4-parser"),
    ("xeneon-widgets", "OPEN SOURCE", "xeneon-widgets",
     "Seven single-page widgets for the Corsair Xeneon Edge touchscreen's iCUE iFrame pane.",
     "github.com/efebiskin/xeneon-widgets", "HTML", "xeneon-widgets"),
]


def wrap(face, text, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if face.width(t, size) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def star(cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{num(cx + rr * math.cos(a))} {num(cy + rr * math.sin(a))}")
    return f'<path d="M{"L".join(pts)}Z" fill="{fill}"/>'


def build_card(i, card, st):
    slug, status, title, desc, url, meta, repo = card
    w, h = 480, 210
    pill_col = LIME if status == "LIVE" else CREAM if status == "ON STEAM" else MUTED
    pl, plw = P(MONOB, status, 10.5, 44, 37.5, pill_col, track=1.0)
    idx, _ = P(MONO, f"{i + 1:02d}", 11, w - 24, 38, DIM, anchor="end")
    tsize = HEAVY.fit(title, 28, w - 48)
    tt, _ = P(HEAVY, title, tsize, 24, 88, CREAM)
    dl = "".join(P(MONO, line, 12.5, 24, 118 + k * 19, MUTED)[0] for k, line in enumerate(wrap(MONO, desc, 12.5, w - 48)[:3]))
    ul, _ = segs(MONO, [("→ ", LIME), (url, LIME)], 12.5, 24, 186)
    mt_parts = [(meta, DIM)]
    mt = ""
    mw = MONO.width(meta, 11)
    if repo is not None:
        n = st["repo_stars"].get(repo, 0)
        if n:
            sw = MONO.width(str(n), 11)
            mt += star(w - 24 - sw - 9, 182, 5.5, LIME) + P(MONO, str(n), 11, w - 24, 186, LIME, anchor="end")[0]
            mw_off = sw + 22
        else:
            mw_off = 0
    else:
        mw_off = 0
    mt += P(MONO, meta, 11, w - 24 - mw_off, 186, DIM, anchor="end")[0]
    per = 2 * (w + h)
    delay = i * 0.9
    css = f""".trace{{stroke-dasharray:140 {per};animation:tr 7s linear infinite;animation-delay:-{delay:.1f}s}}
@keyframes tr{{from{{stroke-dashoffset:{per + 140}}}to{{stroke-dashoffset:0}}}}
.dot{{animation:pulse 1.6s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.25}}}}
.up{{opacity:0;animation:up .8s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes up{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}: {esc(desc)}">
<title>{esc(title)}</title><style>{css}</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{BG}" stroke="{EDGE}"/>
<rect class="trace" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{LIME}" stroke-width="1.6"/>
<g class="up" style="animation-delay:{0.1 + i * 0.08:.2f}s">
<rect x="22" y="22" width="{num(plw + 34)}" height="22" rx="11" fill="{pill_col}" fill-opacity=".1" stroke="{pill_col}" stroke-opacity=".5"/>
<circle class="dot" cx="34" cy="33" r="3.5" fill="{pill_col}"/>{pl}{idx}
{tt}{dl}
<rect x="24" y="160" width="{w - 48}" height="1" fill="{EDGE}"/>
{ul}{mt}
</g>
</svg>
"""


# ───────────────────────────── private listing ─────────────────────────────
PRIVATE = [
    ("trading-research/", "walk-forward ML, costs-in backtests, drift checks, kill switches"),
    ("lfvi/", "land value index: Census + FRED + FEMA → every US county, Dash app"),
    ("hera/", "personal AI agent: Telegram, voice, 42 tools, Obsidian memory"),
    ("polyradar/", "Polymarket whale-trade alerts: asyncio, Postgres, Redis, Discord"),
    ("gains-and-grains/", "cozy Unity 2D sim where customers order by macros (in dev)"),
]


def build_private():
    H = 258
    ids = Ids("p")
    defs, body = [], []
    c, t, end, xe = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED), ("ls -l ~/private", CREAM),
                                ("   # source is private, walkthroughs on request", DIM)], 15, 32, 78, 0.3, cps=40)
    defs.append(c); body.append(t)
    y = 112
    b = end + 0.15
    for name, desc in PRIVATE:
        c, t, b2, _ = typed(ids, [("drwx------  ", DIM), (f"{name:<19}", LIME), (desc, CREAM)], 13, 32, y, b, cps=110)
        defs.append(c); body.append(t)
        b = b2 + 0.05
        y += 26
    c, t, b3, xe2 = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED)], 15, 32, y + 12, b + 0.2, cps=40)
    defs.append(c); body.append(t + cursor(xe2, y + 12, 15, b3))
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@biskin: ~/private", inner, "", "p")


# ───────────────────────────── stack ─────────────────────────────
STACK = [
    ("lang/", ["Python", "TypeScript", "JavaScript", "C#", "Java", "SQL"]),
    ("ml/", ["scikit-learn", "XGBoost", "LightGBM", "walk-forward CV", "drift detection", "calibration"]),
    ("web/", ["Three.js", "WebGL", "Node.js", "Flask", "Postgres", "Redis", "Docker", "Vercel"]),
    ("game+3d/", ["Unity 6", "C# / URP", "Blender", "Steamworks"]),
    ("ai/", ["Claude API", "agent tooling", "Telegram bots", "ElevenLabs", "faster-whisper"]),
]


def build_stack():
    H = 300
    ids = Ids("k")
    defs, body = [], []
    c, t, end, _ = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED), ("ls ~/stack", CREAM)], 15, 32, 78, 0.3)
    defs.append(c); body.append(t)
    y = 110
    k = 0
    total = sum(len(v) for _, v in STACK)
    cyc = total * 0.22 + 2.5
    for label, chips in STACK:
        lb, _ = P(MONOB, label, 12.5, 32, y + 17.5, LIME)
        body.append(f'<g class="fade" style="animation-delay:{end + 0.1:.2f}s">{lb}</g>')
        x = 150
        for chip in chips:
            tw = MONO.width(chip, 12.5)
            cw = tw + 26
            p, _ = P(MONO, chip, 12.5, x + 13, y + 17.5, CREAM)
            body.append(f'<g class="up" style="animation-delay:{end + 0.1 + k * 0.03:.2f}s">'
                        f'<rect class="chip" style="animation-delay:{end + 1 + k * 0.22:.2f}s" x="{num(x)}" y="{y}" '
                        f'width="{num(cw)}" height="26" rx="13"/>{p}</g>')
            x += cw + 8
            k += 1
        y += 36
    css = f""".chip{{fill:#0F110A;stroke:#2A3020;animation:hi {cyc:.1f}s ease-out infinite}}
@keyframes hi{{0%{{fill:{LIME};fill-opacity:.16;stroke:{LIME}}}10%,100%{{fill:#0F110A;fill-opacity:1;stroke:#2A3020}}}}"""
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@biskin: ~/stack", inner, css, "k")


# ───────────────────────────── ethos ─────────────────────────────
def build_ethos():
    H = 250
    ids = Ids("e")
    defs, body = [], []
    c, t, end, _ = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED), ("cat ethos.md", CREAM)], 15, 32, 78, 0.3)
    defs.append(c); body.append(t)
    q, _ = segs(SERIF, [("Rigorous validation ", CREAM), ("over demo-day magic.", LIME)], 44, 32, 140)
    body.append(f'<g class="up" style="animation-delay:{end + 0.1:.2f}s">{q}</g>')
    lines = ["My trading model looked great in-sample: 59.7% win rate at p ≥ 0.70.",
             "Out-of-sample it fell to 48.5%, worse than a coin flip. I caught the overfit,",
             "wrote it up and rebuilt around tested strategies instead of shipping the lie."]
    for i, line in enumerate(lines):
        p, _ = P(MONO, line, 13, 32, 182 + i * 21, MUTED if i < 2 else CREAM)
        body.append(f'<g class="up" style="animation-delay:{end + 0.4 + i * 0.12:.2f}s">{p}</g>')
    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@biskin: ~/ethos.md", inner, "", "e")


# ───────────────────────────── buttons ─────────────────────────────
def build_button(label, sub, filled):
    w, h = 240, 52
    fg = BG if filled else LIME
    l, lw = P(HEAVY, label, 15, 22, 24, fg, track=1.4)
    s, _ = P(MONO, sub, 11, 22, 41, BG if filled else MUTED)
    ar, _ = P(MONOB, "→", 18, w - 20, 33, fg, anchor="end")
    css = """.sh{animation:sh 3.8s ease-in-out infinite}@keyframes sh{0%,60%{transform:translateX(-120px)}100%{transform:translateX(380px)}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)} {esc(sub)}">
<title>{esc(label)}</title><style>{css}</style>
<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="12"/></clipPath>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity="{.35 if filled else .12}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{LIME if filled else BG}"/>
<rect class="sh" x="0" y="-20" width="70" height="{h + 40}" fill="url(#g)" transform="skewX(-20)"/></g>
<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="11.5" fill="none" stroke="{LIME}" stroke-width="1.5"/>
{l}{s}{ar}
</svg>
"""


# ───────────────────────────── footer: the crowd ─────────────────────────────
# The crowd is Open Peeps by Pablo Stanley (CC0). scripts/peeps.json holds the parts used here.
CROWD_HAIR_X = 430          # head centre in peep units (head group sits at x=225)
FOOTER_BOB = (22, 34)       # walk bounce, peep units


def build_footer():
    H, PT = 470, 196                       # panel height, top of the cream crowd panel
    INK, PAPER, WORD = "#0A0A0A", "#FFFDF7", "#E4DDCB"
    pp = json.loads((ROOT / "scripts" / "peeps.json").read_text(encoding="utf-8"))
    rnd = random.Random(2026)              # fixed seed: the same crowd every build, no daily diff
    ids = Ids("f")
    defs, body, used = [], [], set()

    # dark band: the session ends
    c, t, end, x_end = typed(ids, [("efe@biskin", LIME), (" ~ $ ", MUTED), ("exit", CREAM)], 15, 32, 74, 0.3)
    defs.append(c); body.append(t)
    lo, _ = P(MONO, "logout · thanks for scrolling this far.", 12, 32, 98, MUTED)
    body.append(f'<g class="fade" style="animation-delay:{end + 0.15:.2f}s">{lo}</g>')
    see, _ = segs(HEAVY, [("See you ", CREAM), ("around.", LIME)], 50, 30, 160)
    body.append(f'<g class="up" style="animation-delay:{end + 0.35:.2f}s">{see}</g>')
    meta = [("biskin.studio", CREAM), ("linkedin.com/in/efe-biskin-923397400", MUTED),
            ("efebskn@gmail.com", MUTED), ("crowd: Open Peeps by Pablo Stanley, CC0", DIM)]
    for i, (txt, col) in enumerate(meta):
        p, _ = P(MONO, txt, 11.5, W - 32, 92 + i * 20, col, anchor="end")
        body.append(f'<g class="fade" style="animation-delay:{end + 0.5 + i * 0.1:.2f}s">{p}</g>')

    # cream panel + giant wordmark behind the crowd
    body.append(f'<rect y="{PT}" width="{W}" height="{H - PT}" fill="{CREAM}"/>')
    size = DISPLAY.fit("BISKIN.", 400, W - 40)
    base = PT + 18 + size * 0.73
    wm, ww = P(DISPLAY, "BISKIN", size, 20, base, WORD)
    dot, _ = P(DISPLAY, ".", size, 20 + ww, base, LIME)
    body.append(f'<g class="up" style="animation-delay:{end + 0.2:.2f}s">{wm}{dot}</g>')

    # parts become shared <g> defs; every peep is a few <use>s, so repeats cost nothing
    def part(cat, name):
        key = f"pp-{cat}-{name}"
        if key not in used and pp[cat][name]:
            used.add(key)
            frag = pp[cat][name].replace("{FG}", INK).replace("{BG}", "currentColor")
            defs.append(f'<g id="{key}">{frag}</g>')
        return f'<use href="#{key}"/>' if pp[cat][name] else ""

    def peep(kind, x, y, s, lime):
        bodyname = rnd.choice(list(pp[kind]))
        col = LIME if lime else PAPER
        head = (f'<g transform="translate(225 0)" color="{col}">{part("hair", rnd.choice(list(pp["hair"])))}'
                f'<g transform="translate(159 186)">{part("face", rnd.choice(list(pp["face"])))}</g>')
        if rnd.random() < 0.35:
            head += f'<g transform="translate(123 338)">{part("facialHair", rnd.choice(list(pp["facialHair"])[1:]))}</g>'
        if rnd.random() < 0.3:
            head += f'<g transform="translate(47 241)">{part("accessories", rnd.choice(list(pp["accessories"])[1:]))}</g>'
        head += "</g>"
        dur = rnd.uniform(0.9, 1.35)
        bob = rnd.uniform(*FOOTER_BOB)
        anim = (f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {-bob:.0f};0 0" '
                f'keyTimes="0;.5;1" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="{dur:.2f}s" '
                f'begin="-{rnd.uniform(0, dur):.2f}s" repeatCount="indefinite"/>')
        return (f'<g transform="translate({x - CROWD_HAIR_X * s:.1f} {y:.1f}) scale({s})"><g>{anim}'
                f'<g color="{col}">{part(kind, bodyname)}</g>{head}</g></g>')

    def row(rid, L, gap, s, top, kinds, lime_p):
        out, x = [], rnd.uniform(0, gap)
        while x < L:
            kind = rnd.choice(kinds)
            out.append(peep(kind, x, top + rnd.uniform(-8, 14), s, rnd.random() < lime_p))
            x += gap * rnd.uniform(0.8, 1.2)
        defs.append(f'<g id="{rid}">{"".join(out)}</g>')

    # back row: smaller, higher, slower (standing bodies only, so no torso ends above the edge)
    L = 1400
    sb, sf = 0.088, 0.118
    row("pp-back", L, 64, sb, H - 1130 * sb - 48, ["standing"], 0.12)
    row("pp-front", L, 86, sf, H - 1130 * sf + 6, ["bust", "bust", "standing"], 0.2)
    for rid, dur in (("pp-back", 110), ("pp-front", 70)):
        body.append(f'<g><animateTransform attributeName="transform" type="translate" from="{-L} 0" to="0 0" '
                    f'dur="{dur}s" repeatCount="indefinite"/><use href="#{rid}"/><use href="#{rid}" x="{L}"/></g>')

    inner = "<defs>" + "".join(defs) + "</defs>" + "\n".join(body)
    return window(W, H, "efe@biskin: ~ — exit", inner, "", "f")


# ───────────────────────────── main ─────────────────────────────
def main():
    OUT.mkdir(exist_ok=True)
    st = load_stats()
    try:
        with urllib.request.urlopen(st["avatar"], timeout=30) as r:
            avatar = r.read()
        (ROOT / "scripts" / "avatar.png").write_bytes(avatar)
    except Exception as e:  # keep the last good avatar
        print("avatar fetch failed, using cached copy:", e)
        avatar = (ROOT / "scripts" / "avatar.png").read_bytes()
    files = {
        "hero.svg": build_hero(st, avatar),
        "activity.svg": build_activity(st),
        "stats.svg": build_stats(st),
        "private.svg": build_private(),
        "stack.svg": build_stack(),
        "ethos.svg": build_ethos(),
        "btn-site.svg": build_button("BISKIN.STUDIO", "the studio", True),
        "btn-linkedin.svg": build_button("LINKEDIN", "efe-biskin", False),
        "btn-email.svg": build_button("EMAIL", "efebskn@gmail.com", False),
        "footer.svg": build_footer(),
    }
    for i, card in enumerate(CARDS):
        files[f"card-{card[0]}.svg"] = build_card(i, card, st)
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name:28s} {len(svg.encode()) / 1024:7.1f} KB")
    print(f"total {st['total']} contributions · {st['active']} active days · {st['repos']} public repos · {st['stars']} stars")


if __name__ == "__main__":
    main()
