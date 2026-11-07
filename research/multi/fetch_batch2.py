"""第二批标的（笔记六），存到 research/data/multi2/。"""
from pathlib import Path

import pandas as pd

from fetch_multi import tx_daily

OUT = Path(__file__).resolve().parent.parent / "data" / "multi2"
OUT.mkdir(parents=True, exist_ok=True)

TX = {
    "sz000876": ("新希望", "养殖饲料股", "hfq"), "sz002124": ("天邦食品", "养殖饲料股", "hfq"),
    "sz002567": ("唐人神", "养殖饲料股", "hfq"), "sz002311": ("海大集团", "养殖饲料股", "hfq"),
    "sz300059": ("东方财富", "券商股", "hfq"), "sh601688": ("华泰证券", "券商股", "hfq"),
    "sh600036": ("招商银行", "其他股票", "hfq"), "sz000858": ("五粮液", "其他股票", "hfq"),
    "sh601088": ("中国神华", "其他股票", "hfq"), "sh601899": ("紫金矿业", "其他股票", "hfq"),
    "sh600585": ("海螺水泥", "其他股票", "hfq"),
    "sz399001": ("深证成指", "指数", ""), "sz399006": ("创业板指", "指数", ""),
}
SINA = {
    "C0": ("玉米", "农产品期货"), "SR0": ("白糖", "农产品期货"), "CF0": ("棉花", "农产品期货"),
    "JD0": ("鸡蛋", "农产品期货"), "Y0": ("豆油", "农产品期货"), "P0": ("棕榈油", "农产品期货"),
    "JM0": ("焦煤", "工业品期货"), "I0": ("铁矿石", "工业品期货"), "ZN0": ("沪锌", "工业品期货"),
    "RU0": ("橡胶", "工业品期货"), "AU0": ("黄金", "工业品期货"),
}

if __name__ == "__main__":
    import akshare as ak
    meta = []
    for code, (name, kind, adj) in TX.items():
        try:
            df = tx_daily(code, adj)
            df.to_csv(OUT / f"{code}.csv", index=False)
            meta.append((code, name, kind, df["date"].iloc[0], df["date"].iloc[-1], len(df)))
            print(code, name, len(df), df["date"].iloc[0], df["date"].iloc[-1], flush=True)
        except Exception as e:
            print(code, name, "下载失败", repr(e)[:120], flush=True)
    for code, (name, kind) in SINA.items():
        try:
            df = ak.futures_zh_daily_sina(symbol=code)[["date", "open", "close", "high", "low", "volume"]]
            df["date"] = df["date"].astype(str)
            df.to_csv(OUT / f"{code}.csv", index=False)
            meta.append((code, name, kind, df["date"].iloc[0], df["date"].iloc[-1], len(df)))
            print(code, name, len(df), df["date"].iloc[0], df["date"].iloc[-1], flush=True)
        except Exception as e:
            print(code, name, "下载失败", repr(e)[:120], flush=True)
    pd.DataFrame(meta, columns=["代码", "名称", "类别", "起", "止", "天数"]).to_csv(OUT / "_meta.csv", index=False, encoding="utf-8-sig")
