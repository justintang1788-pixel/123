"""第三批标的（笔记十一），存到 research/data/multi3/。名单和留去规矩见 notes/11。"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from fetch_multi import tx_daily

OUT = Path(__file__).resolve().parent.parent / "data" / "multi3"
OUT.mkdir(parents=True, exist_ok=True)

FUT = {
    "AL0": "沪铝", "PB0": "沪铅", "NI0": "沪镍", "SN0": "沪锡", "AG0": "白银", "HC0": "热卷", "SS0": "不锈钢",
    "FU0": "燃料油", "BU0": "沥青", "SP0": "纸浆", "WR0": "线材", "SC0": "原油", "LU0": "低硫燃料油",
    "BC0": "国际铜", "NR0": "20号胶",
    "A0": "豆一", "B0": "豆二", "CS0": "玉米淀粉", "L0": "塑料", "V0": "PVC", "PP0": "聚丙烯", "J0": "焦炭",
    "EG0": "乙二醇", "EB0": "苯乙烯", "PG0": "液化气", "RR0": "粳米", "FB0": "纤维板", "BB0": "胶合板",
    "CY0": "棉纱", "TA0": "PTA", "MA0": "甲醇", "FG0": "玻璃", "RM0": "菜粕", "OI0": "菜油", "SF0": "硅铁",
    "SM0": "锰硅", "AP0": "苹果", "CJ0": "红枣", "UR0": "尿素", "SA0": "纯碱", "PF0": "短纤", "PK0": "花生",
    "WH0": "强麦", "PM0": "普麦", "RI0": "早籼稻", "JR0": "粳稻", "LR0": "晚籼稻", "RS0": "菜籽", "ZC0": "动力煤",
    "T0": "十年国债", "TF0": "五年国债", "TS0": "二年国债",
}
BOND = {"T0", "TF0", "TS0"}
IDX = {
    "sh000016": "上证50", "sh000300": "沪深300", "sh000905": "中证500", "sh000852": "中证1000",
    "sh000922": "中证红利", "sz399005": "中小板指",
    "sh000986": "全指能源", "sh000987": "全指材料", "sh000988": "全指工业", "sh000989": "全指可选消费",
    "sh000990": "全指主要消费", "sh000991": "全指医药", "sh000992": "全指金融地产", "sh000993": "全指信息技术",
    "sh000994": "全指电信", "sh000995": "全指公用事业",
    "sz399997": "中证白酒", "sz399998": "中证煤炭", "sz399975": "证券公司", "sz399986": "中证银行",
    "sz399967": "中证军工", "sz399989": "中证医疗", "sz399971": "中证传媒", "sz399808": "中证新能",
    "sz399395": "国证有色", "sz399393": "国证地产",
}
FOREIGN = {"hkHSI": "恒生指数", "hkHSCEI": "恒生国企指数", "usINX": "标普500", "usIXIC": "纳斯达克", "usDJI": "道琼斯"}
STOCK = {
    "sh601318": "中国平安", "sh601166": "兴业银行", "sh601398": "工商银行", "sh600016": "民生银行", "sh601601": "中国太保",
    "sh600887": "伊利股份", "sh600809": "山西汾酒", "sz000568": "泸州老窖", "sh603288": "海天味业", "sh601888": "中国中免",
    "sz000651": "格力电器", "sz000333": "美的集团", "sh600690": "海尔智家",
    "sh600276": "恒瑞医药", "sz300760": "迈瑞医疗", "sh600436": "片仔癀", "sz000538": "云南白药", "sh600085": "同仁堂",
    "sz000423": "东阿阿胶", "sz000999": "华润三九", "sz002603": "以岭药业",
    "sh600028": "中国石化", "sh601857": "中国石油", "sh600019": "宝钢股份", "sh600362": "江西铜业", "sh601600": "中国铝业",
    "sh603993": "洛阳钼业", "sh600188": "兖矿能源", "sh601225": "陕西煤业", "sz000792": "盐湖股份", "sz002466": "天齐锂业",
    "sh600309": "万华化学", "sh601919": "中远海控",
    "sh600031": "三一重工", "sz002594": "比亚迪", "sz300750": "宁德时代", "sh601012": "隆基绿能", "sz002415": "海康威视",
    "sz002475": "立讯精密", "sz000725": "京东方A", "sz002371": "北方华创", "sh600104": "上汽集团", "sh600089": "特变电工",
    "sz000002": "万科A", "sh600048": "保利发展", "sh601668": "中国建筑", "sh601390": "中国中铁",
    "sh600598": "北大荒", "sz000998": "隆平高科",
}


def get_tx(item):
    code, name, kind, adj = item
    try:
        df = tx_daily(code, adj, 1990 if code.startswith(("sh", "sz")) else 1998)
        return code, name, kind, df, None
    except Exception as e:
        return code, name, kind, None, repr(e)[:120]


def get_fut(item):
    import akshare as ak
    code, name, kind = item
    try:
        df = ak.futures_zh_daily_sina(symbol=code)[["date", "open", "close", "high", "low", "volume"]]
        df["date"] = df["date"].astype(str)
        return code, name, kind, df, None
    except Exception as e:
        return code, name, kind, None, repr(e)[:120]


if __name__ == "__main__":
    tx_items = ([(c, n, "A股指数", "") for c, n in IDX.items()] + [(c, n, "境外指数", "") for c, n in FOREIGN.items()]
                + [(c, n, "A股个股", "hfq") for c, n in STOCK.items()])
    fut_items = [(c, n, "国债期货" if c in BOND else "商品期货") for c, n in FUT.items()]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(get_tx, tx_items)) + list(ex.map(get_fut, fut_items))
    meta, dropped = [], []
    for code, name, kind, df, err in res:
        if err or df is None or df.empty:
            dropped.append((code, name, "下载失败 " + str(err)))
            continue
        df = df.dropna(subset=["close"])
        start = df["date"].iloc[0]
        if start > "2021-12-31":
            dropped.append((code, name, f"数据从{start}才开始"))
            continue
        if kind.endswith("期货"):
            mv = df["volume"].tail(750).median()
            if not mv >= 1000:
                dropped.append((code, name, f"近三年日成交量中位数{mv:.0f}手，少于1000手"))
                continue
        df.to_csv(OUT / f"{code}.csv", index=False)
        meta.append((code, name, kind, start, df["date"].iloc[-1], len(df)))
    pd.DataFrame(meta, columns=["代码", "名称", "类别", "起", "止", "天数"]).to_csv(OUT / "_meta.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(dropped, columns=["代码", "名称", "原因"]).to_csv(OUT / "_dropped.csv", index=False, encoding="utf-8-sig")
    print("留下", len(meta), "去掉", len(dropped))
    for d in dropped:
        print("  去掉", *d)
