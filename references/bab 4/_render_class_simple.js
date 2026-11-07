/**
 * Render CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio -> PNG + SVG
 * Sumber tunggal: file .drawio. Tidak ada gambar raster yang ditempel.
 */
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

const DIR = __dirname;
const SRC = path.join(DIR, 'CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio');
const OUT_PNG = path.join(DIR, 'CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.png');
const OUT_SVG = path.join(DIR, 'CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.svg');

const xml = fs.readFileSync(SRC, 'utf8');
const pageW = parseFloat((xml.match(/pageWidth="([\d.]+)"/) || [0, 1250])[1]);
const pageH = parseFloat((xml.match(/pageHeight="([\d.]+)"/) || [0, 1260])[1]);

function decodeHtml(s) {
  return s
    .replace(/&#xa;/gi, '\n')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, '&');
}
function stripTags(s) { return String(s).replace(/<\/?[ib]>/gi, '').replace(/\s+/g, ' ').trim(); }
function escXml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}

/* ---------------- parse vertices ---------------- */
const vertices = [];
const vRe = /<mxCell id="([^"]+)" value="([^"]*)" style="([^"]*)" vertex="1" parent="1">\s*<mxGeometry x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"/g;
let m;
while ((m = vRe.exec(xml)) !== null) {
  vertices.push({
    id: m[1], value: decodeHtml(m[2]), style: m[3],
    x: +m[4], y: +m[5], w: +m[6], h: +m[7],
  });
}
const classCells = [];
const textCells = [];
for (const v of vertices) {
  if (/shape=rectangle/.test(v.style)) classCells.push(v);
  else if (/text;/.test(v.style)) textCells.push(v);
}

/* ---------------- parse edges ---------------- */
const edges = [];
const eRe = /<mxCell id="([^"]+)" value="([^"]*)" style="([^"]*)" edge="1" parent="1" source="([^"]+)" target="([^"]+)">([\s\S]*?)<\/mxCell>/g;
while ((m = eRe.exec(xml)) !== null) {
  const inner = m[6];
  const points = [];
  const pRe = /<mxPoint x="([\d.]+)" y="([\d.]+)"\/>/g;
  let pm;
  while ((pm = pRe.exec(inner)) !== null) points.push({ x: +pm[1], y: +pm[2] });
  edges.push({
    id: m[1], label: decodeHtml(m[2]).trim(), style: m[3],
    source: m[4], target: m[5], points,
  });
}

