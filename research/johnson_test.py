"""检验冬至理论的核心结构：六层是不是按固定顺序一层一层地翻。

如果六层真按顺序翻，每个月的“六层冷热”组合应该大多落在 12 个合法状态上
（第 1–6 段：前 k 层热、其余冷；第 7–12 段：前 k 层冷、其余热）。
六层要是各翻各的，64 种组合随便出，落在 12 个合法状态上的比例大约只有 12/64≈19%。

热/冷 的统一定义（v0）：序列的 3 个月平均 高于 它过去 12 个月的平均 → 热。
不用未来数据。
"""
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "output"
rng = np.random.default_rng(20261107)


def load_layers(window=12):
    df = pd.read_csv(OUT / "monthly.csv", index_col=0)
    df.index = pd.PeriodIndex(df.index, freq="M")
    # 股东减持数据 2019 年前不全，这里只用新股+增发，保证整段口径一致
    supply = df["ipo"] + df["seo"]
    raw = {
        "太阳·M1-M2": df["m1_m2"],
        "价格": np.log(df["mkt_idx"]),
        "利润·PPI": df["ppi_yoy"],
        "谁在卖": supply / df["mktcap"],
        "资金·融资": df["margin"] / df["mktcap"],
        "人气·换手": df["turnover"] / df["mktcap"],
    }
    hot = {}
    for k, s in raw.items():
        s3 = s.rolling(3, min_periods=3).mean()
        base = s.shift(1).rolling(window, min_periods=window).mean()
        hot[k] = (s3 > base).where(s3.notna() & base.notna())
    H = pd.DataFrame(hot).dropna().astype(int)
    return H


def johnson_states(n=6):
    """返回 {stage: bit tuple}，stage 1..2n。"""
    st = {}
    for k in range(1, n + 1):
        st[k] = tuple([1] * k + [0] * (n - k))
        st[k + n] = tuple([0] * k + [1] * (n - k))
    return st


# 拿不准时选“让你少买、早走”的那个（论文第七节第5步）：按理论隐含的后市好坏从差到好排
CAUTION = [7, 6, 8, 5, 9, 4, 10, 3, 11, 2, 12, 1]


def assign(H, order):
    st = johnson_states(len(order))
    X = H[list(order)].values
    stages, dist = [], []
    for row in X:
        d = {s: int(np.sum(np.array(b) != row)) for s, b in st.items()}
        m = min(d.values())
        cands = [s for s in CAUTION if d[s] == m]
        stages.append(cands[0])
        dist.append(m)
    return pd.DataFrame({"stage": stages, "dist": dist}, index=H.index)


def valid_share(H, order):
    valid = set(johnson_states(len(order)).values())
    X = H[list(order)].values
    return np.mean([tuple(r) in valid for r in X])


def null_share(H, order, n=2000):
    """每一层各自做随机循环平移，保留每层自己的节奏，打乱层与层之间的先后关系。"""
    X = H[list(order)].values
    T = len(X)
    valid = set(johnson_states(len(order)).values())
    out = []
    for _ in range(n):
        Y = np.column_stack([np.roll(X[:, j], rng.integers(T)) for j in range(X.shape[1])])
        out.append(np.mean([tuple(r) in valid for r in Y]))
    return np.array(out)


ORDERS = {
    "论文图2：供需→价格→利润→扩产→资金→人气":
        ("太阳·M1-M2", "价格", "利润·PPI", "谁在卖", "资金·融资", "人气·换手"),
    "按论文第六节的描述：供需→价格→利润→人气→资金→扩产":
        ("太阳·M1-M2", "价格", "利润·PPI", "人气·换手", "资金·融资", "谁在卖"),
}

if __name__ == "__main__":
    import sys
    window = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    H = load_layers(window)
    print(f"样本：{H.index[0]} 至 {H.index[-1]}，共 {len(H)} 个月；热/冷窗口 {window} 个月")
    print("各层热的月份占比：", H.mean().round(2).to_dict())
    rows = []
    for name, order in ORDERS.items():
        v = valid_share(H, order)
        nul = null_share(H, order)
        rows.append((name, v, nul.mean(), (nul >= v).mean()))
    allv = []
    for order in permutations(H.columns):
        if order[0] > order[-1]:  # 正反两个方向的合法状态集合相同，只算一个
            continue
        allv.append((valid_share(H, order), order))
    allv.sort(reverse=True)
    for name, v, nm, p in rows:
        rank = 1 + sum(1 for x, _ in allv if x > v + 1e-12)
        print(f"{name}\n   落在合法状态的月份 {v:.1%}；打乱后平均 {nm:.1%}；p={p:.3f}；在 {len(allv)} 种顺序里排第 {rank}")
    print("最贴合的 5 种顺序（不分正反）：")
    for v, o in allv[:5]:
        print(f"   {v:.1%}  " + " → ".join(o))
    pd.DataFrame([(v, " → ".join(o)) for v, o in allv], columns=["valid_share", "order"]).to_csv(
        OUT / f"johnson_orders_w{window}.csv", index=False, encoding="utf-8-sig")
    H.to_csv(OUT / f"layers_hot_w{window}.csv", encoding="utf-8-sig")
