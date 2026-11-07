# 冬至理论研究

用十二个阶段看清行情走到了哪里。作者：justintang。

## 目录

- `paper/冬至理论.md`：论文原稿（2026-10-16 版）
- `notes/`：研究笔记
  - `01-股票市场的六层顺序.md`：用 2010–2026 年 A 股数据检验图2的六层顺序
  - `02-六样东西怎么量化（草案）.md`：六样东西的量化选项、v0 自动标注和第一次事先检验
  - `手工标注模板_2016-2024.csv`：请作者按月手工标阶段，用来定规则和检验
- `research/`：数据和代码
  - `fetch_data.py`：从东方财富数据中心下载原始数据到 `research/data/`
  - `build_monthly.py`：整理成月度表 `research/output/monthly.csv`
  - `layer_order.py`、`lead_lag.py`：各层在顶部、底部谁先谁后
  - `johnson_test.py`、`johnson_maxnull.py`：六层是不是按固定顺序一层一层地翻
  - `classify_v0.py`：v0 自动标注，算各阶段之后的涨跌

## 运行

需要 Python 3、pandas、numpy、matplotlib。

```bash
cd research
python3 fetch_data.py
python3 build_monthly.py
python3 layer_order.py
python3 lead_lag.py
python3 johnson_test.py 24
python3 classify_v0.py
```
