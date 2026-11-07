// 把 冬至理论_v3.src.txt 排成 Word 文件，版式沿用第二版（A4、宋体正文、黑体标题、红蓝两色）。
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  BorderStyle, ShadingType, WidthType, Footer, PageNumber, LevelFormat, HeadingLevel, PageBreak,
} = require("docx");

const HERE = __dirname;
const PAPER = path.resolve(HERE, "..");
const SRC = fs.readFileSync(path.join(HERE, "冬至理论_v3.src.txt"), "utf8").split(/\r?\n/);

const C = { ink: "2B2B2B", red: "A3432F", blue: "2E4A72", gold: "B08D57", gray: "7A7A7A",
  warmBg: "FBF1E8", coolBg: "EEF2F8", boxBg: "F7F2E8", head: "EEF2F8", line: "C9CED6" };
const BODY = { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "宋体" };
const HEI = { ascii: "Arial", hAnsi: "Arial", eastAsia: "黑体" };
const W = 8732; // 正文宽度（twips）

function runs(text, opt = {}) {
  // **加粗** → 加粗并上蓝色（场景框里只加粗）
  const out = [];
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const p of parts) {
    if (!p) continue;
    const bold = p.startsWith("**") && p.endsWith("**");
    const t = bold ? p.slice(2, -2) : p;
    out.push(new TextRun({ text: t, font: opt.font || BODY, size: opt.size || 23,
      bold: bold || opt.bold, color: bold && !opt.plainBold ? (opt.boldColor || C.blue) : (opt.color || C.ink) }));
  }
  return out;
}

function body(text, extra = {}) {
  return new Paragraph({ children: runs(text, extra), indent: { firstLine: extra.noIndent ? 0 : 460 },
    spacing: { line: 380, after: 100 }, alignment: AlignmentType.JUSTIFIED, ...(extra.para || {}) });
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

function figure(num, file, title, note) {
  const f = path.resolve(PAPER, file);
  const { w, h, data } = pngSize(f);
  const wide = w / h > 1.25;
  const width = wide ? 560 : 380;
  const out = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data, transformation: { width, height: Math.round(width * h / w) } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, keepNext: !!note, children: [
      new TextRun({ text: num + "　", font: HEI, size: 20, bold: true, color: C.blue }),
      new TextRun({ text: title, font: HEI, size: 20, color: C.ink })] }),
  ];
  if (note) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, indent: { left: 600, right: 600 },
    children: [new TextRun({ text: note, font: BODY, size: 18, color: C.gray })] }));
  return out;
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 420, after: 220 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.gold, space: 4 } },
    children: [new TextRun({ text, font: HEI, size: 30, color: C.blue })] });
}

function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 260, after: 120 },
    children: [new TextRun({ text, font: HEI, size: 25, color: C.ink })] });
}

function table(rows) {
  const cols = rows[0].length;
  // 每列先保证放得下最多6个字不折行，剩下的宽度按内容长短分
  const maxlen = Array.from({ length: cols }, (_, j) => Math.max(...rows.map(r => (r[j] || "").length), 2));
  const minw = maxlen.map(l => Math.min(l, 6) * 205 + 220);
  const extra = maxlen.map((l, j) => Math.max(Math.min(l, 40) * 205 + 220 - minw[j], 0));
  const room = W - minw.reduce((a, b) => a + b, 0);
  const etot = extra.reduce((a, b) => a + b, 0) || 1;
  let widths = minw.map((m, j) => Math.floor(m + Math.max(room, 0) * extra[j] / etot));
  widths[widths.length - 1] += W - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: C.line };
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((cell, j) =>
      new TableCell({ width: { size: widths[j], type: WidthType.DXA },
        borders: { top: border, bottom: border, left: border, right: border },
        shading: i === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: C.head } : undefined,
        margins: { top: 60, bottom: 60, left: 90, right: 90 },
        children: [new Paragraph({ spacing: { line: 300 }, children: runs(cell, { size: 19, bold: i === 0,
          color: i === 0 ? C.blue : C.ink, plainBold: true }) })] })) })) });
}

