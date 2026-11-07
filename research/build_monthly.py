"""把 data/ 下的原始数据整理成一张月度表 output/monthly.csv。

每一行是一个月，列按冬至理论的六样东西归类：
  价格：hs300 月末收盘
  成交量：turnover 沪深两市月成交额（亿元）
  资金：margin 月末融资余额（亿元）、margin_ratio 融资余额/流通市值（%）
  人气：new_inv 新增投资者（万，2015-04 至 2023-08）
  谁在卖：net_reduce 重要股东净减持（亿元，正数=净减持）、seo 增发募资、ipo 首发募资（亿元）
  太阳候选：ppi_yoy、m1_yoy、m2_yoy、m1_m2 剪刀差、pmi
"""
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)


def month(s):
    return pd.to_datetime(s).dt.to_period("M")


def load():
    m = pd.read_csv(D / "margin_daily.csv")
    m["date"] = pd.to_datetime(m["DIM_DATE"])
    m["ym"] = m["date"].dt.to_period("M")
    g = m.groupby("ym").last()
    df = pd.DataFrame({
        "hs300": g["NEW"],
        "margin": g["RZYE"] / 1e8,
        "margin_ratio": g["RZYEZB"],
    })
    # 月内最高最低（日收盘），用来判断创新高/新低
    df["hs300_hi"] = m.groupby("ym")["NEW"].max()
    df["hs300_lo"] = m.groupby("ym")["NEW"].min()

    mm = pd.read_csv(D / "market_monthly.csv")
    mm["ym"] = month(mm["REPORT_DATE"])
    mm = mm.set_index("ym")
    df = df.join((mm["DEAL_AMOUNT_SH"] + mm["DEAL_AMOUNT_SZ"]).rename("turnover"), how="outer")
    df = df.join((mm["TOTAL_MARKE_SH"] + mm["TOTAL_MARKE_SZ"]).rename("mktcap"), how="left")

    na = pd.read_csv(D / "new_accounts.csv")
    na["ym"] = pd.PeriodIndex(na["STATISTICS_DATE"], freq="M")
    df = df.join(na.set_index("ym")["ADD_INVESTOR"].rename("new_inv"), how="left")

    ppi = pd.read_csv(D / "ppi.csv"); ppi["ym"] = month(ppi["REPORT_DATE"])
    df = df.join(ppi.set_index("ym")["BASE_SAME"].rename("ppi_yoy"), how="outer")
    ms = pd.read_csv(D / "money_supply.csv"); ms["ym"] = month(ms["REPORT_DATE"])
    ms = ms.set_index("ym")
    df = df.join(ms["CURRENCY_SAME"].rename("m1_yoy"), how="left")
    df = df.join(ms["BASIC_CURRENCY_SAME"].rename("m2_yoy"), how="left")
    df["m1_m2"] = df["m1_yoy"] - df["m2_yoy"]
    pmi = pd.read_csv(D / "pmi.csv"); pmi["ym"] = month(pmi["REPORT_DATE"])
    df = df.join(pmi.set_index("ym")["MAKE_INDEX"].rename("pmi"), how="left")

    seo = pd.read_csv(D / "seo.csv")
    seo["ym"] = month(seo["ISSUE_LISTING_DATE"])
    # 吸收合并是换股，不是募资；单笔 ≥1000 亿的是国家注资银行（2018 农行、2025 四大行），都不算“往外卖”
    seo = seo[(seo["ISSUE_WAY"] != "吸收合并") & (seo["TOTAL_RAISE_FUNDS"] < 1000e8)]
    df = df.join((seo.groupby("ym")["TOTAL_RAISE_FUNDS"].sum() / 1e8).rename("seo"), how="left")

    ipo = pd.read_csv(D / "ipo.csv")
    ipo = ipo[ipo["LISTING_DATE"].notna()].copy()
    ipo["ym"] = month(ipo["LISTING_DATE"])
    # TOTAL_RAISE_FUNDS 单位亿元；缺的用 发行价 × 发行量（万股）/ 1e4 补
    ipo["raise"] = ipo["TOTAL_RAISE_FUNDS"].fillna(ipo["ISSUE_PRICE"] * ipo["ISSUE_NUM"] / 1e4)
    df = df.join(ipo.groupby("ym")["raise"].sum().rename("ipo"), how="left")
    df = df.join(ipo.groupby("ym").size().rename("ipo_n"), how="left")

    hc_path = D / "holder_change.csv"
    if hc_path.exists():
        hc = pd.read_csv(hc_path)
        hc["ym"] = month(hc["END_DATE"].fillna(hc["NOTICE_DATE"]))
        px = hc["TRADE_AVERAGE_PRICE"].fillna(hc["CLOSE_PRICE"])
        # CHANGE_NUM_SYMBOL 单位万股，减持为负；金额 = 万股 × 元 = 万元
        hc["amt"] = hc["CHANGE_NUM_SYMBOL"] * px / 1e4  # 亿元
        g = hc.groupby("ym")["amt"]
        df = df.join((-g.sum()).rename("net_reduce"), how="left")
        df = df.join((-hc[hc["amt"] < 0].groupby("ym")["amt"].sum()).rename("gross_reduce"), how="left")
        # 这张表 2019 年以前收录很不全（2015 全年只有约 257 亿净减持，公开报道仅上半年就有 4771 亿），
        # 所以只用 2019 年以后的
        early = df.index < pd.Period("2019-01", "M")
        df.loc[early, ["net_reduce", "gross_reduce"]] = np.nan

    df.index.name = "ym"
    df = df.sort_index()
    df["seo"] = df["seo"].fillna(0)
    df["ipo"] = df["ipo"].fillna(0)
    # 全市场指数：用两市总市值的月度变化，扣掉当月新股和增发带来的市值，近似一个全市场市值加权指数
    r = (df["mktcap"] - df["ipo"] - df["seo"]) / df["mktcap"].shift(1)
    df["mkt_idx"] = 1000 * r.fillna(1).cumprod()
    df.loc[df["mktcap"].isna(), "mkt_idx"] = np.nan
    df = df[(df.index >= pd.Period("2008-01", "M")) & (df.index <= pd.Period("2026-10", "M"))]
    # 2008-01 以前没有总市值，指数从 2008-01=1000 起算
    df["mkt_idx"] = 1000 * df["mkt_idx"] / df["mkt_idx"].iloc[0]
    for c in ["seo", "ipo", "ipo_n"]:
        df[c] = df[c].fillna(0)
    return df


if __name__ == "__main__":
    df = load()
    df.to_csv(OUT / "monthly.csv", encoding="utf-8-sig")
    print(df.loc["2014-06":"2016-03"].round(1).to_string())
