"""论文用图。正文插图用浅色，和正文配套（深蓝字、金色＝涨/正面、蓝色＝跌/反面）；封面是整页深色海报。
输出到 paper/images_v5/。跑法：python3 figs.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, Wedge

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "images_v5"
IMG.mkdir(exist_ok=True)
DATA = HERE.parent.parent / "research" / "data"
DPI = 240

# ---------------------------------------------------------------- 字体：从系统的 Noto CJK 合集里取出简体中文那一款
FONT_DIR = Path.home() / ".cache" / "dongzhi_fonts"


def _font(name, src):
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    out = FONT_DIR / name
    if not out.exists():
        from fontTools.ttLib import TTCollection
        for f in TTCollection(src).fonts:
            if f["name"].getDebugName(1).endswith(" SC"):
                f.save(out)
                break
    return fm.FontProperties(fname=str(out))


NOTO = "/usr/share/fonts/opentype/noto/"
SERIF = _font("NotoSerifSCBold.otf", NOTO + "NotoSerifCJK-Bold.ttc")
SANS = _font("NotoSansSCRegular.otf", NOTO + "NotoSansCJK-Regular.ttc")
SANSB = _font("NotoSansSCBold.otf", NOTO + "NotoSansCJK-Bold.ttc")
plt.rcParams["axes.unicode_minus"] = False

# 配色：浅色（正文插图）
BG, PANEL, LINE = "#FFFFFF", "#F4F6F9", "#D5DBE4"
INK, TXT, MUTED = "#1D2F4A", "#2E3A4A", "#6C7889"
GOLD, BLUE = "#C2851B", "#3D689E"            # 线和字
GOLD_F, BLUE_F = "#E8B24C", "#6D92C3"        # 填色
WARM = ["#F6DFAE", "#F0CB80", "#E8B24C", "#D99A30", "#C2821E", "#A26A16"]
COOL = ["#D3E0F1", "#B5CAE6", "#93B0D7", "#7096C6", "#4F79AF", "#3A6196"]
# 封面（深色）
D_BG, D_LINE, D_CREAM, D_TXT, D_MUTED = "#101927", "#2C3B52", "#EFE7D6", "#D9DFE8", "#8A96A8"
D_GOLD, D_BLUE = "#E3A73C", "#6F98CC"

STAGES = ["绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]


def col(k, dark=False):
    if dark:
        return D_GOLD if k < 6 else D_BLUE
    return GOLD if k < 6 else BLUE


def T(ax, x, y, s, size=10, w="r", c=TXT, **kw):
    fp = {"r": SANS, "b": SANSB, "s": SERIF}[w]
    return ax.text(x, y, s, fontproperties=fp, fontsize=size, color=c, **kw)


def canvas(w, h, bg=BG):
    fig = plt.figure(figsize=(w, h), facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    return fig, ax, 100 * h / w


def card(ax, x, y, w, h, ec=LINE, fc=PANEL, lw=1.0, r=1.8, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, zorder=z))


def pill(ax, x, y, s, c, size=9, pad=0.55, w="r", fc=BG):
    t = T(ax, x, y, s, size, w, c, ha="center", va="center", zorder=9)
    t.set_bbox(dict(boxstyle=f"round,pad={pad},rounding_size=1.2", fc=fc, ec=c, lw=1.0))
    return t


def numdot(ax, x, y, k, r=1.8, size=8, dark=False, bg=None):
    c = col(k, dark)
    ax.add_patch(Circle((x, y), r, fc=bg or (D_BG if dark else BG), ec=c, lw=1.5, zorder=7))
    T(ax, x, y - 0.05, str(k + 1), size, "b", c, ha="center", va="center", zorder=8)


def arrow(ax, a, b, c=MUTED, lw=1.1, ms=10, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=ms, color=c, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", zorder=3))


def save(fig, name, bg=BG):
    fig.savefig(IMG / name, dpi=DPI, facecolor=bg)
    plt.close(fig)
    print("存好", name)


# ---------------------------------------------------------------- 一轮行情的路径（示意）
PATH = [(0, 16), (3, 12), (6, 9.5),
        (9.5, 14), (11.5, 11.5), (15.5, 19), (17.5, 16.5), (21.5, 25), (23.5, 22.5), (27.5, 33),
        (29.5, 30.5), (33.5, 44), (35, 41.5), (39.5, 64), (42, 86), (43.8, 78), (45.8, 84), (47.6, 79.5), (49.2, 84),
        (53, 66), (54.6, 70), (58.4, 57.5), (60, 60.5), (63.6, 50), (65.6, 46), (67.6, 49.5), (71.4, 41), (73.4, 44),
        (76.6, 36), (79.5, 24), (81.5, 12), (84.5, 7.5), (88.5, 6.5), (91, 8.5)]
NEXT = [(91, 8.5), (93.5, 12.5), (95.5, 11), (98, 15)]
MARK = {0: 3, 1: 5, 2: 9, 3: 11, 4: 13, 5: 16, 6: 20, 7: 21, 8: 24, 9: 29, 10: 30, 11: 32}
SIDE = {0: (-1, 1), 1: (1, -1), 2: (-1, 1), 3: (-1, 1), 4: (-1, 1), 5: (0, 1),
        6: (1, 1), 7: (-1, -1), 8: (1, 1), 9: (1, 1), 10: (1, 1), 11: (0, -1)}


def draw_path(ax, x0, y0, sx, sy, dark=False, label=10.5, dot=1.9):
    g, b, ln, lab = (D_GOLD, D_BLUE, D_LINE, D_CREAM) if dark else (GOLD, BLUE, LINE, INK)
    P = np.array(PATH, float)
    X, Y = x0 + P[:, 0] * sx, y0 + P[:, 1] * sy
    ax.plot(X[:4], Y[:4], color=ln, lw=2.2, solid_capstyle="round", zorder=3)
    ax.plot(X[3:18], Y[3:18], color=g, lw=2.4, solid_joinstyle="round", zorder=4)
    ax.plot(X[17:], Y[17:], color=b, lw=2.4, solid_joinstyle="round", zorder=4)
    N = np.array(NEXT, float)
    ax.plot(x0 + N[:, 0] * sx, y0 + N[:, 1] * sy, color=g, lw=2.0, ls=(0, (1, 2.2)), zorder=4)
    for k, i in MARK.items():
        numdot(ax, X[i], Y[i], k, r=dot, size=dot * 4.3, dark=dark)
        dx, dy = SIDE[k]
        ha = "right" if dx < 0 else ("left" if dx > 0 else "center")
        T(ax, X[i] + dx * (dot + 1.1), Y[i] + dy * (dot + 1.4), STAGES[k], label, "b", lab,
          ha=ha, va="bottom" if dy > 0 else "top", zorder=8)
    peak = (x0 + 42 * sx, y0 + 86 * sy)
    bottom = (x0 + 6 * sx, y0 + 9.5 * sy)
    return peak, bottom


# ---------------------------------------------------------------- 封面（整页，A4）
def cover():
    fig, ax, H = canvas(8.27, 11.69, D_BG)
    ax.add_patch(Rectangle((0, 0), 100, H, fc=D_BG, ec="none", zorder=0))
    L = 10
    T(ax, L, H - 11, "市 场 周 期 方 法 论", 11, "r", D_MUTED, va="center")
    T(ax, L - 0.8, H - 24, "冬至理论", 76, "s", D_CREAM, va="center")
    T(ax, L, H - 36.5, "一个关于市场冷热循环的十二阶段模型", 15, "r", D_TXT, va="center")
    T(ax, L, H - 42.5, "JustinTang洛辰", 13, "r", D_TXT, va="center")
    T(ax, L, H - 53, "最冷的那天，太阳已经回头；", 20, "s", D_GOLD, va="center")
    T(ax, L, H - 60.5, "最热的那天，太阳已经要走。", 20, "s", D_BLUE, va="center")
    peak, bot = draw_path(ax, L, 21, 0.81, 0.58, dark=True, label=11.5, dot=2.0)
    ax.plot([L, 100 - L], [22.5, 22.5], color=D_LINE, lw=0.8, zorder=1)
    pill(ax, L + 7, 17.5, "冬至 · 最冷", D_BLUE, 10, fc=D_BG)
    ax.plot([peak[0] - 12.5, peak[0] - 0.8], [peak[1] - 0.5, peak[1] - 0.5], color=D_GOLD, lw=0.8, ls=":", zorder=2)
    pill(ax, peak[0] - 19.5, peak[1] - 0.5, "夏至 · 最热", D_GOLD, 10, fc=D_BG)
    T(ax, L + 97 * 0.81, 21 + 19 * 0.58, "下一轮", 10, "r", D_GOLD, ha="center", va="bottom")
    ax.plot([L, 100 - L], [10, 10], color=D_LINE, lw=0.8)
    T(ax, L, 6.5, "冬里藏春，夏里藏秋", 11, "r", D_MUTED, va="center")
    T(ax, 100 - L, 6.5, "二〇二六年十一月", 11, "r", D_MUTED, va="center", ha="right")
    save(fig, "封面.png", D_BG)


# ---------------------------------------------------------------- 图1 太阳和气温
def sun_temp():
    fig, ax, H = canvas(7.2, 3.8)
    t = np.linspace(0, 12, 400)
    dz = 3.0
    mid, amp = H / 2 - 1.5, 11
    X = lambda tt: 7 + tt / 12 * 86
    ax.plot([7, 93], [mid, mid], color=LINE, lw=0.7, zorder=1)
    ax.plot(X(t), mid - amp * np.cos(2 * np.pi * (t - dz) / 12), color=INK, lw=2.0, zorder=4)
    ax.plot(X(t), mid - amp * np.cos(2 * np.pi * (t - dz - 1) / 12), color=GOLD, lw=2.0, ls=(0, (4, 2.5)), zorder=4)
    lo, hi = mid - amp, mid + amp
    for tt, yy, c in [(dz, lo, BLUE), (dz + 1, lo, BLUE), (dz + 6, hi, GOLD), (dz + 7, hi, GOLD)]:
        ax.add_patch(Circle((X(tt), yy), 0.95, fc=c, ec=BG, lw=1, zorder=6))
    T(ax, X(dz) - 1.4, lo - 2.8, "冬至：太阳回头", 9, "b", BLUE, ha="right", va="top")
    T(ax, X(dz + 1) + 1.4, lo - 2.8, "最冷：三九", 9, "b", BLUE, ha="left", va="top")
    T(ax, X(dz + 6) - 1.4, hi + 2.8, "夏至：太阳要走", 9, "b", GOLD, ha="right", va="bottom")
    T(ax, X(dz + 7) + 1.4, hi + 2.8, "最热：三伏", 9, "b", GOLD, ha="left", va="bottom")
    for a1, yy, va in [(dz, lo - 9.5, "top"), (dz + 6, hi + 9.5, "bottom")]:
        ax.add_patch(FancyArrowPatch((X(a1), yy), (X(a1 + 1), yy), arrowstyle="<->", mutation_scale=8, color=MUTED, lw=0.9))
        T(ax, X(a1 + 0.5), yy + (-1.3 if va == "top" else 1.3), "差一个月左右", 8, "r", MUTED, ha="center", va=va)
    ax.plot([7, 11.5], [H - 4.5, H - 4.5], color=INK, lw=2.0)
    T(ax, 12.8, H - 4.5, "太阳：源头，是事实", 8.8, "r", TXT, va="center")
    ax.plot([40, 44.5], [H - 4.5, H - 4.5], color=GOLD, lw=2.0, ls=(0, (4, 2.5)))
    T(ax, 45.8, H - 4.5, "气温：感觉，是价格的冷热", 8.8, "r", TXT, va="center")
    save(fig, "太阳和气温.png")


# ---------------------------------------------------------------- 图2 三股力翻面
STATE = {0: (0.5, 0, 0), 1: (1, 0, 0), 2: (1, 0.5, 0), 3: (1, 1, 0), 4: (1, 1, 0.5), 5: (1, 1, 1),
         6: (-0.5, 1, 1), 7: (0, 1, 1), 8: (0, -0.5, 1), 9: (0, 0, 1), 10: (0, 0, -0.5), 11: (0, 0, 0)}


def forces_grid():
    fig, ax, H = canvas(7.2, 3.55)
    rows = [("条件", "地 · 事实"), ("时机", "天 · 钱和趋势"), ("人性", "人 · 贪和怕")]
    x0, cw, ch, gap = 16, 6.6, 8.2, 0.6
    ytop = H - 13
    for k in range(12):
        x = x0 + k * cw + (cw - gap) / 2
        numdot(ax, x, ytop + 7.4, k, r=1.55, size=6.8)
        T(ax, x, ytop + 3.0, STAGES[k] if k != 3 else "大众\n共识", 7.4, "b", col(k), ha="center", va="center", linespacing=0.95)
    for r, (nm, sub) in enumerate(rows):
        y = ytop - r * (ch + gap) - ch
        T(ax, x0 - 1.6, y + ch / 2 + 1.3, nm, 10.5, "b", INK, ha="right", va="center")
        T(ax, x0 - 1.6, y + ch / 2 - 2.1, sub, 6.8, "r", MUTED, ha="right", va="center")
        for k in range(12):
            s = STATE[k][r]
            x, w = x0 + k * cw, cw - gap
            if s in (0, 1):
                card(ax, x, y, w, ch, ec="none", fc=GOLD_F if s == 1 else BLUE_F, r=0.7)
            else:
                old, new = (BLUE_F, GOLD_F) if s > 0 else (GOLD_F, BLUE_F)
                ax.add_patch(Polygon([(x, y), (x + w, y), (x, y + ch)], fc=old, ec="none"))
                ax.add_patch(Polygon([(x + w, y), (x + w, y + ch), (x, y + ch)], fc=new, ec="none"))
                ax.add_patch(Rectangle((x, y), w, ch, fc="none", ec=INK, lw=1.3))
                T(ax, x + w / 2, y + ch / 2, "翻", 8.5, "b", INK, ha="center", va="center",
                  bbox=dict(boxstyle="circle,pad=0.15", fc=BG, ec="none"))
    xm = x0 + 6 * cw - gap / 2
    ax.plot([xm, xm], [ytop - 3 * (ch + gap) - 1, ytop + 9.5], color=MUTED, lw=0.6, ls=":")
    yb = ytop - 3 * (ch + gap) - 4.2
    T(ax, x0 + 3 * cw, yb, "上涨六段：条件先转，时机跟着，人性最后", 8.3, "r", GOLD, ha="center", va="center")
    T(ax, x0 + 9 * cw, yb, "下跌六段：还是条件先转，人性最后", 8.3, "r", BLUE, ha="center", va="center")
    lx, ly = x0, 2.2
    for i, (c, s) in enumerate([(GOLD_F, "正面"), (BLUE_F, "反面")]):
        ax.add_patch(Rectangle((lx + i * 12, ly), 3.0, 2.4, fc=c, ec="none"))
        T(ax, lx + i * 12 + 4.0, ly + 1.2, s, 8, "r", TXT, va="center")
    ax.add_patch(Polygon([(lx + 24, ly), (lx + 27, ly), (lx + 24, ly + 2.4)], fc=BLUE_F))
    ax.add_patch(Polygon([(lx + 27, ly), (lx + 27, ly + 2.4), (lx + 24, ly + 2.4)], fc=GOLD_F))
    T(ax, lx + 28, ly + 1.2, "这一段正在翻面的那股力", 8, "r", TXT, va="center")
    save(fig, "三股力翻面.png")


# ---------------------------------------------------------------- 图3 十二阶段循环
def wheel():
    fig, ax, H = canvas(6.2, 5.9)
    cx, cy, R, w = 50, H / 2 - 0.5, 31, 11.5
    for k in range(12):
        a = 270 - (k + 1) * 30
        c = (WARM + COOL)[k]
        ax.add_patch(Wedge((cx, cy), R, a + 0.6, a + 30 - 0.6, width=w, fc=c, ec=BG, lw=1.5))
        mid = np.deg2rad(a + 15)
        rr = R - w / 2
        tx, ty = cx + rr * np.cos(mid), cy + rr * np.sin(mid)
        tc = BG if (k % 6) >= 3 else INK
        T(ax, tx, ty + 1.7, str(k + 1), 8, "b", tc, ha="center", va="center")
        T(ax, tx, ty - 1.7, STAGES[k], 8.6 if k != 3 else 7.2, "b", tc, ha="center", va="center")
    for k in range(12):
        a = np.deg2rad(270 - (k + 0.5) * 30)
        b = np.deg2rad(270 - (k + 0.5) * 30 - 18)
        r2 = R + 2.6
        arrow(ax, (cx + r2 * np.cos(a), cy + r2 * np.sin(a)), (cx + r2 * np.cos(b), cy + r2 * np.sin(b)),
              c=(GOLD if k < 6 else BLUE), lw=0.9, ms=6, rad=-0.12)
    T(ax, cx, cy + 3.4, "冬至理论", 17, "s", INK, ha="center", va="center")
    T(ax, cx, cy - 2.8, "十二阶段，转圈不停", 8.5, "r", MUTED, ha="center", va="center")
    pill(ax, cx, cy + R + 7.5, "夏至 · 最热：人性贪到头，条件开始转身", GOLD, 8.5)
    pill(ax, cx, cy - R - 7.5, "冬至 · 最冷：人性怕到头，条件开始回头", BLUE, 8.5)
    T(ax, cx - R - 7, cy, "上\n涨\n六\n段", 10.5, "b", GOLD, ha="center", va="center", linespacing=1.15)
    T(ax, cx + R + 7, cy, "下\n跌\n六\n段", 10.5, "b", BLUE, ha="center", va="center", linespacing=1.15)
    save(fig, "十二阶段循环.png")


# ---------------------------------------------------------------- 图4 圈的大小（真实数据）
def zigzag_legs(c, th):
    v = c.values
    pts, mode, ext, hi, lo = [], 0, 0, 0, 0
    for i in range(1, len(v)):
        if mode == 0:
            hi = i if v[i] > v[hi] else hi
            lo = i if v[i] < v[lo] else lo
            if v[i] >= v[lo] * (1 + th):
                pts.append(lo); mode, ext = 1, i
            elif v[i] <= v[hi] * (1 - th):
                pts.append(hi); mode, ext = -1, i
        elif mode == 1:
            if v[i] > v[ext]:
                ext = i
            elif v[i] <= v[ext] * (1 - th):
                pts.append(ext); mode, ext = -1, i
        else:
            if v[i] < v[ext]:
                ext = i
            elif v[i] >= v[ext] * (1 + th):
                pts.append(ext); mode, ext = 1, i
    pts.append(len(v) - 1)
    return pts


def circles():
    def load(p):
        d = pd.read_csv(p, parse_dates=["date"]).set_index("date")["close"]
        return d[d > 0].resample("W-FRI").last().dropna()
    s0 = pd.Timestamp("2014-01-01")
    eggs = load(DATA / "multi2" / "JD0.csv")
    mt = load(DATA / "multi" / "sh600519.csv")
    eggs, mt = eggs[eggs.index >= s0], mt[mt.index >= s0]
    fig = plt.figure(figsize=(7.2, 3.1), facecolor=BG)
    for i, (s, nm, th, note) in enumerate([(eggs, "鸡蛋期货", 0.25, "两三年就转一圈"),
                                           (mt, "贵州茅台（后复权）", 0.40, "涨了七年，2021年以后转进秋冬")]):
        ax = fig.add_axes([0.05 + i * 0.5, 0.11, 0.43, 0.66], facecolor=BG)
        pts = zigzag_legs(s, th)
        for a, b in zip(pts[:-1], pts[1:]):
            seg = s.iloc[a:b + 1]
            ax.plot(seg.index, seg.values, color=GOLD if seg.iloc[-1] > seg.iloc[0] else BLUE, lw=1.3)
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(plt.NullFormatter())
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.tick_params(axis="y", which="both", length=0)
        ax.tick_params(axis="x", colors=MUTED, labelsize=7.5)
        for lab in ax.get_xticklabels():
            lab.set_fontproperties(SANS); lab.set_fontsize(7.5)
        for sp in ["top", "right", "left"]:
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(LINE)
        fig.text(0.05 + i * 0.5, 0.9, nm, fontproperties=SANSB, fontsize=10, color=INK)
        fig.text(0.05 + i * 0.5, 0.82, note, fontproperties=SANS, fontsize=8.5, color=MUTED)
    save(fig, "圈的大小.png")


# ---------------------------------------------------------------- 图5 一轮行情走一遍
def path_fig():
    fig, ax, H = canvas(7.2, 3.9)
    peak, bot = draw_path(ax, 5, 6, 0.9, 0.5, label=9.5, dot=1.75)
    ax.plot([5, 95], [7.6, 7.6], color=LINE, lw=0.8, zorder=1)
    pill(ax, 12, 3.2, "冬至 · 最冷", BLUE, 8)
    ax.plot([peak[0] - 12, peak[0] - 0.8], [peak[1] - 0.5, peak[1] - 0.5], color=GOLD, lw=0.8, ls=":", zorder=2)
    pill(ax, peak[0] - 18, peak[1] - 0.5, "夏至 · 最热", GOLD, 8)
    T(ax, 5 + 96 * 0.9, 6 + 18 * 0.5, "下一轮", 8, "r", GOLD, ha="center", va="bottom")
    T(ax, 95, H - 3, "只定位置，不算时间", 8.5, "r", MUTED, ha="right", va="center")
    save(fig, "一轮行情走一遍.png")


# ---------------------------------------------------------------- 图6 第零步
def step_zero():
    fig, ax, H = canvas(7.2, 4.5)
    qs = [("它的价格最后靠什么兑现？", "这是它的锚"), ("谁说了算，他要什么？", "人性看的是这拨人做了什么"),
          ("圈靠什么转，一圈多久？", "母猪十个月，药材三五年")]
    cw, gap = 29.4, 1.9
    for i, (q, a) in enumerate(qs):
        x = 4 + i * (cw + gap)
        card(ax, x, H - 16, cw, 13)
        ax.add_patch(Circle((x + 3.6, H - 7.4), 1.9, fc=GOLD, ec="none", zorder=3))
        T(ax, x + 3.6, H - 7.5, str(i + 1), 8.5, "b", BG, ha="center", va="center", zorder=4)
        T(ax, x + 6.6, H - 7.4, q, 8.9, "b", INK, va="center")
        T(ax, x + 2.6, H - 12.6, a, 7.8, "r", MUTED, va="center")
    arrow(ax, (50, H - 17), (50, H - 21.5), c=GOLD, lw=1.3, ms=11)
    pill(ax, 50, H - 24.5, "先认锚，再定谁当家", GOLD, 10.5, w="b")
    cols = [("锚：实物", "猪、药材、铜、钢材", "条件当家", "地利：供求在变好还是变坏", GOLD),
            ("锚：政策和钱", "A股的指数", "人和当家", "杠杆资金在加还是在减，新股增发多发还是少发", GOLD),
            ("锚：将来的钱", "个股", "先看大圈", "大盘和行业在哪个季节；个股只看比大圈强还是弱", BLUE)]
    for i, (anc, ex, boss, how, c) in enumerate(cols):
        x = 4 + i * (cw + gap)
        y = 7.5
        card(ax, x, y, cw, H - 36.5, ec=c, fc=BG, lw=1.1)
        T(ax, x + 2.6, y + H - 41.5, anc, 8.6, "b", MUTED, va="center")
        T(ax, x + 2.6, y + H - 46, ex, 8.3, "r", TXT, va="center")
        T(ax, x + 2.6, y + 9.5, boss, 14, "s", c, va="center")
        T(ax, x + 2.6, y + 3.6, how if len(how) <= 15 else how.replace("，", "，\n", 1).replace("；", "；\n", 1), 7.4, "r", TXT,
          va="center", linespacing=1.35)
    T(ax, 50, 3.0, "天时不当家：只看价格和人气，分不清上半圈还是下半圈", 8.3, "r", MUTED, ha="center", va="center")
    save(fig, "第零步.png")


# ---------------------------------------------------------------- 图7 消息怎么看
def news():
    fig, ax, H = canvas(7.2, 3.5)

    def box(x, y, w, h, t1, t2=None, ec=LINE, tc=INK, fc=PANEL, s1=9.5):
        card(ax, x, y, w, h, ec=ec, fc=fc, lw=1.1)
        T(ax, x + w / 2, y + h / 2 + (2.1 if t2 else 0), t1, s1, "b", tc, ha="center", va="center")
        if t2:
            T(ax, x + w / 2, y + h / 2 - 2.6, t2, 7.4, "r", MUTED, ha="center", va="center", linespacing=1.35)

    my = H / 2 + 1
    box(2, my - 5, 13, 10, "一条消息")
    arrow(ax, (15.2, my), (19.3, my))
    box(19.5, my - 8, 21, 16, "这件事对不对？", "能不能对上产量、库存、\n订单、公告、成交", ec=INK)
    box(46, my + 3.5, 25, 13.5, "对：归到条件里去观", "动机次要：订单是真的，\n订单就还是订单", ec=GOLD, tc=GOLD, fc=BG)
    box(46, my - 17, 25, 13.5, "对不上：这时才问动机", "谁放的？什么时候放的？\n想让你买、卖，还是别动？", ec=BLUE, tc=BLUE, fc=BG)
    arrow(ax, (40.7, my + 2.5), (45.8, my + 9), c=GOLD)
    arrow(ax, (40.7, my - 2.5), (45.8, my - 9), c=BLUE)
    arrow(ax, (71.2, my + 9), (76.3, my + 2.5))
    arrow(ax, (71.2, my - 9), (76.3, my - 2.5))
    box(76.5, my - 9, 21.5, 18, "看价格的反应", "想让你买却不涨：兑现\n想让你卖却不跌：绝望", ec=INK)
    T(ax, 50, 2.6, "消息是话，反应是钱", 10, "s", GOLD, ha="center", va="center")
    save(fig, "消息怎么看.png")


# ---------------------------------------------------------------- 图8 观一样东西，走六步
def steps():
    fig, ax, H = canvas(7.2, 3.75)
    items = [("认清这个东西", "靠什么兑现，谁说了算，\n圈靠什么转"),
             ("观三股力的正反面", "条件、时机，\n和说了算的人做了什么"),
             ("看当家的那股力", None),
             ("定在半圈里的哪一段", "其他两股力定位置；\n回头观，前面走完了哪一段"),
             ("写下观错的信号", "出现什么，\n就说明我观错了"),
             ("算好最坏", "认错的位置在哪，最多亏多少，\n能接受才做")]
    cw, ch, gx, gy = 29.4, 15, 1.9, 3.2
    for i, (t1, t2) in enumerate(items):
        r, c = divmod(i, 3)
        x, y = 4 + c * (cw + gx), H - 4 - (r + 1) * ch - r * gy
        card(ax, x, y, cw, ch)
        ax.add_patch(Circle((x + 3.8, y + ch - 3.8), 2.1, fc=BG, ec=GOLD, lw=1.4, zorder=3))
        T(ax, x + 3.8, y + ch - 3.9, str(i + 1), 9, "b", GOLD, ha="center", va="center", zorder=4)
        T(ax, x + 7.2, y + ch - 3.8, t1, 9.3, "b", INK, va="center")
        if t2 is None:
            T(ax, x + 3, y + 6.2, "往上：上半圈", 8.3, "b", GOLD, va="center")
            T(ax, x + 3, y + 2.8, "往下：下半圈", 8.3, "b", BLUE, va="center")
        else:
            T(ax, x + 3, y + 4.4, t2, 7.7, "r", MUTED, va="center", linespacing=1.4)
        if c < 2:
            arrow(ax, (x + cw + 0.1, y + ch / 2), (x + cw + gx - 0.1, y + ch / 2), c=MUTED, ms=8, lw=0.9)
    xa = 4 + 2 * (cw + gx) + cw / 2
    y1 = H - 4 - ch
    ax.plot([xa, xa], [y1, y1 - gy / 2], color=MUTED, lw=0.9)
    ax.plot([xa, 4 + cw / 2], [y1 - gy / 2, y1 - gy / 2], color=MUTED, lw=0.9)
    arrow(ax, (4 + cw / 2, y1 - gy / 2), (4 + cw / 2, y1 - gy + 0.1), c=MUTED, ms=8, lw=0.9)
    yb = H - 4 - 2 * ch - gy - 5.5
    T(ax, 4, yb, "然后才是怎么做：", 9.3, "b", INK, va="center")
    for j, (wd, d, c) in enumerate([("狠", "对的时候", GOLD), ("拿", "条件撑着", GOLD), ("忍", "还没到时候", BLUE),
                                    ("断", "错了就走", BLUE), ("趴", "势不对", BLUE)]):
        x = 25 + j * 14.8
        card(ax, x, yb - 4.4, 13.2, 8.8, ec=c, fc=BG, lw=1.1)
        T(ax, x + 3.6, yb, wd, 14, "s", c, ha="center", va="center")
        T(ax, x + 8.9, yb, d, 7, "r", MUTED, ha="center", va="center")
    save(fig, "观的步骤.png")


# ---------------------------------------------------------------- 图9 条件和时机怎么配
def quadrant():
    fig, ax, H = canvas(7.2, 3.9)
    x0, y0, W, Hh = 14, 7.5, 82, H - 11
    cells = [(1, 1, "狠", "条件撑着，时机也顺：主仓上，拿住", GOLD, 1.6),
             (0, 1, "忍", "条件撑着，时机还逆：小钱先站位置，等", GOLD, 1.0),
             (1, 0, "不追", "条件不撑，时机还顺：热是虚的，有的减", BLUE, 1.0),
             (0, 0, "趴", "条件不撑，时机也逆：像乌龟一样趴着", BLUE, 1.6)]
    for cx, cy, big, small, c, lw in cells:
        x, y = x0 + cx * W / 2, y0 + cy * Hh / 2
        card(ax, x + 0.7, y + 0.7, W / 2 - 1.4, Hh / 2 - 1.4, ec=c, fc=PANEL if lw > 1.2 else BG, lw=lw)
        T(ax, x + 4.5, y + Hh / 4 + 0.5, big, 21 if len(big) == 1 else 16, "s", c, va="center")
        T(ax, x + (13 if len(big) == 1 else 16), y + Hh / 4 + 0.5, small.replace("：", "：\n"), 8.2, "r", TXT,
          va="center", linespacing=1.45)
    T(ax, x0 + W / 4, y0 - 3.4, "时机逆：钱在走，趋势向下", 8.2, "r", BLUE, ha="center", va="center")
    T(ax, x0 + 3 * W / 4, y0 - 3.4, "时机顺：钱在进，趋势向上", 8.2, "r", GOLD, ha="center", va="center")
    T(ax, x0 - 2.5, y0 + 3 * Hh / 4, "条件\n撑着", 9, "b", GOLD, ha="right", va="center")
    T(ax, x0 - 2.5, y0 + Hh / 4, "条件\n不撑", 9, "b", BLUE, ha="right", va="center")
    save(fig, "条件和时机.png")


# ---------------------------------------------------------------- 图10 仓位的火候
def heat():
    fig, ax, H = canvas(7.2, 3.1)
    pos = [1 / 3, 2 / 3, 1, 1, 1, 0.5, 0.5, 0.5, 0, 0, 0, 0]
    word = ["试", "加", "狠", "拿", "不加", "减", "忍", "断", "趴", "趴", "趴", "等"]
    x0, bw, base, top = 9.5, 7.3, 9.5, 26
    for lv, lab in [(0, "空仓"), (1 / 3, "1/3"), (2 / 3, "2/3"), (1, "满")]:
        y = base + lv * top
        ax.plot([x0 - 0.5, x0 + 12 * bw], [y, y], color=LINE, lw=0.6, zorder=1)
        T(ax, x0 - 1.5, y, lab, 7.5, "r", MUTED, ha="right", va="center")
    for k in range(12):
        x = x0 + k * bw + 0.8
        h = pos[k] * top
        c, cf = (GOLD, GOLD_F) if k < 6 else (BLUE, BLUE_F)
        if k in (6, 7):
            ax.add_patch(Rectangle((x, base), bw - 1.6, h, fc="none", ec=c, lw=1.1, hatch="////", zorder=3))
        elif h > 0:
            card(ax, x, base, bw - 1.6, h, ec="none", fc=cf, r=0.5, z=3)
        T(ax, x + (bw - 1.6) / 2, base + h + 1.6, word[k], 10 if len(word[k]) == 1 else 8.5, "s", c, ha="center", va="bottom")
        T(ax, x + (bw - 1.6) / 2, base - 1.8, STAGES[k] if k != 3 else "大众\n共识", 7.2, "b", c, ha="center", va="top",
          linespacing=0.95)
    T(ax, x0 + 7.5 * bw, base + 0.5 * top + 6.5, "斜线：拿着剩下的，跌破认错线就清零", 7.4, "r", MUTED, ha="center", va="bottom")
    save(fig, "仓位火候.png")


if __name__ == "__main__":
    cover(); sun_temp(); forces_grid(); wheel(); circles(); path_fig()
    step_zero(); news(); steps(); quadrant(); heat()
