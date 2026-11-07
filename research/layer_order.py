"""检验股票市场外三层（人气、资金、谁在卖）的先后顺序。

做法：在每一轮大顶、大底附近的窗口里，找出各个序列的最高点（顶）或最低点（底）出现在哪个月，
再和价格的高点、低点比，看谁先谁后。

流量类序列（成交额、新开户、IPO、净减持）先做居中3个月平均，避免单月噪声；
存量类序列（价格、融资余额）直接用月末值。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = Path(__file__).parent / "output"

df = pd.read_csv(OUT / "monthly.csv", index_col=0)
df.index = pd.PeriodIndex(df.index, freq="M")

c3 = lambda s: s.rolling(3, center=True, min_periods=2).mean()
S = {
    "价格·全市场": df["mkt_idx"],
    "价格·沪深300": df["hs300"],
    "成交额": c3(df["turnover"]),
    "换手率": c3(df["turnover"] / df["mktcap"]),
    "人气·新开户": c3(df["new_inv"]),
    "资金·融资余额": df["margin"],
    "谁在卖·IPO募资": c3(df["ipo"]),
}
if "net_reduce" in df:
    S["谁在卖·股东净减持"] = c3(df["net_reduce"])

# 事件窗口：(名称, 顶/底, 起, 止)
EVENTS = [
    ("2015顶", "top", "2014-07", "2016-06"),
    ("2018顶", "top", "2017-03", "2018-12"),
    ("2021顶", "top", "2020-06", "2022-06"),
    ("2026顶?", "top", "2025-06", "2026-10"),
    ("2016底", "bot", "2015-09", "2016-12"),
    ("2019底", "bot", "2018-03", "2019-08"),
    ("2024底", "bot", "2022-06", "2024-09"),
]


def turning_points():
    rows = []
    for name, kind, a, b in EVENTS:
        w = slice(pd.Period(a, "M"), pd.Period(b, "M"))
        ref = S["价格·全市场"][w]
        ref_t = ref.idxmax() if kind == "top" else ref.idxmin()
        row = {"事件": name}
        for k, s in S.items():
            x = s[w].dropna()
            if len(x) < 0.6 * len(ref):
                row[k] = ""
                continue
            t = x.idxmax() if kind == "top" else x.idxmin()
            lag = (t - ref_t).n
            # 拐点落在窗口边上，说明真正的拐点可能在窗口外，标个 *
            edge = "*" if t in (x.index[0], x.index[-1]) else ""
            row[k] = f"{t.strftime('%Y-%m')} ({lag:+d}){edge}"
        rows.append(row)
    return pd.DataFrame(rows).set_index("事件")


def daily_points():
    """价格和融资余额有日数据，拐点精确到日。"""
    m = pd.read_csv(Path(__file__).parent / "data" / "margin_daily.csv")
    m["date"] = pd.to_datetime(m["DIM_DATE"])
    m = m.set_index("date")
    rows = []
    for name, kind, a, b in EVENTS:
        w = m.loc[a:pd.Period(b, "M").end_time]
        f = (lambda x: x.idxmax()) if kind == "top" else (lambda x: x.idxmin())
        tp, tm = f(w["NEW"]), f(w["RZYE"])
        rows.append({"事件": name, "沪深300": tp.date(), "融资余额": tm.date(),
                     "相差(交易日)": int(((w.index > min(tp, tm)) & (w.index <= max(tp, tm))).sum()) * (1 if tm >= tp else -1)})
    return pd.DataFrame(rows).set_index("事件")


def event_plot():
    tops = [e for e in EVENTS if e[1] == "top"]
    fig, axes = plt.subplots(1, len(tops), figsize=(4.2 * len(tops), 3.9), sharey=True)
    keys = [k for k in S if k != "价格·沪深300"]
    keys = [k for k in keys if k != "成交额"]
    colors = dict(zip(keys, ["#222222", "#9a9a9a", "#d4a017", "#2b6cb0", "#c0392b", "#7b3fa0", "#2f855a"]))
    for ax, (name, _, a, b) in zip(axes, tops):
        w = slice(pd.Period(a, "M"), pd.Period(b, "M"))
        ref_t = S["价格·全市场"][w].idxmax()
        for k in keys:
            x = S[k][w].dropna()
            if len(x) < 6:
                continue
            rel = [(t - ref_t).n for t in x.index]
            ax.plot(rel, x / x.max(), label=k, color=colors[k],
                    lw=2.4 if k.startswith("价格") else 1.5)
        ax.axvline(0, color="#888", lw=0.8, ls="--")
        ax.set_title(f"{name}（0 = 全市场价格最高月）", fontsize=10)
        ax.set_xlabel("距价格高点的月数")
    axes[0].set_ylabel("相对窗口内最高值")
    handles, labels = {}, {}
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    fig.legend(handles.values(), handles.keys(), loc="lower center", ncol=len(handles), fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(OUT / "layer_order_tops.png", dpi=150)


if __name__ == "__main__":
    tp = turning_points()
    tp.to_csv(OUT / "layer_order.csv", encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print(tp.to_string())
    dp = daily_points()
    dp.to_csv(OUT / "layer_order_daily.csv", encoding="utf-8-sig")
    print(dp.to_string())
    event_plot()
