const T = {
  text: "#1c1917",
  muted: "#5c574e",
  faint: "#8a8478",
  line: "#d9d3c6",
  fill: "#ece8dc",
  fill2: "#e4dfd1",
  accent: "#1f5f8b",
  good: "#2d6a45",
  bad: "#8b2e2e",
  added: "rgba(45, 106, 69, 0.28)",
  removed: "rgba(139, 46, 46, 0.28)",
  blue: "#1f5f8b",
  purple: "#6b4ea1",
  green: "#2d6a45",
  yellow: "#8a6a12",
};

const PAGES = [
  { href: "index.html", id: "index", label: "Notes" },
  { href: "harmonic-stack.html", id: "harmonic-stack", label: "Harmonics" },
  { href: "pluck.html", id: "pluck", label: "Pluck" },
  { href: "render.html", id: "render", label: "Render" },
  { href: "fft-values.html", id: "fft-values", label: "FFT values" },
  { href: "spectrum.html", id: "spectrum", label: "Spectrum" },
  { href: "energy-at.html", id: "energy-at", label: "energy_at" },
  { href: "correlation-formula.html", id: "correlation-formula", label: "Winding" },
  { href: "keybank.html", id: "keybank", label: "Keybank" },
];

function nav(active) {
  const el = document.getElementById("nav");
  el.innerHTML =
    `<a class="brand" href="index.html">piano-transcribe notes</a>` +
    PAGES.slice(1)
      .map(
        (p) =>
          `<a href="${p.href}" class="${p.id === active ? "active" : ""}">${p.label}</a>`,
      )
      .join("");
}

function downsample(xs, n) {
  if (xs.length <= n) return xs;
  return Array.from({ length: n }, (_, i) => {
    const src = Math.min(xs.length - 1, Math.round((i / (n - 1)) * (xs.length - 1)));
    return xs[src];
  });
}

