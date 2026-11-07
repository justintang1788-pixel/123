"""论文用图（深色海报风格）：金色＝涨、正面；蓝色＝跌、反面。输出到 paper/images_v5/。

跑法：python3 figs.py
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
DPI = 220

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

BG, PANEL, LINE = "#101927", "#172336", "#2C3B52"
CREAM, TXT, MUTED = "#EFE7D6", "#D9DFE8", "#8A96A8"
GOLD, BLUE = "#E3A73C", "#6F98CC"
GOLD_D, BLUE_D = "#9C6E22", "#34557F"
STAGES = ["绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]
QUOTE = ["回本就卖", "等回调再买", "要不要上车", "还能上车吗", "这次不一样", "拿住就是格局",
         "正常回调", "不卖不算亏", "这么便宜为啥还跌", "不看了", "割了，销户", "这还有人看？"]
DO = ["小钱先站位置", "回踩不破就加", "主仓上，拿住", "拿稳，不追加", "不买新的，盯住条件", "减仓，破位就走",
      "忍住不抄底，反弹时减", "断舍离", "趴着，不补仓", "空着，记下不跟跌的", "不抄底，借钱的先减", "观条件，等信号"]


def col(k):
    return GOLD if k < 6 else BLUE


def T(ax, x, y, s, size=10, w="r", c=TXT, **kw):
    fp = {"r": SANS, "b": SANSB, "s": SERIF}[w]
    return ax.text(x, y, s, fontproperties=fp, fontsize=size, color=c, **kw)


def canvas(w, h):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    ax.set_facecolor(BG)
    return fig, ax


def pill(ax, x, y, s, c, size=9, pad=0.6, w="r", fc=None):
    t = T(ax, x, y, s, size, w, c, ha="center", va="center", zorder=6)
    t.set_bbox(dict(boxstyle=f"round,pad={pad},rounding_size=1.2", fc=fc or BG, ec=c, lw=1.1))
    return t


def numdot(ax, x, y, k, r=1.9, size=8.5, fill=False):
    c = col(k)
    ax.add_patch(Circle((x, y), r, fc=(c if fill else BG), ec=c, lw=1.6, zorder=7))
    T(ax, x, y - 0.05, str(k + 1), size, "b", BG if fill else c, ha="center", va="center", zorder=8)


def save(fig, name):
    fig.savefig(IMG / name, dpi=DPI, facecolor=BG)
    plt.close(fig)
    print("存好", name)


# ---------------------------------------------------------------- 一轮行情的路径（示意）
PATH = [(0, 16), (3, 12), (6, 9.5),                                   # 上一轮的尾巴
        (9.5, 14), (11.5, 11.5), (15.5, 19), (17.5, 16.5), (21.5, 25), (23.5, 22.5), (27.5, 33),
        (29.5, 30.5), (33.5, 44), (35, 41.5), (39.5, 64), (42, 86), (43.8, 78), (45.8, 84), (47.6, 79.5), (49.2, 84),
        (53, 66), (54.6, 70), (58.4, 57.5), (60, 60.5), (63.6, 50), (65.6, 46), (67.6, 49.5), (71.4, 41), (73.4, 44),
        (76.6, 36), (79.5, 24), (81.5, 12), (84.5, 7.5), (88.5, 6.5), (91, 8.5)]
NEXT = [(91, 8.5), (93.5, 12.5), (95.5, 11), (98, 15)]
MARK = {0: 3, 1: 5, 2: 9, 3: 11, 4: 13, 5: 16, 6: 20, 7: 21, 8: 24, 9: 29, 10: 30, 11: 32}   # 阶段 → 路径上第几个点
LABEL_SIDE = {0: (-1, 1), 1: (1, -1), 2: (-1, 1), 3: (-1, 1), 4: (-1, 1), 5: (0, 1),
              6: (1, 1), 7: (-1, -1), 8: (1, 1), 9: (1, 1), 10: (1, 1), 11: (0, -1)}


def draw_path(ax, x0, y0, sx, sy, label_size=11, dot=1.9, show_labels=True):
    P = np.array(PATH, float)
    X, Y = x0 + P[:, 0] * sx, y0 + P[:, 1] * sy
    up_end = 16 + 1
    ax.plot(X[:4], Y[:4], color=LINE, lw=2.2, solid_capstyle="round", zorder=3)
    ax.plot(X[3:up_end + 1], Y[3:up_end + 1], color=GOLD, lw=2.4, solid_joinstyle="round", zorder=4)
    ax.plot(X[up_end:], Y[up_end:], color=BLUE, lw=2.4, solid_joinstyle="round", zorder=4)
    N = np.array(NEXT, float)
    ax.plot(x0 + N[:, 0] * sx, y0 + N[:, 1] * sy, color=GOLD, lw=2.0, ls=(0, (1, 2.2)), zorder=4)
    for k, i in MARK.items():
        numdot(ax, X[i], Y[i], k, r=dot, size=dot * 4.4)
        if show_labels:
            dx, dy = LABEL_SIDE[k]
            ha = "right" if dx < 0 else ("left" if dx > 0 else "center")
            T(ax, X[i] + dx * (dot + 1.2), Y[i] + dy * (dot + 1.6), STAGES[k], label_size, "b", CREAM,
              ha=ha, va="bottom" if dy > 0 else "top", zorder=8)
    return X, Y


# ---------------------------------------------------------------- 封面
def cover():
    fig, ax = canvas(7.2, 10.2)
    H = 100 * 10.2 / 7.2
    T(ax, 8, H - 9, "市 场 周 期 方 法 论", 10, "r", MUTED, va="center")
    T(ax, 7, H - 22, "冬至理论", 66, "s", CREAM, va="center")
    T(ax, 8, H - 34.5, "一个关于市场冷热循环的十二阶段模型", 14, "r", TXT, va="center")
    T(ax, 8, H - 40.5, "JustinTang洛辰", 12, "r", TXT, va="center")
    T(ax, 8, H - 50, "最冷的那天，太阳已经回头；", 17, "s", GOLD, va="center")
    T(ax, 8, H - 57, "最热的那天，太阳已经要走。", 17, "s", BLUE, va="center")
    X, Y = draw_path(ax, 8, 16, 0.85, 0.62, label_size=10.5, dot=1.9)
    ax.plot([8, 92], [17.5, 17.5], color=LINE, lw=0.8, zorder=1)
    pill(ax, 15, 12.5, "冬至 · 最冷", BLUE, 9)
    peak = (8 + 42 * 0.85, 16 + 86 * 0.62)
    ax.plot([peak[0] - 12.5, peak[0] - 0.8], [peak[1] - 0.5, peak[1] - 0.5], color=GOLD, lw=0.8, ls=":", zorder=2)
    pill(ax, peak[0] - 19, peak[1] - 0.5, "夏至 · 最热", GOLD, 9)
    T(ax, 8 + 97 * 0.85, 16 + 19 * 0.62, "下一轮", 9, "r", GOLD, ha="center", va="bottom")
    ax.plot([8, 92], [7.5, 7.5], color=LINE, lw=0.8)
    T(ax, 8, 4, "市场只有一个方向：做对", 10, "r", MUTED, va="center")
    T(ax, 92, 4, "二〇二六年十一月", 10, "r", MUTED, va="center", ha="right")
    save(fig, "封面.png")


# ---------------------------------------------------------------- 图：一轮行情 + 每段的口头禅和做法
def path_list():
    fig, ax = canvas(7.2, 10.6)
    H = 100 * 10.6 / 7.2
    T(ax, 6, H - 5, "一轮行情走一遍", 15, "s", CREAM, va="center")
    T(ax, 94, H - 5, "只定位置，不算时间", 9.5, "r", MUTED, va="center", ha="right")
    base = H - 66
    draw_path(ax, 6, base + 2, 0.88, 0.55, label_size=10.5, dot=1.9)
    ax.plot([6, 94], [base + 3.6, base + 3.6], color=LINE, lw=0.8, zorder=1)
    pill(ax, 13, base - 0.6, "冬至 · 最冷", BLUE, 8.5)
    pk = (6 + 42 * 0.88, base + 2 + 86 * 0.55)
    ax.plot([pk[0] - 12.5, pk[0] - 0.8], [pk[1] - 0.5, pk[1] - 0.5], color=GOLD, lw=0.8, ls=":", zorder=2)
    pill(ax, pk[0] - 19, pk[1] - 0.5, "夏至 · 最热", GOLD, 8.5)
    T(ax, 6 + 96 * 0.88, base + 2 + 18 * 0.55, "下一轮", 8.5, "r", GOLD, ha="center", va="bottom")
    # 两列清单
    top = base - 7
    for side, (x, title, c) in enumerate([(6, "上涨六段", GOLD), (52, "下跌六段", BLUE)]):
        T(ax, x, top, title, 12, "b", c, va="center")
        ax.plot([x, x + 42], [top - 2.6, top - 2.6], color=LINE, lw=0.8)
        for j in range(6):
            k = side * 6 + j
            y = top - 7.2 - j * 9.3
            numdot(ax, x + 2, y, k, r=1.7, size=7.5)
            T(ax, x + 5.5, y + 0.2, STAGES[k], 11, "b", CREAM, va="center")
            T(ax, x + 5.5 + 2.6 * len(STAGES[k]) + 1.5, y + 0.2, f"“{QUOTE[k]}”", 9, "r", MUTED, va="center")
            T(ax, x + 5.5, y - 3.6, "→ " + DO[k], 9.2, "r", c, va="center")
    save(fig, "一轮行情走一遍.png")


# ---------------------------------------------------------------- 图：太阳和气温的时间差
def sun_temp():
    fig, ax = canvas(7.2, 4.6)
    H = 100 * 4.6 / 7.2
    t = np.linspace(0, 12, 400)                    # 从9月下旬起，一年
    dz = 3.0                                       # 冬至
    mid, amp = H / 2 - 2, 14
    X = lambda tt: 8 + tt / 12 * 84
    sun = mid - amp * np.cos(2 * np.pi * (t - dz) / 12)
    tmp = mid - amp * np.cos(2 * np.pi * (t - dz - 1.0) / 12)   # 晚一个月左右
    ax.plot([8, 92], [mid, mid], color=LINE, lw=0.7, zorder=1)
    ax.plot(X(t), sun, color=CREAM, lw=2.2, zorder=4)
    ax.plot(X(t), tmp, color=GOLD, lw=2.0, ls=(0, (4, 2.5)), zorder=4)
    lo, hi = mid - amp, mid + amp
    for tt, yy, c in [(dz, lo, BLUE), (dz + 1, lo, BLUE), (dz + 6, hi, GOLD), (dz + 7, hi, GOLD)]:
        ax.add_patch(Circle((X(tt), yy), 1.0, fc=c, ec="none", zorder=6))
    T(ax, X(dz) - 1.5, lo - 3.5, "冬至：太阳回头", 9.5, "b", BLUE, ha="right", va="top")
    T(ax, X(dz + 1) + 1.5, lo - 3.5, "最冷：三九", 9.5, "b", BLUE, ha="left", va="top")
    T(ax, X(dz + 6) - 1.5, hi + 3.5, "夏至：太阳要走", 9.5, "b", GOLD, ha="right", va="bottom")
    T(ax, X(dz + 7) + 1.5, hi + 3.5, "最热：三伏", 9.5, "b", GOLD, ha="left", va="bottom")
    for a1, yy, va in [(dz, lo - 10.5, "top"), (dz + 6, hi + 10.5, "bottom")]:
        ax.add_patch(FancyArrowPatch((X(a1), yy), (X(a1 + 1), yy), arrowstyle="<->", mutation_scale=9, color=MUTED, lw=1))
        T(ax, X(a1 + 0.5), yy + (-1.5 if va == "top" else 1.5), "差一个月左右", 8.5, "r", MUTED, ha="center", va=va)
    ax.plot([9, 14], [H - 6, H - 6], color=CREAM, lw=2.2)
    T(ax, 15.5, H - 6, "太阳（白天长短）", 9, "r", TXT, va="center")
    ax.plot([40, 45], [H - 6, H - 6], color=GOLD, lw=2.0, ls=(0, (4, 2.5)))
    T(ax, 46.5, H - 6, "冷热（人的感觉）", 9, "r", TXT, va="center")
    save(fig, "太阳和气温.png")


# ---------------------------------------------------------------- 图：三股力怎么一股一股翻面
# 每一段三股力的状态：1 正面，0 反面，0.5 反面走完、正在翻到正面，-0.5 正面走完、正在翻到反面
STATE = {  # 条件、时机、人性
    0: (0.5, 0, 0), 1: (1, 0, 0), 2: (1, 0.5, 0), 3: (1, 1, 0), 4: (1, 1, 0.5), 5: (1, 1, 1),
    6: (-0.5, 1, 1), 7: (0, 1, 1), 8: (0, -0.5, 1), 9: (0, 0, 1), 10: (0, 0, -0.5), 11: (0, 0, 0)}


def forces_grid():
    fig, ax = canvas(7.2, 4.0)
    H = 100 * 4.0 / 7.2
    rows = [("条件", "地 · 事实"), ("时机", "天 · 钱和趋势"), ("人性", "人 · 贪和怕")]
    x0, cw, ch, gap = 17, 6.5, 8.6, 0.55
    ytop = H - 14
    for k in range(12):
        x = x0 + k * cw
        numdot(ax, x + cw / 2 - gap / 2, ytop + 7.6, k, r=1.6, size=7)
        T(ax, x + cw / 2 - gap / 2, ytop + 3.2, STAGES[k] if len(STAGES[k]) <= 2 else "大众\n共识", 7.6, "b", col(k),
          ha="center", va="center", linespacing=0.95)
    for r, (nm, sub) in enumerate(rows):
        y = ytop - r * (ch + gap) - ch
        T(ax, x0 - 1.5, y + ch / 2 + 1.4, nm, 11, "b", CREAM, ha="right", va="center")
        T(ax, x0 - 1.5, y + ch / 2 - 2.2, sub, 6.8, "r", MUTED, ha="right", va="center")
        for k in range(12):
            s = STATE[k][r]
            x = x0 + k * cw
            w, h = cw - gap, ch
            if s in (0, 1):
                ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                            fc=GOLD if s == 1 else BLUE_D, ec="none", alpha=0.95 if s == 1 else 0.9))
            else:
                old, new = (BLUE_D, GOLD) if s > 0 else (GOLD, BLUE_D)
                ax.add_patch(Polygon([(x, y), (x + w, y), (x, y + h)], fc=old, ec="none"))
                ax.add_patch(Polygon([(x + w, y), (x + w, y + h), (x, y + h)], fc=new, ec="none"))
                ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=CREAM, lw=1.3))
                T(ax, x + w / 2, y + h / 2, "翻", 9, "b", CREAM, ha="center", va="center",
                  bbox=dict(boxstyle="circle,pad=0.15", fc=BG, ec="none"))
    yb = ytop - 3 * (ch + gap) - 4
    ax.plot([x0 + 6 * cw - gap / 2 - 0.0, x0 + 6 * cw - gap / 2], [yb + 1, ytop + 10], color=MUTED, lw=0.6, ls=":")
    T(ax, x0 + 3 * cw, yb - 1.5, "上涨六段：条件先转，时机跟着，人性最后", 8.5, "r", GOLD, ha="center", va="center")
    T(ax, x0 + 9 * cw, yb - 1.5, "下跌六段：还是条件先转，人性最后", 8.5, "r", BLUE, ha="center", va="center")
    for i, (c, s) in enumerate([(GOLD, "正面"), (BLUE_D, "反面")]):
        ax.add_patch(Rectangle((x0 + i * 13, 2.2), 3.2, 2.6, fc=c, ec="none"))
        T(ax, x0 + i * 13 + 4.2, 3.4, s, 8.5, "r", TXT, va="center")
    ax.add_patch(Polygon([(x0 + 26, 2.2), (x0 + 29.2, 2.2), (x0 + 26, 4.8)], fc=BLUE_D))
    ax.add_patch(Polygon([(x0 + 29.2, 2.2), (x0 + 29.2, 4.8), (x0 + 26, 4.8)], fc=GOLD))
    T(ax, x0 + 30.2, 3.4, "这一段正在翻面的那股力", 8.5, "r", TXT, va="center")
    save(fig, "三股力翻面.png")


# ---------------------------------------------------------------- 图：十二阶段循环
def wheel():
    fig, ax = canvas(7.2, 6.6)
    H = 100 * 6.6 / 7.2
    cx, cy, R, w = 50, H / 2 - 1, 30, 11
    warm = ["#F0CF8A", "#EBBB62", "#E3A73C", "#D38F2C", "#BC7722", "#9C6018"]
    cool = ["#A9C2E2", "#8FAED7", "#7598C8", "#5D82B6", "#4B6EA0", "#3A5A86"]
    for k in range(12):
        a = 270 - (k + 1) * 30
        c = (warm + cool)[k]
        ax.add_patch(Wedge((cx, cy), R, a + 0.6, a + 30 - 0.6, width=w, fc=c, ec=BG, lw=1.5))
        mid = np.deg2rad(a + 15)
        rr = R - w / 2
        tx, ty = cx + rr * np.cos(mid), cy + rr * np.sin(mid)
        T(ax, tx, ty + 1.6, str(k + 1), 8, "b", BG, ha="center", va="center")
        T(ax, tx, ty - 1.6, STAGES[k] if k != 3 else "大众共识", 8.6 if k != 3 else 7.4, "b", BG, ha="center", va="center")
    for k in range(12):                                   # 外圈箭头，顺时针
        a = np.deg2rad(270 - (k + 0.5) * 30)
        b = np.deg2rad(270 - (k + 0.5) * 30 - 18)
        r2 = R + 2.6
        ax.add_patch(FancyArrowPatch((cx + r2 * np.cos(a), cy + r2 * np.sin(a)), (cx + r2 * np.cos(b), cy + r2 * np.sin(b)),
                                     connectionstyle="arc3,rad=-0.12", arrowstyle="-|>", mutation_scale=7,
                                     color=(GOLD if k < 6 else BLUE), lw=1, alpha=0.8))
    T(ax, cx, cy + 3.5, "冬至理论", 17, "s", CREAM, ha="center", va="center")
    T(ax, cx, cy - 2.5, "十二阶段，转圈不停", 9, "r", MUTED, ha="center", va="center")
    pill(ax, cx, cy + R + 7, "夏至 · 最热：人性贪到头，条件开始转身", GOLD, 8.5)
    pill(ax, cx, cy - R - 7, "冬至 · 最冷：人性怕到头，条件开始回头", BLUE, 8.5)
    T(ax, cx - R - 6, cy, "上\n涨\n六\n段", 11, "b", GOLD, ha="center", va="center", linespacing=1.15)
    T(ax, cx + R + 6, cy, "下\n跌\n六\n段", 11, "b", BLUE, ha="center", va="center", linespacing=1.15)
    save(fig, "十二阶段循环.png")


# ---------------------------------------------------------------- 图：圈的大小（真实数据）
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
    eggs = load(DATA / "multi2" / "JD0.csv")
    mt = load(DATA / "multi" / "sh600519.csv")
    s0 = pd.Timestamp("2014-01-01")
    eggs, mt = eggs[eggs.index >= s0], mt[mt.index >= s0]
    fig = plt.figure(figsize=(7.2, 3.6), facecolor=BG)
    for i, (s, nm, th, note) in enumerate([(eggs, "鸡蛋期货", 0.25, "两三年就转一圈"),
                                           (mt, "贵州茅台（后复权）", 0.40, "涨了七年，2021年以后转进秋冬")]):
        ax = fig.add_axes([0.07 + i * 0.49, 0.12, 0.42, 0.68], facecolor=BG)
        pts = zigzag_legs(s, th)
        for a, b in zip(pts[:-1], pts[1:]):
            seg = s.iloc[a:b + 1]
            ax.plot(seg.index, seg.values, color=GOLD if seg.iloc[-1] > seg.iloc[0] else BLUE, lw=1.4)
        ax.set_yscale("log")
        ax.tick_params(colors=MUTED, labelsize=7.5, which="both")
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(SANS); lab.set_fontsize(7.5)
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.yaxis.set_major_formatter(plt.NullFormatter())
        ax.tick_params(axis="y", which="both", length=0)
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
        for sp in ["left", "bottom"]:
            ax.spines[sp].set_color(LINE)
        fig.text(0.07 + i * 0.49, 0.9, nm, fontproperties=SANSB, fontsize=11, color=CREAM)
        fig.text(0.07 + i * 0.49, 0.835, note, fontproperties=SANS, fontsize=9, color=MUTED)
    fig.text(0.97, 0.965, "金色：一段涨　蓝色：一段跌", fontproperties=SANS, fontsize=8.5, color=MUTED, ha="right")
    save(fig, "圈的大小.png")


# ---------------------------------------------------------------- 图：第零步
def step_zero():
    fig, ax = canvas(7.2, 6.6)
    H = 100 * 6.6 / 7.2
    T(ax, 6, H - 6, "第零步：先认清这个东西", 15, "s", CREAM, va="center")
    qs = [("它的价格最后\n靠什么兑现？", "这是它的锚"), ("谁说了算，\n他要什么？", "人性看的是这拨人做了什么"),
          ("圈靠什么转，\n一圈多久？", "母猪十个月，药材三五年")]
    for i, (q, a) in enumerate(qs):
        x = 6 + i * 30.3
        ax.add_patch(FancyBboxPatch((x, H - 33), 27.5, 20, boxstyle="round,pad=0,rounding_size=2", fc=PANEL, ec=LINE, lw=1))
        ax.add_patch(Circle((x + 4.5, H - 17.5), 2.3, fc=GOLD, ec="none"))
        T(ax, x + 4.5, H - 17.6, str(i + 1), 10, "b", BG, ha="center", va="center")
        T(ax, x + 8.5, H - 19.5, q, 11, "b", CREAM, va="center", linespacing=1.3)
        T(ax, x + 3, H - 29.5, a, 8.5, "r", MUTED, va="center")
    ax.add_patch(FancyArrowPatch((50, H - 35), (50, H - 41), arrowstyle="-|>", mutation_scale=12, color=GOLD, lw=1.4))
    pill(ax, 50, H - 44.5, "先认锚，再定谁当家", GOLD, 12, pad=0.7, w="b")
    cols = [("实物", "猪、药材、铜、钢材", "条件当家", "地利：供求在变好还是变坏", GOLD),
            ("政策和钱", "A股的指数", "人和当家", "杠杆资金在加还是在减，\n新股增发在多发还是少发", GOLD),
            ("将来的钱", "个股", "先看大圈", "大盘和行业在哪个季节，\n个股只看它比大圈强还是弱", BLUE)]
    for i, (anc, ex, boss, how, c) in enumerate(cols):
        x = 6 + i * 30.3
        y = H - 82
        ax.add_patch(FancyBboxPatch((x, y), 27.5, 31, boxstyle="round,pad=0,rounding_size=2", fc=PANEL, ec=LINE, lw=1))
        T(ax, x + 3, y + 26.5, "锚：" + anc, 10, "b", MUTED, va="center")
        T(ax, x + 3, y + 21.5, ex, 9, "r", TXT, va="center")
        ax.plot([x + 3, x + 24.5], [y + 18, y + 18], color=LINE, lw=0.8)
        T(ax, x + 3, y + 13, boss, 15, "s", c, va="center")
        T(ax, x + 3, y + 5.5, how, 8.2, "r", TXT, va="center", linespacing=1.4)
    T(ax, 50, 4.5, "天时不当家：只看价格和人气，分不清上半圈还是下半圈", 9.5, "r", MUTED, ha="center", va="center")
    save(fig, "第零步.png")


# ---------------------------------------------------------------- 图：判断阶段的步骤
def steps():
    fig, ax = canvas(7.2, 8.9)
    H = 100 * 8.9 / 7.2
    T(ax, 6, H - 6, "观一样东西，走六步", 15, "s", CREAM, va="center")
    items = [("认清这个东西", "靠什么兑现，谁说了算，圈靠什么转；先认锚，再定谁当家"),
             ("观三股力的正反面", "条件：事实往哪边变；时机：钱和趋势；人性：说了算的人做了什么"),
             ("看当家的那股力往哪边走", None),
             ("其他两股力，定在半圈里的哪一段", "回头观：前面哪一段已经走完了，下一段可能是什么"),
             ("写下：出现什么，就说明我观错了", "比如“跌破前面的最低点，说明条件还没转完”"),
             ("算好最坏，能接受才做", "认错的位置在哪，最多亏多少钱")]
    y = H - 17
    ys = []
    for i, (t1, t2) in enumerate(items):
        ys.append(y)
        ax.add_patch(Circle((10, y), 2.6, fc=BG, ec=GOLD, lw=1.6, zorder=5))
        T(ax, 10, y - 0.1, str(i + 1), 10.5, "b", GOLD, ha="center", va="center", zorder=6)
        T(ax, 16, y + 1.6, t1, 12, "b", CREAM, va="center")
        if t2:
            T(ax, 16, y - 3.0, t2, 8.8, "r", MUTED, va="center")
            y -= 12.5
        else:
            for j, (lab, sub, c) in enumerate([("往上：上半圈", "绝望 → 兑现", GOLD), ("往下：下半圈", "幻想 → 衰竭", BLUE)]):
                xx = 16 + j * 30
                ax.add_patch(FancyBboxPatch((xx, y - 9.5), 26, 6.6, boxstyle="round,pad=0,rounding_size=1.5", fc=PANEL, ec=c, lw=1.1))
                T(ax, xx + 2, y - 6.2, lab, 9.5, "b", c, va="center")
                T(ax, xx + 24, y - 6.2, sub, 8.5, "r", MUTED, va="center", ha="right")
            y -= 17
    ax.plot([10, 10], [ys[-1], ys[0]], color=LINE, lw=1.4, zorder=1)
    yb = y - 1
    T(ax, 6, yb, "然后才是怎么做：", 11, "b", CREAM, va="center")
    for j, (w, d, c) in enumerate([("狠", "对的时候", GOLD), ("拿", "条件撑着", GOLD), ("忍", "还没到时候", BLUE),
                                   ("断", "错了就走", BLUE), ("趴", "势不对", BLUE)]):
        xx = 8 + j * 17.5
        ax.add_patch(FancyBboxPatch((xx, yb - 15), 14.5, 10, boxstyle="round,pad=0,rounding_size=1.8", fc=PANEL, ec=c, lw=1.1))
        T(ax, xx + 7.25, yb - 8.6, w, 16, "s", c, ha="center", va="center")
        T(ax, xx + 7.25, yb - 13, d, 7.8, "r", MUTED, ha="center", va="center")
    save(fig, "观的步骤.png")


# ---------------------------------------------------------------- 图：消息怎么看
def news():
    fig, ax = canvas(7.2, 6.4)
    H = 100 * 6.4 / 7.2
    T(ax, 6, H - 6, "消息：先辨对不对，再问它想干什么", 15, "s", CREAM, va="center")

    def box(x, y, w, h, title, sub=None, c=LINE, tc=CREAM, size=11):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.8", fc=PANEL, ec=c, lw=1.2))
        T(ax, x + w / 2, y + h / 2 + (2 if sub else 0), title, size, "b", tc, ha="center", va="center")
        if sub:
            T(ax, x + w / 2, y + h / 2 - 3.2, sub, 8.3, "r", MUTED, ha="center", va="center", linespacing=1.35)

    def arrow(a, b, c=MUTED):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, color=c, lw=1.2))

    box(35, H - 21, 30, 8, "一条消息")
    arrow((50, H - 21), (50, H - 25))
    box(22, H - 38, 56, 12.5, "这件事对不对？", "能不能对上产量、库存、订单、公告、真金白银的成交", c=CREAM)
    arrow((35, H - 38), (24, H - 43.5), GOLD)
    arrow((65, H - 38), (76, H - 43.5), BLUE)
    T(ax, 26.5, H - 39.5, "对，是事实", 9, "b", GOLD, ha="right", va="center")
    T(ax, 73.5, H - 39.5, "对不上，只是话", 9, "b", BLUE, ha="left", va="center")
    box(5, H - 61, 40, 17, "归到条件里去观", "动机是次要的：订单是真的，\n订单就还是订单", c=GOLD, tc=GOLD)
    box(55, H - 61, 40, 17, "这时候才问动机", "谁放的？什么时候放的？\n想让你买、卖，还是别动？", c=BLUE, tc=BLUE)
    arrow((25, H - 61), (42, H - 66.5))
    arrow((75, H - 61), (58, H - 66.5))
    box(22, H - 79, 56, 12, "都要看价格对它的反应", "想让你买却不涨：兑现；想让你卖却不跌：绝望", c=CREAM)
    T(ax, 50, 4, "消息是话，反应是钱。", 13, "s", GOLD, ha="center", va="center")
    save(fig, "消息怎么看.png")


# ---------------------------------------------------------------- 图：条件和时机怎么配
def quadrant():
    fig, ax = canvas(7.2, 5.6)
    H = 100 * 5.6 / 7.2
    x0, y0, W, Hh = 16, 10, 78, 56
    cells = [  # (列, 行, 大字, 小字, 颜色, 透明度)
        (1, 1, "狠", "条件撑着，时机也顺：\n主仓上，拿住", GOLD, 1.0),
        (0, 1, "忍", "条件撑着，时机还逆：\n小钱先站位置，等", GOLD, 0.45),
        (1, 0, "不追", "条件不撑，时机还顺：\n热是虚的，有的减", BLUE, 0.45),
        (0, 0, "趴", "条件不撑，时机也逆：\n像乌龟一样趴着，有货的断舍离", BLUE, 1.0)]
    for cx, cy, big, small, c, a in cells:
        x, y = x0 + cx * W / 2, y0 + cy * Hh / 2
        ax.add_patch(FancyBboxPatch((x + 0.8, y + 0.8), W / 2 - 1.6, Hh / 2 - 1.6, boxstyle="round,pad=0,rounding_size=2",
                                    fc=PANEL, ec=c, lw=1.6 if a == 1 else 1.0, alpha=1))
        T(ax, x + 5, y + Hh / 2 - 9, big, 26 if len(big) == 1 else 20, "s", c, va="center", alpha=1 if a == 1 else 0.8)
        T(ax, x + 5, y + 7.5, small, 8.8, "r", TXT, va="center", linespacing=1.45)
    T(ax, x0 + W / 4, y0 - 4, "时机逆：钱在走，趋势向下", 9, "r", BLUE, ha="center", va="center")
    T(ax, x0 + 3 * W / 4, y0 - 4, "时机顺：钱在进，趋势向上", 9, "r", GOLD, ha="center", va="center")
    T(ax, x0 - 3, y0 + 3 * Hh / 4, "条件\n撑着", 10, "b", GOLD, ha="right", va="center")
    T(ax, x0 - 3, y0 + Hh / 4, "条件\n不撑", 10, "b", BLUE, ha="right", va="center")
    T(ax, 6, H - 6, "条件和时机怎么配", 15, "s", CREAM, va="center")
    T(ax, 94, H - 6, "两样冲突，以条件为准", 9.5, "r", MUTED, va="center", ha="right")
    save(fig, "条件和时机.png")


# ---------------------------------------------------------------- 图：仓位的火候
def heat():
    fig, ax = canvas(7.2, 4.6)
    H = 100 * 4.6 / 7.2
    pos = [1 / 3, 2 / 3, 1, 1, 1, 0.5, 0.5, 0.5, 0, 0, 0, 0]
    word = ["试", "加", "狠", "拿", "不加", "减", "忍", "断", "趴", "趴", "趴", "等"]
    x0, bw, base, top = 10, 7.0, 12, 34
    for lv, lab in [(0, "空仓"), (1 / 3, "1/3"), (2 / 3, "2/3"), (1, "满")]:
        y = base + lv * top
        ax.plot([x0 - 1, x0 + 12 * bw], [y, y], color=LINE, lw=0.6, zorder=1)
        T(ax, x0 - 2, y, lab, 8, "r", MUTED, ha="right", va="center")
    for k in range(12):
        x = x0 + k * bw + 0.6
        h = pos[k] * top
        c = col(k)
        if k in (6, 7):     # 幻想、侥幸：拿着剩下的，跌破认错线就清零
            ax.add_patch(Rectangle((x, base), bw - 1.2, h, fc="none", ec=c, lw=1.2, hatch="////", zorder=3))
        elif h > 0:
            ax.add_patch(FancyBboxPatch((x, base), bw - 1.2, h, boxstyle="round,pad=0,rounding_size=0.6", fc=c, ec="none",
                                        alpha=0.95, zorder=3))
        T(ax, x + (bw - 1.2) / 2, base + h + 2.2, word[k], 11 if len(word[k]) == 1 else 9, "s", c, ha="center", va="bottom")
        T(ax, x + (bw - 1.2) / 2, base - 3, STAGES[k] if k != 3 else "大众\n共识", 7.8, "b", c, ha="center", va="top",
          linespacing=0.95)
    T(ax, 6, H - 6, "仓位的火候：一段一段加，一段一段退", 15, "s", CREAM, va="center")
    T(ax, x0 + 7.6 * bw, base + 0.5 * top + 9, "斜线：拿着剩下的，\n跌破认错线就清零", 8, "r", MUTED, ha="center", va="bottom",
      linespacing=1.3)
    save(fig, "仓位火候.png")


if __name__ == "__main__":
    cover(); path_list(); sun_temp(); forces_grid(); wheel(); circles(); step_zero(); steps(); news(); quadrant(); heat()
