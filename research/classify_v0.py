"""冬至理论 v0 自动标注 + 事先检验。

只用当月及以前的数据给每个月标一个阶段（1–12），再看各阶段之后 6、12 个月的涨跌和最大回撤。
两种标法：
  A 规则版：照论文第七节的步骤（先用价格分区，再用速度、成交定到哪一段，资金确认，拿不准往保守靠）。
  B 结构版：用六层冷热，找最近的合法状态（johnson_test.py）。
"""
from pathlib import Path

import numpy as np
import pandas as pd

from johnson_test import CAUTION, assign, load_layers

OUT = Path(__file__).parent / "output"
NAMES = {1: "绝望", 2: "怀疑", 3: "犹豫", 4: "大众入场", 5: "泡沫", 6: "兑现",
         7: "幻想", 8: "侥幸", 9: "瓦解", 10: "麻木", 11: "恐慌", 12: "衰竭"}


def features():
    df = pd.read_csv(OUT / "monthly.csv", index_col=0)
    df.index = pd.PeriodIndex(df.index, freq="M")
    p = df["mkt_idx"]
    f = pd.DataFrame(index=df.index)
    f["p"] = p
    hi36, lo36 = p.rolling(36, min_periods=24).max(), p.rolling(36, min_periods=24).min()
    f["pos"] = (p - lo36) / (hi36 - lo36)            # 在三年区间里的位置，0=最低 1=最高
    f["above_ma12"] = p > p.rolling(12).mean()       # 价格在一年均线上方
    f["r3"] = p / p.shift(3) - 1                     # 三个月涨跌，衡量陡还是缓
    lo_now, lo_prev = p.rolling(6).min(), p.shift(6).rolling(6).min()
    hi_now, hi_prev = p.rolling(6).max(), p.shift(6).rolling(6).max()
    f["higher_low"] = lo_now > lo_prev               # 低点一个比一个高
    f["lower_low"] = lo_now < lo_prev
    f["lower_high"] = hi_now < hi_prev
    tr = (df["turnover"] / df["mktcap"]).rolling(3).mean()
    f["vol_pct"] = tr.rolling(36, min_periods=24).rank(pct=True)   # 换手率在三年里的分位
    mr = df["margin"] / df["mktcap"]
    f["margin_up"] = mr.rolling(3).mean() > mr.shift(3).rolling(3).mean()
    # 前瞻收益（只用来检验，不进标注）
    f["fwd6"] = p.shift(-6) / p - 1
    f["fwd12"] = p.shift(-12) / p - 1
    fut_min = pd.concat([p.shift(-k) for k in range(1, 13)], axis=1).min(axis=1)
    f["fwd12_mdd"] = fut_min / p - 1                 # 未来一年里最深跌到哪
    return f


def rule_stage(r, prev):
    """论文第七节 1–5 步的一个可执行版本。prev 是上个月的阶段，用来区分 1 和 12、6 和 7。"""
    pos, r3, v = r.pos, r.r3, r.vol_pct
    if np.isnan(pos):
        return np.nan
    up = r.above_ma12 or (r.higher_low and r3 > 0)
    if up:
        if pos < 0.3:
            s = 1 if (prev in (10, 11, 12, 1) or np.isnan(prev)) else 2
        elif pos < 0.55:
            s = 2 if not r.higher_low else 3
        elif pos < 0.8:
            s = 3
        else:  # 高位
            if r3 > 0.15 and v > 0.8:
                s = 5                       # 接近直线、天量
            elif r3 <= 0.02 and v > 0.6:
                s = 6                       # 放量不涨
            else:
                s = 4
        # 第5步：拿不准犹豫还是大众入场，当大众入场看
        if s == 3 and v > 0.7:
            s = 4
    else:
        if pos > 0.7:
            s = 7                           # 刚从高处下来，反弹过不了前高
        elif pos > 0.45:
            s = 8 if r.lower_low else 7
        elif pos > 0.25:
            s = 9
        else:
            if r3 < -0.12:
                s = 11                      # 加速下跌
            elif v < 0.25 and r3 > -0.03:
                s = 12                      # 地量、跌不动
            else:
                s = 10
        # 第5步：分不清麻木还是恐慌，当麻木看
        if s == 11 and v < 0.5:
            s = 10
        # 资金还在加的“衰竭”不可信，退回麻木
        if s == 12 and r.margin_up:
            s = 10
    return s


def label_rules(f):
    out, prev = [], np.nan
    for _, r in f.iterrows():
        s = rule_stage(r, prev)
        out.append(s)
        prev = s
    return pd.Series(out, index=f.index, name="A")


