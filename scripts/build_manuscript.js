// Build FlyLite_manuscript_EN_v1.docx from the Markdown manuscript, embedding the final figures.
// usage: node build_manuscript.js ../FlyLite_manuscript_EN_v1.md ../results/final ../FlyLite_manuscript_EN_v1.docx
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, AlignmentType,
        ImageRun, PageBreak, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, LineNumberRestartFormat } = require("docx");
const LAYOUT = process.env.LAYOUT || "journal";   // "journal": centred title block, 1.5 spacing, line numbers, keywords

const [mdPath, figDir, outPath] = process.argv.slice(2);
const md = fs.readFileSync(mdPath, "utf8").split(/\r?\n/);

// ---- inline LaTeX -> Unicode (good enough for a preprint; polish in Word if needed)
const TEX = [[/\\tau_m/g, "τₘ"], [/\\tau_s/g, "τₛ"], [/\\sigma/g, "σ"], [/\\tau/g, "τ"], [/\\xi/g, "ξ"], [/\\geq/g, "≥"], [/\\leq/g, "≤"], [/\\in\b/g, "∈"],
  [/\\subset/g, "⊂"], [/\\cdot/g, "·"], [/\\cap/g, "∩"], [/\\cup/g, "∪"], [/\\lvert/g, "|"], [/\\rvert/g, "|"], [/\\\{/g, "⦃"], [/\\\}/g, "⦄"], [/\\,/g, " "],
  [/\\dot v/g, "v̇"], [/\\dot g/g, "ġ"], [/\\bar r/g, "r̄"], [/\\sqrt\{([^}]*)\}/g, "√$1"], [/\\mathrm\{([^}]*)\}/g, "$1"], [/\\times/g, "×"], [/\\approx/g, "≈"],
  [/\^\{full\}/g, "ᶠᵘˡˡ"], [/\^\*/g, "*"], [/_\{([^}]*)\}/g, "_$1"], [/\^\{([^}]*)\}/g, "^$1"], [/\\/g, ""]];
function tex(s) { for (const [re, r] of TEX) s = s.replace(re, r); return s.replace(/[{}]/g, "").replace(/⦃/g, "{").replace(/⦄/g, "}"); }

// ---- inline markdown: **bold**, *italic*, `code`, $math$ -> TextRuns
const AST = "⁢AST⁢";  // token for an escaped literal asterisk (markdown "\*"), restored after inline parsing
function runs(text, base = {}) {
  text = text.replace(/\\\*/g, AST).replace(/\\_/g, "_");
  const restore = t => t.split(AST).join("*");
  const out = []; let i = 0;
  const re = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\$[^$]+\$)/g; let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > i) out.push(new TextRun({ text: restore(text.slice(i, m.index)), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: restore(t.slice(2, -2)), bold: true, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: restore(t.slice(1, -1)), font: "Consolas", size: 18, ...base }));
    else if (t.startsWith("$")) out.push(new TextRun({ text: restore(tex(t.slice(1, -1))), italics: true, ...base }));
    else out.push(new TextRun({ text: restore(t.slice(1, -1)), italics: true, ...base }));
    i = m.index + t.length;
  }
  if (i < text.length) out.push(new TextRun({ text: restore(text.slice(i)), ...base }));
  return out;
}
const LINE = LAYOUT === "journal" ? 360 : 300;
const P = (text, opts = {}) => new Paragraph({ children: runs(text, opts.run || {}), spacing: { after: 120, line: LINE }, alignment: opts.align, ...opts.para });

// ---- table from markdown pipe rows
function table(rows) {
  const cells = rows.filter(r => !/^\|\s*-+/.test(r)).map(r => r.replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
  const ncol = Math.max(...cells.map(c => c.length)); const total = 9000; const w = Math.floor(total / ncol);
  const mk = (txt, head) => new TableCell({ width: { size: w, type: WidthType.DXA }, shading: head ? { type: ShadingType.CLEAR, fill: "EEF2F7", color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 }, children: [new Paragraph({ children: runs(txt, { size: 17, bold: !!head }), spacing: { after: 0 } })] });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: Array(ncol).fill(w),
    rows: cells.map((c, i) => new TableRow({ tableHeader: i === 0, children: Array.from({ length: ncol }, (_, j) => mk(c[j] || "", i === 0)) })) });
}

// ---- figure image (PNG at 300 dpi, 7.2 in wide -> scale to 6.3 in text width)
function figure(name) {
  const p = path.join(figDir, name + ".png"); if (!fs.existsSync(p)) return null;
  const buf = fs.readFileSync(p); const wpx = buf.readUInt32BE(16), hpx = buf.readUInt32BE(20);
  const wIn = 6.3, hIn = wIn * hpx / wpx;
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: Math.round(wIn * 96), height: Math.round(hIn * 96) } })] });
}

// ---- walk the markdown
const body = []; let i = 0; let inFigs = false; let front = true;   // front = title block before the Abstract heading
const skipNote = /^> English manuscript v1/;
while (i < md.length) {
  let line = md[i];
  if (!line.trim() || line.trim() === "---") { i++; continue; }
  if (skipNote.test(line)) { i++; continue; }
  if (line.startsWith("# ")) { body.push(new Paragraph({ children: runs(line.slice(2), { size: 32, bold: true }), spacing: { after: 360, line: 300 }, alignment: AlignmentType.CENTER })); i++; continue; }
  if (line.startsWith("## ")) { const t = line.slice(3).trim(); inFigs = /^Figure legends/.test(t); const isAbs = /^Abstract/.test(t); if (isAbs) front = false;
    body.push(new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, spacing: { before: isAbs ? 600 : 360, after: 160 } })); i++; continue; }
  if (line.startsWith("### ")) { body.push(new Paragraph({ text: line.slice(4).trim(), heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } })); i++; continue; }
  if (line.startsWith("|")) { const rows = []; while (i < md.length && md[i].startsWith("|")) rows.push(md[i++]); body.push(table(rows)); body.push(new Paragraph({ spacing: { after: 120 } })); continue; }
  if (/^\d+\. /.test(line)) { body.push(new Paragraph({ children: runs(line.replace(/^\d+\. /, "")), numbering: { reference: "refs", level: 0 }, spacing: { after: 80 } })); i++; continue; }
  if (line.startsWith("> ")) { body.push(P(line.slice(2), { run: { italics: true, color: "555555" } })); i++; continue; }
  // figure legend paragraph: insert the image before its legend
  const fm = inFigs && line.match(/^\*\*(Figure (S?\d+))\./);
  if (fm) { const img = figure("fig" + fm[2]); if (img) { body.push(new Paragraph({ children: [new PageBreak()] })); body.push(img); } }
  if (front) { body.push(P(line, { align: AlignmentType.CENTER, run: line.startsWith("**") ? { size: 24 } : { size: 20 }, para: { spacing: { after: 80, line: 276 } } })); i++; continue; }   // author / affiliation / correspondence
  if (/^\*\*Keywords:\*\*/.test(line)) { body.push(P(line, { run: { size: 20 }, para: { spacing: { before: 120, after: 240, line: 276 } } })); i++; continue; }
  body.push(P(line)); i++;
}

const doc = new Document({
  creator: "Donggyu An", title: "How sparse can a fly-brain model be?",
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: "Calibri" }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: "Calibri" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 480 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      ...(LAYOUT === "journal" ? { lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS, distance: 360 } } : {}) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "777777" })] })] }) },
    children: body }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(outPath, b); console.log("wrote", outPath, (b.length / 1e6).toFixed(1), "MB"); });
