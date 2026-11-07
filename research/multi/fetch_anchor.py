"""笔记十四的数据：随机抽100只新股票、新期货的持仓量、全部个股的增减持、回购、解禁。存到 research/data/tf/ 和 research/data/anchor/。"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from fetch_multi import tx_daily
from fetch_three_force import OUT as TF, em_all, fut, stock

ROOT = Path(__file__).resolve().parent.parent
AN = ROOT / "data" / "anchor"
for sub in ["", "price", "insider", "buyback"]:
    (AN / sub).mkdir(parents=True, exist_ok=True)
SEED = 20261108
NEW_FUT = ["SS0", "SP0", "PF0", "NR0", "LU0", "PG0", "CY0"]


def old_codes():
    codes = []
    for sub in ["multi", "multi2", "multi3"]:
        meta = pd.read_csv(ROOT / "data" / sub / "_meta.csv")
        codes += [c[2:] for c in meta["代码"] if c.startswith(("sh6", "sz0", "sz3")) and not c.startswith("sz399")]
    return codes


def _check(args):
    code6, name = args
    sym = ("sh" if code6.startswith("6") else "sz") + code6
    try:
        chk = tx_daily(sym, "hfq", 2015, 2016)   # 先看2016年底以前有没有数据
        return code6, name, sym, len(chk) > 0, ""
    except Exception as e:
        return code6, name, sym, False, "查询出错 " + repr(e)[:60]


def _full(sym):
    d = tx_daily(sym, "hfq", 2004)   # 2004年以前的数据用不到（宏观数据从2008年才有）
    d.to_csv(AN / "price" / f"{sym}.csv", index=False)
    return sym, d["date"].iloc[0], len(d)


def pick_stocks():
    lst = em_all({"reportName": "RPTA_WEB_RZRQ_GGMX", "columns": "SCODE,SECNAME", "filter": "(DATE='2026-11-06')"})
    lst = lst.drop_duplicates("SCODE")
    lst.to_csv(AN / "_margin_list_20261106.csv", index=False, encoding="utf-8-sig")
    pool = lst[~lst["SCODE"].isin(old_codes())].sort_values("SCODE").reset_index(drop=True)
    order = np.random.RandomState(SEED).permutation(len(pool))
    cand = [(pool.loc[i, "SCODE"], pool.loc[i, "SECNAME"]) for i in order]
    picked, tried, k = [], [], 0
    while len(picked) < 100 and k < len(cand):
        batch = cand[k:k + 60]
        k += len(batch)
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(_check, batch))       # 结果按原来的顺序排
        for code6, name, sym, ok, err in res:
            if len(picked) == 100:
                break
            tried.append((code6, name, "留下" if ok else (err or "2016年底以前没有数据")))
            if ok:
                picked.append((sym, code6, name))
    with ThreadPoolExecutor(8) as ex:
        info = {sym: (st, n) for sym, st, n in ex.map(_full, [p[0] for p in picked])}
    out = [(sym, c6, nm, info[sym][0], info[sym][1]) for sym, c6, nm in picked]
    pd.DataFrame(out, columns=["代码", "代码6", "名称", "起", "天数"]).to_csv(AN / "_picked.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(tried, columns=["代码6", "名称", "结果"]).to_csv(AN / "_tried.csv", index=False, encoding="utf-8-sig")
    print("抽到", len(out), "只；一共看了", len(tried), "只", flush=True)
    return [p[1] for p in picked]


def insider(code6):
    d = em_all({"reportName": "RPT_SHARE_HOLDER_INCREASE", "columns": "NOTICE_DATE,DIRECTION,CHANGE_FREE_RATIO,CHANGE_RATE,HOLDER_NAME",
                "filter": f'(SECURITY_CODE="{code6}")', "sortColumns": "NOTICE_DATE", "sortTypes": "1"})
    if len(d):
        d["NOTICE_DATE"] = d["NOTICE_DATE"].str[:10]
        d.to_csv(AN / "insider" / f"{code6}.csv", index=False)
    b = em_all({"reportName": "RPTA_WEB_GETHGLIST_NEW", "columns": "DIM_SCODE,REPURSTARTDATE,REPURENDDATE,REPURAMOUNTLIMIT,REPURPROGRESS",
                "filter": f'(DIM_SCODE="{code6}")', "sortColumns": "REPURSTARTDATE", "sortTypes": "1"})
    if len(b):
        for c in ["REPURSTARTDATE", "REPURENDDATE"]:
            b[c] = b[c].astype(str).str[:10]
        b.to_csv(AN / "buyback" / f"{code6}.csv", index=False)
    return code6, len(d), len(b)


def lifts():
    rows = []
    for y in range(2008, 2028):
        d = em_all({"reportName": "RPT_LIFT_STAGE",
                    "columns": "SECURITY_CODE,FREE_DATE,FREE_SHARES_TYPE,ABLE_FREE_SHARES,CURRENT_FREE_SHARES,TOTAL_RATIO,FREE_RATIO",
                    "filter": f"(FREE_DATE>='{y}-01-01')(FREE_DATE<='{y}-12-31')", "sortColumns": "FREE_DATE", "sortTypes": "1"})
        if len(d):
            d["FREE_DATE"] = d["FREE_DATE"].str[:10]
            rows.append(d)
        print("解禁", y, len(d), flush=True)
    pd.concat(rows).to_csv(AN / "lifts.csv", index=False)


if __name__ == "__main__":
    new = pick_stocks()
    print("新股票", len(new), flush=True)
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(fut, NEW_FUT):
            print("期货", *r, flush=True)
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(stock, new):
            print("个股（融资、业绩、户数）", *r, flush=True)
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(insider, new + old_codes()):
            print("增减持、回购", *r, flush=True)
    lifts()