const out = [];
const tone = { color: C.red, bg: C.warmBg };

// 封面
const cover = pngSize(path.join(PAPER, "images_v3", "封面.png"));
out.push(
  new Paragraph({ spacing: { before: 1400, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "市 场 周 期 方 法 论", font: HEI, size: 21, color: C.gold })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "冬至理论", font: HEI, size: 64, color: C.blue })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "——一个关于市场冷热循环的十二阶段模型", font: BODY, size: 27, color: C.ink })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "第三版", font: HEI, size: 24, color: C.gold })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "看清阶段　做好选择　少亏大钱", font: HEI, size: 21, color: C.gray })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: cover.data,
    transformation: { width: 330, height: Math.round(330 * cover.h / cover.w) } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 500, after: 80 },
    children: [new TextRun({ text: "洛辰justin", font: BODY, size: 27, color: C.ink })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "二〇二六年十一月", font: BODY, size: 19, color: C.gray })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

let mode = null, buf = [];
for (const raw of SRC) {
  const line = raw.trimEnd();
  if (mode) {
    if (line === "@end") {
      if (mode === "box") {
        for (const t of buf) out.push(new Paragraph({ spacing: { line: 360, before: 120, after: 120 },
          indent: { left: 200, right: 200 }, alignment: AlignmentType.JUSTIFIED,
          shading: { type: ShadingType.CLEAR, color: "auto", fill: C.boxBg },
          border: { top: { style: BorderStyle.SINGLE, size: 10, color: C.gold, space: 8 },
                    bottom: { style: BorderStyle.SINGLE, size: 10, color: C.gold, space: 8 } },
          children: runs(t, { size: 20 }) }));
      } else if (mode === "scene") {
        const bd = { left: { style: BorderStyle.SINGLE, size: 18, color: tone.color, space: 8 } };
        out.push(new Paragraph({ keepNext: true, spacing: { before: 160, after: 0 }, indent: { left: 240, right: 120 },
          shading: { type: ShadingType.CLEAR, color: "auto", fill: tone.bg }, border: bd,
          children: [new TextRun({ text: "交易场景", font: HEI, size: 19, color: tone.color })] }));
        buf.forEach((t, i) => out.push(new Paragraph({ spacing: { line: 340, after: i === buf.length - 1 ? 220 : 0 },
          indent: { left: 240, right: 120, firstLine: 420 }, alignment: AlignmentType.JUSTIFIED,
          shading: { type: ShadingType.CLEAR, color: "auto", fill: tone.bg }, border: bd,
          children: runs(t, { size: 21, plainBold: true }) })));
      } else if (mode === "quote") {
        buf.forEach((t, i) => out.push(new Paragraph({ alignment: AlignmentType.CENTER,
          spacing: { before: i === 0 ? 160 : 0, after: i === buf.length - 1 ? 200 : 40 },
          children: [new TextRun({ text: t, font: HEI, size: 27, bold: true, color: i === 0 ? C.blue : C.red })] })));
      } else if (mode === "table") {
        out.push(table(buf.map(r => r.split("|"))));
        out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      }
      mode = null; buf = [];
    } else if (line) buf.push(line);
    continue;
  }
  if (!line) continue;
  if (line === "@titlepage") {
    out.push(
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 120 },
        children: [new TextRun({ text: "冬至理论", font: HEI, size: 40, color: C.blue })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
        children: [new TextRun({ text: "一个关于市场冷热循环的十二阶段模型（第三版）", font: HEI, size: 26, color: C.blue })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
        children: [new TextRun({ text: "洛辰justin", font: BODY, size: 21, color: C.gray })] }));
  } else if (["@box", "@scene", "@quote", "@table"].includes(line)) {
    mode = line.slice(1);
  } else if (line.startsWith("@keywords ")) {
    out.push(new Paragraph({ spacing: { before: 200, after: 300 }, children: [
      new TextRun({ text: "关键词　", font: HEI, size: 20, color: C.blue }),
      new TextRun({ text: line.slice(10), font: BODY, size: 20, color: C.ink })] }));
  } else if (line.startsWith("# ")) {
    out.push(h1(line.slice(2)));
  } else if (line.startsWith("## ")) {
    out.push(h2(line.slice(3)));
  } else if (line.startsWith("@fig ")) {
    const [num, file, title, note] = line.slice(5).split("|");
    out.push(...figure(num, file, title, note));
  } else if (line.startsWith("@stage ")) {
    const [num, name, sub, t] = line.slice(7).split("|");
    Object.assign(tone, t === "warm" ? { color: C.red, bg: C.warmBg } : { color: C.blue, bg: C.coolBg });
    out.push(new Paragraph({ keepNext: true, spacing: { before: 360, after: 80 },
      border: { left: { style: BorderStyle.SINGLE, size: 24, color: tone.color, space: 8 } }, indent: { left: 160 },
      children: [new TextRun({ text: "阶段" + num + "　", font: HEI, size: 19, color: C.gray }),
        new TextRun({ text: name, font: HEI, size: 32, bold: true, color: tone.color }),
        new TextRun({ text: "　" + sub, font: HEI, size: 22, color: C.ink })] }));
  } else if (line.startsWith("@people ")) {
    out.push(new Paragraph({ keepNext: true, spacing: { after: 120 }, indent: { left: 160 },
      children: [new TextRun({ text: "◆ " + line.slice(8), font: BODY, size: 20, color: tone.color })] }));
  } else if (line.startsWith("@key ")) {
    const t = line.slice(5);
    const i = t.indexOf("？") + 1;
    out.push(new Paragraph({ indent: { firstLine: 460 }, spacing: { line: 380, after: 100 }, children: [
      new TextRun({ text: t.slice(0, i), font: BODY, size: 23, bold: true, color: tone.color }),
      new TextRun({ text: t.slice(i), font: BODY, size: 23, color: tone.color })] }));
  } else if (line.startsWith("@caption ")) {
    const t = line.slice(9);
    const k = t.indexOf("　");
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 200, after: 80 }, children: [
      new TextRun({ text: t.slice(0, k + 1), font: HEI, size: 20, bold: true, color: C.blue }),
      new TextRun({ text: t.slice(k + 1), font: HEI, size: 20, color: C.ink })] }));
  } else if (line.startsWith("@note ")) {
    out.push(new Paragraph({ spacing: { after: 200, line: 300 }, children: [
      new TextRun({ text: line.slice(6), font: BODY, size: 18, color: C.gray })] }));
  } else if (line.startsWith("@center ")) {
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240 }, children: [
      new TextRun({ text: line.slice(8), font: BODY, size: 20, color: C.gray })] }));
  } else if (line.startsWith("- ")) {
    out.push(new Paragraph({ numbering: { reference: "dot", level: 0 }, spacing: { line: 360, after: 60 },
      children: runs(line.slice(2)) }));
  } else {
    out.push(body(line));
  }
}

const doc = new Document({
  creator: "洛辰justin", title: "冬至理论（第三版）",
  styles: { default: { document: { run: { font: BODY, size: 23, color: C.ink } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HEI, size: 30, color: C.blue }, paragraph: { spacing: { before: 420, after: 220 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HEI, size: 25, color: C.ink }, paragraph: { spacing: { before: 260, after: 120 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "dot", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 640, hanging: 280 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1531, right: 1587, bottom: 1417, left: 1587, header: 720, footer: 720 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "— ", size: 18, color: C.gray }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: C.gray }),
      new TextRun({ text: " —", size: 18, color: C.gray })] })] }) },
    children: out,
  }],
});

Packer.toBuffer(doc).then(b => {
  const f = path.join(PAPER, "冬至理论_v3.docx");
  fs.writeFileSync(f, b);
  console.log("written", f, b.length);
});
