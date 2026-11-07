"""把排版源文件转成 Markdown，方便在 GitHub 上直接读。"""
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "冬至理论_v3.src.txt").read_text(encoding="utf-8").splitlines()
out = ["# 冬至理论（第三版）", "", "一个关于市场冷热循环的十二阶段模型", "", "洛辰justin　二〇二六年十一月", ""]
mode, buf = None, []
for line in src:
    line = line.rstrip()
    if mode:
        if line == "@end":
            if mode == "box":
                out += ["> " + t for t in buf] + [""]
            elif mode == "scene":
                out += ["> **交易场景**", ">"] + ["> " + t for t in buf] + [""]
            elif mode == "quote":
                out += ["> **" + t + "**  " for t in buf] + [""]
            elif mode == "table":
                rows = [r.split("|") for r in buf]
                out += ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * len(rows[0])]
                out += ["| " + " | ".join(r) + " |" for r in rows[1:]] + [""]
            mode, buf = None, []
        elif line:
            buf.append(line)
        continue
    if not line or line == "@titlepage":
        continue
    if line in ("@box", "@scene", "@quote", "@table"):
        mode = line[1:]
    elif line.startswith("@keywords "):
        out += ["**关键词**　" + line[10:], ""]
    elif line.startswith("# "):
        out += ["## " + line[2:], ""]
    elif line.startswith("## "):
        out += ["### " + line[3:], ""]
    elif line.startswith("@fig "):
        num, f, title, note = (line[5:].split("|") + [""])[:4]
        out += [f"![{num} {title}]({f})", "", f"**{num}**　{title}" + (f"。{note}" if note else ""), ""]
    elif line.startswith("@stage "):
        num, name, sub, _ = line[7:].split("|")
        out += [f"#### 阶段{num}　{name}　{sub}", ""]
    elif line.startswith("@people "):
        out += ["◆ " + line[8:], ""]
    elif line.startswith("@key "):
        t = line[5:]; i = t.index("？") + 1
        out += [f"**{t[:i]}**{t[i:]}", ""]
    elif line.startswith("@caption "):
        out += ["**" + line[9:] + "**", ""]
    elif line.startswith("@note ") or line.startswith("@center "):
        out += [line.split(" ", 1)[1], ""]
    else:
        out += [line, ""]
(HERE.parent / "冬至理论_v3.md").write_text("\n".join(out), encoding="utf-8")
print("ok")