def summarize(f, col):
    g = f.dropna(subset=[col]).groupby(col)
    t = pd.DataFrame({
        "月数": g.size(),
        "之后6个月平均涨跌": g["fwd6"].mean(),
        "之后12个月平均涨跌": g["fwd12"].mean(),
        "之后12个月上涨的比例": g["fwd12"].apply(lambda x: (x.dropna() > 0).mean()),
        "之后12个月平均最深跌幅": g["fwd12_mdd"].mean(),
    })
    t.index = [f"{int(i):2d} {NAMES[int(i)]}" for i in t.index]
    return t


def theory_rank_corr(f, col):
    """理论隐含的后市从好到坏：1,12,2,11,3,10,4,9,5,8,6,7。看实际的 12 个月涨跌是不是这个顺序。"""
    expected = {s: i for i, s in enumerate(CAUTION[::-1])}   # 0 = 理论上最好
    g = f.dropna(subset=[col, "fwd12"]).groupby(col)["fwd12"].mean()
    e = pd.Series({s: expected[int(s)] for s in g.index})
    return -g.rank().corr(e.rank())   # 正 = 和理论一致


def perm_p(f, col, n=2000, block=12, seed=7):
    """把阶段标签按 12 个月一块整块错位，算“和理论一致”的程度在随机下有多常见。"""
    rng = np.random.default_rng(seed)
    obs = theory_rank_corr(f, col)
    lab = f[col].values
    T = len(lab)
    cnt = 0
    for _ in range(n):
        k = rng.integers(block, T - block)
        g = f.copy()
        g[col] = np.roll(lab, k)
        if theory_rank_corr(g, col) >= obs:
            cnt += 1
    return obs, cnt / n


# 论文第八节的手工划分，按月展开（同一个月跨两段的，取月末所在的那段）
PAPER = {"2014-07": 1, "2014-08": 2, "2014-09": 2, "2014-10": 3, "2014-11": 3, "2014-12": 4,
         "2015-01": 4, "2015-02": 4, "2015-03": 5, "2015-04": 5, "2015-05": 6, "2015-06": 7,
         "2015-07": 8, "2015-08": 9, "2015-09": 10, "2015-10": 10, "2015-11": 10, "2015-12": 10,
         "2016-01": 12}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    f = features()
    f["A"] = label_rules(f)
    H = load_layers(24)
    order = ("太阳·M1-M2", "价格", "利润·PPI", "谁在卖", "资金·融资", "人气·换手")
    B = assign(H, order)
    f["B"] = B["stage"]
    f["B_dist"] = B["dist"]
    f = f[f.index >= pd.Period("2010-01", "M")]
    f.to_csv(OUT / "stages_v0.csv", encoding="utf-8-sig")
    for col, title in [("A", "A 规则版"), ("B", "B 结构版（论文图2顺序，24个月窗口）")]:
        print(f"\n===== {title} =====")
        print(summarize(f, col).round(3).to_string())
        obs, p = perm_p(f, col)
        print(f"阶段排序和理论一致的程度（秩相关）{obs:+.2f}，随机错位下达到这个程度的概率 p={p:.3f}")
    # 粗分四区：底部(12,1) 上升(2-5) 顶部(6,7) 下降(8-11)
    zone = {12: "底部", 1: "底部", 2: "上升", 3: "上升", 4: "上升", 5: "上升",
            6: "顶部", 7: "顶部", 8: "下降", 9: "下降", 10: "下降", 11: "下降"}
    f["zone"] = f["A"].map(zone)
    z = f.dropna(subset=["zone"]).groupby("zone")[["fwd6", "fwd12", "fwd12_mdd"]].agg(["mean", "count"])
    print("\n===== A 规则版，四区 =====")
    print(z.round(3).to_string())
    print("\n===== 2014-06 至 2016-06 的自动标注（对照论文第八节） =====")
    seg = f.loc["2014-06":"2016-06", ["p", "pos", "r3", "vol_pct", "A", "B"]].copy()
    seg["A名"] = seg["A"].map(lambda x: NAMES.get(int(x), "") if pd.notna(x) else "")
    seg["B名"] = seg["B"].map(lambda x: NAMES.get(int(x), "") if pd.notna(x) else "")
    seg["论文"] = [NAMES.get(PAPER.get(str(i), 0), "") for i in seg.index]
    print(seg.round(2).to_string())
    seg.to_csv(OUT / "label_2014_2016.csv", encoding="utf-8-sig")
    hit = [(PAPER[str(i)] == seg.loc[i, "A"]) for i in seg.index if str(i) in PAPER]
    near = [abs(((PAPER[str(i)] - seg.loc[i, "A"]) + 6) % 12 - 6) <= 1 for i in seg.index if str(i) in PAPER]
    print(f"A 规则版和论文完全一致 {sum(hit)}/{len(hit)} 个月，相差不超过一段 {sum(near)}/{len(near)} 个月")