function toPath(ys, w, h, yMin, yMax, pl, pr, pt, pb) {
  const iw = w - pl - pr;
  const ih = h - pt - pb;
  const span = yMax - yMin || 1;
  return ys
    .map((y, i) => {
      const x = pl + (i / Math.max(1, ys.length - 1)) * iw;
      const py = pt + ((yMax - y) / span) * ih;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${py.toFixed(1)}`;
    })
    .join(" ");
}

function signedFill(ys, w, h, yAbs, pl, pr, pt, pb, sign) {
  const iw = w - pl - pr;
  const ih = h - pt - pb;
  const zeroY = pt + ih / 2;
  const xOf = (i) => pl + (i / Math.max(1, ys.length - 1)) * iw;
  const yOf = (y) => pt + ((yAbs - y) / (2 * yAbs)) * ih;
  const parts = [];
  let run = null;
  const flush = (end) => {
    if (!run || !run.length) return;
    const start = end - run.length;
    const d = run.map((y, k) => {
      const i = start + k;
      return `${k === 0 ? "M" : "L"}${xOf(i).toFixed(1)} ${yOf(y).toFixed(1)}`;
    });
    d.push(`L${xOf(end - 1).toFixed(1)} ${zeroY.toFixed(1)}`);
    d.push(`L${xOf(start).toFixed(1)} ${zeroY.toFixed(1)} Z`);
    parts.push(d.join(" "));
    run = null;
  };
  for (let i = 0; i < ys.length; i++) {
    const keep = sign === 1 ? ys[i] >= 0 : ys[i] < 0;
    if (keep) {
      if (!run) run = [];
      run.push(ys[i]);
    } else flush(i);
  }
  flush(ys.length);
  return parts.join(" ");
}

function envelopeBand(env, w, h, yAbs, pl, pr, pt, pb) {
  const iw = w - pl - pr;
  const ih = h - pt - pb;
  const yOf = (amp) => pt + ((yAbs - amp) / (2 * yAbs)) * ih;
  const xOf = (i) => pl + (i / (env.length - 1)) * iw;
  const top = env.map(
    (e, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(2)} ${yOf(e * yAbs).toFixed(2)}`,
  );
  const bot = env
    .map((e, i) => `${xOf(i).toFixed(2)} ${yOf(-e * yAbs).toFixed(2)}`)
    .reverse();
  return `${top.join(" ")} L${bot.join(" L")} Z`;
}

function waveSvg({
  series,
  yAbs,
  xLabel,
  yLabel,
  w = 720,
  h = 140,
  fillSigned,
  fillEnv,
  mark,
}) {
  const pl = 40,
    pr = 10,
    pt = 8,
    pb = 22;
  const zeroY = pt + (h - pt - pb) / 2;
  let extra = "";
  if (fillEnv) {
    extra += `<path d="${envelopeBand(fillEnv, w, h, yAbs, pl, pr, pt, pb)}" fill="${T.fill2}"/>`;
  }
  if (fillSigned) {
    extra += `<path d="${signedFill(fillSigned, w, h, yAbs, pl, pr, pt, pb, 1)}" fill="${T.added}"/>`;
    extra += `<path d="${signedFill(fillSigned, w, h, yAbs, pl, pr, pt, pb, -1)}" fill="${T.removed}"/>`;
  }
  const paths = series
    .map(
      (s) =>
        `<path d="${toPath(s.ys, w, h, -yAbs, yAbs, pl, pr, pt, pb)}" fill="none" stroke="${s.color}" stroke-width="${s.width ?? 1.5}"/>`,
    )
    .join("");
  let markG = "";
  if (mark) {
    const iw = w - pl - pr;
    const ih = h - pt - pb;
    const markX = pl + (mark.i / Math.max(1, mark.n - 1)) * iw;
    const src = Math.min(
      series[0].ys.length - 1,
      Math.round((mark.i / Math.max(1, mark.n - 1)) * (series[0].ys.length - 1)),
    );
    const markY = pt + ((yAbs - series[0].ys[src]) / (2 * yAbs)) * ih;
    markG = `<line x1="${markX}" y1="${pt}" x2="${markX}" y2="${h - pb}" stroke="${mark.color}" stroke-width="1" stroke-dasharray="3 3"/>
      <circle cx="${markX}" cy="${markY}" r="3.5" fill="${mark.color}"/>`;
  }
  const yTop = yLabel ?? yAbs.toFixed(1);
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img">
    ${extra}
    <line x1="${pl}" y1="${zeroY}" x2="${w - pr}" y2="${zeroY}" stroke="${T.line}" stroke-width="1" stroke-dasharray="3 3"/>
    ${paths}
    ${markG}
    <text x="${pl - 6}" y="${pt + 8}" text-anchor="end" fill="${T.faint}" font-size="10">${yTop}</text>
    <text x="${(pl + w - pr) / 2}" y="${h - 4}" text-anchor="middle" fill="${T.faint}" font-size="10">${xLabel}</text>
  </svg>`;
}

function lineChart({ categories, series, height = 200, yMin, yMax, fill, refLines }) {
  const w = 840,
    h = height,
    pl = 48,
    pr = 12,
    pt = 12,
    pb = 28;
  const all = series.flatMap((s) => s.data);
  let lo = yMin ?? Math.min(0, ...all);
  let hi = yMax ?? Math.max(...all);
  if (lo === hi) {
    lo -= 1;
    hi += 1;
  }
  const colors = [T.accent, T.yellow, T.muted];
  const fills = series
    .map((s, i) => {
      if (!fill) return "";
      const d = toPath(s.data, w, h, lo, hi, pl, pr, pt, pb);
      const x0 = pl;
      const x1 = w - pr;
      const y0 = pt + ((hi - 0) / (hi - lo)) * (h - pt - pb);
      return `<path d="${d} L${x1} ${y0} L${x0} ${y0} Z" fill="${colors[i]}" opacity="0.12"/>`;
    })
    .join("");
  const paths = series
    .map(
      (s, i) =>
        `<path d="${toPath(s.data, w, h, lo, hi, pl, pr, pt, pb)}" fill="none" stroke="${colors[i]}" stroke-width="1.6"/>`,
    )
    .join("");
  const refs = (refLines || [])
    .map((r) => {
      const y = pt + ((hi - r.value) / (hi - lo)) * (h - pt - pb);
      return `<line x1="${pl}" y1="${y}" x2="${w - pr}" y2="${y}" stroke="${T.line}" stroke-dasharray="4 4"/>
        <text x="${w - pr}" y="${y - 4}" text-anchor="end" fill="${T.faint}" font-size="10">${r.label}</text>`;
    })
    .join("");
  const ticks = categories
    .map((c, i) => {
      if (!c) return "";
      const x = pl + (i / Math.max(1, categories.length - 1)) * (w - pl - pr);
      return `<text x="${x}" y="${h - 6}" text-anchor="middle" fill="${T.faint}" font-size="10">${c}</text>`;
    })
    .join("");
  const legend = series
    .map(
      (s, i) =>
        `<span style="color:${colors[i]};margin-right:12px;font-size:12px">${s.name}</span>`,
    )
    .join("");
  return `<div>${legend}
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">
      <line x1="${pl}" y1="${h - pb}" x2="${w - pr}" y2="${h - pb}" stroke="${T.line}"/>
      <line x1="${pl}" y1="${pt}" x2="${pl}" y2="${h - pb}" stroke="${T.line}"/>
      ${refs}${fills}${paths}${ticks}
      <text x="${pl - 6}" y="${pt + 4}" text-anchor="end" fill="${T.faint}" font-size="10">${hi.toFixed(2)}</text>
    </svg></div>`;
}

function barChart({ categories, data, yMax = 1, height = 180 }) {
  const w = 400,
    h = height,
    pl = 36,
    pr = 12,
    pt = 10,
    pb = 28;
  const iw = w - pl - pr;
  const ih = h - pt - pb;
  const bw = iw / categories.length;
  const bars = data
    .map((v, i) => {
      const bh = (v / yMax) * ih;
      return `<rect x="${pl + i * bw + 8}" y="${pt + ih - bh}" width="${bw - 16}" height="${bh}" fill="${T.accent}"/>
        <text x="${pl + (i + 0.5) * bw}" y="${h - 8}" text-anchor="middle" fill="${T.faint}" font-size="11">${categories[i]}</text>`;
    })
    .join("");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">
    <line x1="${pl}" y1="${h - pb}" x2="${w - pr}" y2="${h - pb}" stroke="${T.line}"/>
    ${bars}
  </svg>`;
}

function statsHtml(items) {
  return `<div class="grid grid-${Math.min(4, items.length)}">${items
    .map(
      (s) =>
        `<div class="stat ${s.tone || ""}"><div class="v">${s.value}</div><div class="l">${s.label}</div></div>`,
    )
    .join("")}</div>`;
}

function tableHtml({ headers, rows, align = [], tones = [], striped }) {
  const th = headers
    .map((h, i) => `<th class="${align[i] === "right" ? "num" : ""}">${h}</th>`)
    .join("");
  const body = rows
    .map((r, ri) => {
      const tone = tones[ri] ? ` class="tone-${tones[ri]}"` : "";
      const tds = r
        .map((c, i) => `<td class="${align[i] === "right" ? "num" : ""}">${c}</td>`)
        .join("");
      return `<tr${tone}>${tds}</tr>`;
    })
    .join("");
  return `<table><thead><tr>${th}</tr></thead><tbody>${body}</tbody></table>`;
}

function callout(tone, title, body) {
  return `<div class="callout ${tone || ""}"><div class="t">${title}</div>${body}</div>`;
}

function card(title, body, trail) {
  return `<div class="card"><div class="card-h">${title}${
    trail ? `<span class="trail">${trail}</span>` : ""
  }</div><div class="card-b">${body}</div></div>`;
}

function pillsHtml(items, active, key) {
  return items
    .map((it) => {
      const id = it.id ?? it.hz ?? it;
      const label = it.label ?? it;
      const on = String(id) === String(active);
      return `<button class="pill ${on ? "active" : ""}" data-key="${key}" data-id="${id}">${
        it.swatch
          ? `<span class="swatch" style="background:${it.swatch}"></span>`
          : ""
      }${label}</button>`;
    })
    .join("");
}

function midiToHz(m) {
  return 440 * Math.pow(2, (m - 69) / 12);
}

function makeSignal(freqs, n, rate, phaseDeg = 0) {
  const phase = (phaseDeg * Math.PI) / 180;
  const out = new Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / rate;
    let v = 0;
    for (const f of freqs) v += Math.sin(2 * Math.PI * f * t + phase);
    out[i] = v / freqs.length;
  }
  return out;
}