/* ---------------- class model ---------------- */
function parseClass(cell) {
  const raw = cell.value.split('\n').map(s => s.trim()).filter(Boolean);
  let i = raw.indexOf('----');
  const header = i >= 0 ? raw.slice(0, i) : raw.slice(0, 2);
  let rest = i >= 0 ? raw.slice(i + 1) : [];
  let j = rest.indexOf('----');
  const attrs = j >= 0 ? rest.slice(0, j) : [];
  const ops = j >= 0 ? rest.slice(j + 1) : rest;
  const stereo = header.length > 1 ? stripTags(header[0]) : '';
  const name = stripTags(header.length > 1 ? header[1] : header[0]);
  const fillColor = (cell.style.match(/fillColor=(#[0-9A-Fa-f]{6})/) || ['', '#FFFFFF'])[1];
  return {
    id: cell.id, x: cell.x, y: cell.y, w: cell.w, h: cell.h,
    stereo, name, fillColor,
    attrs: attrs.map(stripTags),
    ops: ops.map(stripTags),
  };
}
const classes = classCells.map(parseClass);
const byId = new Map(classes.map(c => [c.id, c]));

/* ---------------- PNG ---------------- */
const SCALE = 3;
const canvas = createCanvas(pageW * SCALE, pageH * SCALE);
const ctx = canvas.getContext('2d');
ctx.scale(SCALE, SCALE);
ctx.fillStyle = '#FFFFFF';
ctx.fillRect(0, 0, pageW, pageH);

const FONT = '"Segoe UI", "Helvetica Neue", Arial, sans-serif';
const HEADER_FILL = '#ECECEC';
const BODY_FILL = '#FFFFFF';
const STROKE = '#000000';
const ROW = 15;

function textWidth(text, font) {
  ctx.font = font;
  return ctx.measureText(text).width;
}

function fitBodyFont(rows, maxWidth, start = 10) {
  let size = start;
  while (size > 8.0) {
    const f = `${size}px ${FONT}`;
    if (rows.every(r => textWidth(r, f) <= maxWidth)) return size;
    size -= 0.25;
  }
  return 8.0;
}

function drawClass(c) {
  const headerH = 40;
  const padX = 8;
  const innerW = c.w - padX * 2;
  const bodyRows = c.attrs.concat(c.ops);
  const bodyFontSize = fitBodyFont(bodyRows, innerW, 10);
  const bodyFont = `${bodyFontSize}px ${FONT}`;
  const rowH = Math.max(12, Math.round(bodyFontSize + 4.5));

  const attrTextH = c.attrs.length ? c.attrs.length * rowH + 8 : 10;
  let opsTextH = c.ops.length ? c.ops.length * rowH + 8 : 10;
  let total = headerH + attrTextH + opsTextH;
  if (total > c.h) {
    const overflow = total - c.h;
    opsTextH = Math.max(10, opsTextH - overflow);
    total = headerH + attrTextH + opsTextH;
  }
  const attrTop = c.y + headerH;
  const sep2Y = attrTop + attrTextH;
  const opsTop = sep2Y;

  // body + border
  ctx.fillStyle = c.fillColor || '#FFFFFF';
  ctx.fillRect(c.x, c.y, c.w, c.h);
  ctx.strokeStyle = STROKE;
  ctx.lineWidth = 1;
  ctx.strokeRect(c.x + 0.5, c.y + 0.5, c.w - 1, c.h - 1);

  // header
  ctx.fillStyle = HEADER_FILL;
  ctx.fillRect(c.x + 0.5, c.y + 0.5, c.w - 1, headerH - 1);
  ctx.beginPath();
  ctx.moveTo(c.x, c.y + headerH + 0.5);
  ctx.lineTo(c.x + c.w, c.y + headerH + 0.5);
  ctx.stroke();

  // header text
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#000000';
  if (c.stereo) {
    ctx.font = `italic 9.5px ${FONT}`;
    ctx.fillText(c.stereo, c.x + c.w / 2, c.y + 16);
  }
  ctx.font = `bold 12px ${FONT}`;
  ctx.fillText(c.name, c.x + c.w / 2, c.y + (c.stereo ? 33 : 26));

  // attribute rows
  ctx.textAlign = 'left';
  ctx.font = bodyFont;
  c.attrs.forEach((line, idx) => {
    ctx.fillText(line, c.x + padX, attrTop + 4 + rowH * idx + bodyFontSize);
  });

  // separator between attrs and ops
  if (c.ops.length > 0) {
    ctx.beginPath();
    ctx.moveTo(c.x, sep2Y + 0.5);
    ctx.lineTo(c.x + c.w, sep2Y + 0.5);
    ctx.stroke();
  }

  // operation rows
  c.ops.forEach((line, idx) => {
    ctx.fillText(line, c.x + padX, opsTop + 4 + rowH * idx + bodyFontSize);
  });
}

classes.forEach(drawClass);

/* ---------------- geometry helpers ---------------- */
function center(c) { return { x: c.x + c.w / 2, y: c.y + c.h / 2 }; }
function borderPoint(c, towardX, towardY) {
  const cx = c.x + c.w / 2, cy = c.y + c.h / 2;
  const dx = towardX - cx, dy = towardY - cy;
  if (dx === 0 && dy === 0) return { x: cx, y: cy };
  const sx = dx === 0 ? Infinity : (c.w / 2) / Math.abs(dx);
  const sy = dy === 0 ? Infinity : (c.h / 2) / Math.abs(dy);
  const s = Math.min(sx, sy);
  return { x: cx + dx * s, y: cy + dy * s };
}

function edgePoints(e) {
  const s = byId.get(e.source), t = byId.get(e.target);
  if (!s || !t) return null;
  const first = e.points.length ? e.points[0] : center(t);
  const last = e.points.length ? e.points[e.points.length - 1] : center(s);
  const start = borderPoint(s, first.x, first.y);
  const end = borderPoint(t, last.x, last.y);
  return [start, ...e.points, end];
}

function segLength(a, b) { return Math.hypot(b.x - a.x, b.y - a.y); }
function longestSegmentMid(pts) {
  let best = null, bestLen = -1;
  for (let i = 0; i < pts.length - 1; i++) {
    const len = segLength(pts[i], pts[i + 1]);
    if (len > bestLen) { bestLen = len; best = [pts[i], pts[i + 1]]; }
  }
  if (!best) return pts[0];
  return { x: (best[0].x + best[1].x) / 2, y: (best[0].y + best[1].y) / 2 };
}

function drawLabel(text, x, y, fontSize = 9.5, bold = false) {
  if (!text) return;
  ctx.font = `${bold ? 'bold ' : ''}${fontSize}px ${FONT}`;
  const w = ctx.measureText(text).width;
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(x - w / 2 - 3, y - fontSize + 1, w + 6, fontSize + 4);
  ctx.fillStyle = '#000000';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(text, x, y + 1);
}

function drawDiamond(x, y, dirX, dirY, size = 9) {
  const len = Math.hypot(dirX, dirY) || 1;
  const ux = dirX / len, uy = dirY / len;
  const px = -uy, py = ux;
  const tip = { x: x + ux * size, y: y + uy * size };
  const left = { x: x + px * size * 0.5, y: y + py * size * 0.5 };
  const right = { x: x - px * size * 0.5, y: y - py * size * 0.5 };
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(left.x, left.y);
  ctx.lineTo(tip.x, tip.y);
  ctx.lineTo(right.x, right.y);
  ctx.closePath();
  ctx.fillStyle = '#FFFFFF';
  ctx.fill();
  ctx.strokeStyle = STROKE;
  ctx.stroke();
}

function drawOpenArrow(x, y, dirX, dirY, size = 7) {
  const len = Math.hypot(dirX, dirY) || 1;
  const ux = dirX / len, uy = dirY / len;
  const px = -uy, py = ux;
  ctx.beginPath();
  ctx.moveTo(x - ux * size + px * size * 0.55, y - uy * size + py * size * 0.55);
  ctx.lineTo(x, y);
  ctx.lineTo(x - ux * size - px * size * 0.55, y - uy * size - py * size * 0.55);
  ctx.stroke();
}

edges.forEach(e => {
  const pts = edgePoints(e);
  if (!pts) return;
  const dashed = /dashed=1/.test(e.style);
  const aggregation = /startArrow=diamond/.test(e.style);
  ctx.strokeStyle = STROKE;
  ctx.lineWidth = 1;
  ctx.setLineDash(dashed ? [5, 3] : []);
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.stroke();
  ctx.setLineDash([]);

  if (aggregation) {
    const d = { x: pts[0].x - pts[1].x, y: pts[0].y - pts[1].y };
    drawDiamond(pts[0].x, pts[0].y, d.x, d.y);
  }
  if (dashed) {
    const a = pts[pts.length - 2], b = pts[pts.length - 1];
    drawOpenArrow(b.x, b.y, b.x - a.x, b.y - a.y);
  }
  if (e.label) {
    const p = longestSegmentMid(pts);
    drawLabel(e.label, p.x, p.y - 3);
  }
});

/* ---------------- multiplicity / free text ---------------- */
textCells.forEach(tc => {
  ctx.font = 'bold 10px ' + FONT;
  ctx.fillStyle = '#000000';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(tc.value, tc.x + tc.w / 2, tc.y + tc.h / 2);
});

fs.writeFileSync(OUT_PNG, canvas.toBuffer('image/png'));

/* ---------------- SVG ---------------- */
const svg = [];
svg.push(`<?xml version="1.0" encoding="UTF-8"?>`);
svg.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${pageW * SCALE}" height="${pageH * SCALE}" viewBox="0 0 ${pageW} ${pageH}">`);
svg.push(`<rect x="0" y="0" width="${pageW}" height="${pageH}" fill="#FFFFFF"/>`);
svg.push(`<g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif" stroke="#000000" stroke-width="1">`);

function svgText(x, y, text, opts = {}) {
  const { size = 10, bold = false, italic = false, anchor = 'start', fill = '#000000' } = opts;
  const style = `${bold ? 'font-weight="bold" ' : ''}${italic ? 'font-style="italic" ' : ''}fill="${fill}"`;
  return `<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" ${style} stroke="none">${escXml(text)}</text>`;
}

classes.forEach(c => {
  const headerH = 40, padX = 8;
  const innerW = c.w - padX * 2;
  const bodyFontSize = fitBodyFont(c.attrs.concat(c.ops), innerW, 10);
  const rowH = Math.max(12, Math.round(bodyFontSize + 4.5));
  const attrTextH = c.attrs.length ? c.attrs.length * rowH + 8 : 10;
  let opsTextH = c.ops.length ? c.ops.length * rowH + 8 : 10;
  let total = headerH + attrTextH + opsTextH;
  if (total > c.h) opsTextH = Math.max(10, opsTextH - (total - c.h));
  const attrTop = c.y + headerH;
  const sep2Y = attrTop + attrTextH;
  const opsTop = sep2Y;

  svg.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" fill="${c.fillColor || '#FFFFFF'}"/>`);
  svg.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${headerH}" fill="${HEADER_FILL}"/>`);
  svg.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" fill="none"/>`);
  svg.push(`<line x1="${c.x}" y1="${c.y + headerH}" x2="${c.x + c.w}" y2="${c.y + headerH}"/>`);
  if (c.ops.length > 0) svg.push(`<line x1="${c.x}" y1="${sep2Y}" x2="${c.x + c.w}" y2="${sep2Y}"/>`);
  if (c.stereo) svg.push(svgText(c.x + c.w / 2, c.y + 16, c.stereo, { size: 9.5, italic: true, anchor: 'middle' }));
  svg.push(svgText(c.x + c.w / 2, c.y + (c.stereo ? 33 : 26), c.name, { size: 12, bold: true, anchor: 'middle' }));
  c.attrs.forEach((line, idx) => svg.push(svgText(c.x + padX, attrTop + 4 + rowH * idx + bodyFontSize, line, { size: bodyFontSize })));
  c.ops.forEach((line, idx) => svg.push(svgText(c.x + padX, opsTop + 4 + rowH * idx + bodyFontSize, line, { size: bodyFontSize })));
});

edges.forEach(e => {
  const pts = edgePoints(e);
  if (!pts) return;
  const dashed = /dashed=1/.test(e.style);
  const aggregation = /startArrow=diamond/.test(e.style);
  const d = pts.map(p => `${p.x},${p.y}`).join(' ');
  svg.push(`<polyline points="${d}" fill="none"${dashed ? ' stroke-dasharray="5,3"' : ''}/>`);
  if (aggregation) {
    const dx = pts[0].x - pts[1].x, dy = pts[0].y - pts[1].y;
    const len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, px = -uy, py = ux;
    const s = 9;
    const tip = `${pts[0].x + ux * s},${pts[0].y + uy * s}`;
    const l = `${pts[0].x + px * s * 0.5},${pts[0].y + py * s * 0.5}`;
    const r = `${pts[0].x - px * s * 0.5},${pts[0].y - py * s * 0.5}`;
    svg.push(`<polygon points="${pts[0].x},${pts[0].y} ${l} ${tip} ${r}" fill="#FFFFFF"/>`);
  }
  if (dashed) {
    const a = pts[pts.length - 2], b = pts[pts.length - 1];
    const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
    const ux = dx / len, uy = dy / len, px = -uy, py = ux, s = 7;
    svg.push(`<polyline points="${b.x - ux * s + px * s * 0.55},${b.y - uy * s + py * s * 0.55} ${b.x},${b.y} ${b.x - ux * s - px * s * 0.55},${b.y - uy * s - py * s * 0.55}" fill="none"/>`);
  }
  if (e.label) {
    const p = longestSegmentMid(pts);
    ctx.font = `9.5px ${FONT}`;
    const w = ctx.measureText(e.label).width;
    svg.push(`<rect x="${p.x - w / 2 - 3}" y="${p.y - 3 - 9.5 + 1}" width="${w + 6}" height="${9.5 + 4}" fill="#FFFFFF" stroke="none"/>`);
    svg.push(svgText(p.x, p.y - 2, e.label, { size: 9.5, anchor: 'middle' }));
  }
});

textCells.forEach(tc => {
  svg.push(svgText(tc.x + tc.w / 2, tc.y + tc.h / 2 + 3.5, tc.value, { size: 10, bold: true, anchor: 'middle' }));
});
svg.push(`</g></svg>`);
fs.writeFileSync(OUT_SVG, svg.join('\n'), 'utf8');

console.log('Rendered:', OUT_PNG);
console.log('Rendered:', OUT_SVG);
console.log('Classes:', classes.length, '| Edges:', edges.length);
console.log('Page:', pageW, 'x', pageH, '| PNG:', pageW * SCALE, 'x', pageH * SCALE);
