/** Small local SVG line chart. Only measured samples are drawn. */
export function lineChart(samples, key, label, color = '#00D9FF') {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 640 180');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', label);
  svg.classList.add('line-chart');
  const values = samples.filter(sample => typeof sample[key] === 'number');
  if (!values.length) return svg;
  const minTime = values[0].timestamp;
  const maxTime = values[values.length - 1].timestamp;
  const span = Math.max(1, maxTime - minTime);
  const points = values.map(sample => {
    const x = 16 + (sample.timestamp - minTime) / span * 608;
    const y = 164 - Math.min(100, Math.max(0, sample[key])) / 100 * 148;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  for (const percent of [0, 25, 50, 75, 100]) {
    const line = document.createElementNS(ns, 'line');
    const y = 164 - percent / 100 * 148;
    for (const [attr, value] of Object.entries({x1: 16, x2: 624, y1: y, y2: y, stroke: '#24344a', 'stroke-width': 1})) line.setAttribute(attr, value);
    svg.append(line);
  }
  const polyline = document.createElementNS(ns, 'polyline');
  polyline.setAttribute('points', points);
  polyline.setAttribute('fill', 'none');
  polyline.setAttribute('stroke', color);
  polyline.setAttribute('stroke-width', '2.5');
  polyline.setAttribute('stroke-linecap', 'round');
  polyline.setAttribute('stroke-linejoin', 'round');
  svg.append(polyline);
  return svg;
}

/** Bandwidth chart with a dynamic local scale; no synthetic samples. */
export function trafficChart(samples, label) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 640 180');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', label);
  svg.classList.add('line-chart');
  const valid = samples.filter(row => Number.isFinite(row.down) && Number.isFinite(row.up));
  if (!valid.length) return svg;
  const high = Math.max(1024, ...valid.flatMap(row => [row.down, row.up]));
  const t0 = valid[0].time;
  const span = Math.max(1, valid[valid.length - 1].time - t0);
  for (const [key, color] of [['down', '#00D9FF'], ['up', '#22C55E']]) {
    const polyline = document.createElementNS(ns, 'polyline');
    const points = valid.map(row => `${(16 + (row.time - t0) / span * 608).toFixed(1)},${(164 - row[key] / high * 148).toFixed(1)}`).join(' ');
    polyline.setAttribute('points', points);
    polyline.setAttribute('fill', 'none');
    polyline.setAttribute('stroke', color);
    polyline.setAttribute('stroke-width', '2.5');
    svg.append(polyline);
  }
  return svg;
}