function correlate(x, freq, rate) {
  let re = 0,
    im = 0;
  const n = x.length;
  for (let i = 0; i < n; i++) {
    const angle = (2 * Math.PI * freq * i) / rate;
    re += x[i] * Math.cos(angle);
    im += x[i] * Math.sin(angle);
  }
  return { re, im, mag: Math.hypot(re, im) / n, reN: re / n, imN: im / n };
}

function hanning(m) {
  return Array.from({ length: m }, (_, n) => 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (m - 1)));
}

function fft(input) {
  const n = input.length;
  const re = input.slice();
  const im = new Array(n).fill(0);
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      const tr = re[i];
      re[i] = re[j];
      re[j] = tr;
      const ti = im[i];
      im[i] = im[j];
      im[j] = ti;
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wlenRe = Math.cos(ang);
    const wlenIm = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let wRe = 1,
        wIm = 0;
      const half = len >> 1;
      for (let j = 0; j < half; j++) {
        const k = i + j;
        const tRe = re[k + half] * wRe - im[k + half] * wIm;
        const tIm = re[k + half] * wIm + im[k + half] * wRe;
        re[k + half] = re[k] - tRe;
        im[k + half] = im[k] - tIm;
        re[k] += tRe;
        im[k] += tIm;
        const nwRe = wRe * wlenRe - wIm * wlenIm;
        wIm = wRe * wlenIm + wIm * wlenRe;
        wRe = nwRe;
      }
    }
  }
  const outRe = [],
    outIm = [],
    mag = [];
  for (let k = 0; k <= n / 2; k++) {
    outRe.push(re[k]);
    outIm.push(im[k]);
    mag.push(Math.hypot(re[k], im[k]));
  }
  return { re: outRe, im: outIm, mag };
}

function pluckNote(midi, n, dur, decay = 3) {
  const f = midiToHz(midi);
  return Array.from({ length: n }, (_, i) => {
    const t = (i / n) * dur;
    let wave = 0;
    for (let k = 1; k <= 4; k++) wave += Math.sin(2 * Math.PI * f * k * t) / k;
    return wave * Math.exp(-decay * t);
  });
}

function mixChord(chord, n, dur, decay = 3) {
  const out = new Array(n).fill(0);
  for (const m of chord) {
    const p = pluckNote(m, n, dur, decay);
    for (let i = 0; i < n; i++) out[i] += p[i];
  }
  const d = Math.max(chord.length, 1);
  return out.map((x) => x / d);
}

function topIdx(spec, n) {
  return spec
    .map((_, i) => i)
    .sort((a, b) => spec[a] - spec[b])
    .slice(-n)
    .reverse();
}
