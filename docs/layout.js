/* Interactive Glove80 layout. Data comes from layout-data.js (generated). */
(() => {
  'use strict';
  const data = window.GLOVE80;
  const $ = (s, root = document) => root.querySelector(s);
  const state = { layer: data.layers[0].name, ru: false, shift: false, flavor: data.default, preview: null };
  try { state.flavor = localStorage.getItem('flavor') || state.flavor; } catch (e) { /* storage unavailable */ }

  const KEY = 0.92, SVG = 'http://www.w3.org/2000/svg';
  const corners = data.geometry.flatMap(g => {
    const r = (g.r || 0) * Math.PI / 180, cx = g.x + 0.5, cy = g.y + 0.5;
    return [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]].map(([x, y]) => [cx + x * Math.cos(r) - y * Math.sin(r), cy + x * Math.sin(r) + y * Math.cos(r)]);
  });
  const xs = corners.map(c => c[0]), ys = corners.map(c => c[1]);
  const viewBox = [Math.min(...xs) - 0.3, Math.min(...ys) - 0.3, Math.max(...xs) - Math.min(...xs) + 0.6, Math.max(...ys) - Math.min(...ys) + 0.6].join(' ');

  const layer = name => data.layers.find(l => l.name === name);
  const colors = () => data.colors[state.flavor];

  function legend(key, ru, shift) {
    const base = ru && key.ru !== undefined ? [key.ru, key.ruShift] : [key.label, key.shift];
    return shift && base[1] ? [base[1], base[0]] : base;
  }

  function el(tag, attrs, text) {
    const node = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function render(svg, name, ru, shift, interactive) {
    svg.setAttribute('viewBox', viewBox);
    svg.replaceChildren();
    const palette = colors();
    layer(name).keys.forEach((key, i) => {
      const g = data.geometry[i], fill = palette[key.role];
      const group = el('g', { transform: `translate(${g.x} ${g.y}) rotate(${g.r || 0} 0.5 0.5)`, class: 'key' + (key.inherited ? ' inherited' : '') + (key.layer === name ? ' active' : '') });
      group.appendChild(el('rect', { x: (1 - KEY) / 2, y: (1 - KEY) / 2, width: KEY, height: KEY, rx: 0.12, fill: fill || 'var(--surface0)', class: fill ? 'lit' : 'unlit' }));
      const [main, small] = legend(key, ru, shift);
      const long = main.length > 3;
      group.appendChild(el('text', { x: 0.5, y: long ? 0.57 : 0.6, class: 'label' + (long ? ' long' : '') }, main));
      if (small && small !== main.toUpperCase()) group.appendChild(el('text', { x: 0.5, y: 0.3, class: 'small' }, small));
      if (key.lock) group.appendChild(el('text', { x: 0.5, y: 0.84, class: 'small' }, '⌁'));
      if (interactive && key.layer) {
        group.classList.add('switch');
        group.addEventListener('mouseenter', () => { state.preview = key.layer; show(); });
        group.addEventListener('mouseleave', () => { state.preview = null; show(); });
        group.addEventListener('click', () => { state.layer = key.layer; state.preview = null; show(); });
      }
      group.appendChild(el('title', {}, `${g.label}: ${main}${small ? ' / ' + small : ''}`));
      svg.appendChild(group);
    });
  }

  function legendList(ul, name) {
    const palette = colors(), roles = new Set(layer(name).keys.map(k => k.role));
    ul.replaceChildren(...Object.entries(data.roles).filter(([role]) => roles.has(role)).map(([role, label]) => {
      const li = document.createElement('li');
      li.innerHTML = `<i style="background:${palette[role] || 'var(--surface0)'}"></i>${label}`;
      return li;
    }));
  }

  function applyFlavor() {
    const f = data.flavors[state.flavor];
    for (const [k, v] of Object.entries(f)) document.documentElement.style.setProperty('--' + k, v);
    document.documentElement.dataset.light = state.flavor === 'latte';
    try { localStorage.setItem('flavor', state.flavor); } catch (e) { /* storage unavailable */ }
  }

  function show() {
    const name = state.preview || state.layer;
    $('.title').textContent = `${name} · ${state.ru ? data.russian : data.name}`;
    render($('.keyboard'), name, state.ru, state.shift, true);
    legendList($('.legend'), name);
    for (const b of $('.layers').children) b.setAttribute('aria-current', b.textContent === state.layer);
    $('.lang').textContent = state.ru ? 'RU' : 'EN';
    $('.shift').setAttribute('aria-pressed', state.shift);
    const printout = $('.printout');
    printout.replaceChildren(...data.layers.map(l => {
      const page = document.createElement('article');
      page.innerHTML = `<h2>${l.name} · ${state.ru ? data.russian : data.name}</h2>`;
      const svg = el('svg', { class: 'keyboard' }), ul = document.createElement('ul');
      ul.className = 'legend';
      render(svg, l.name, state.ru, state.shift, false);
      legendList(ul, l.name);
      page.append(svg, ul);
      return page;
    }));
  }

  $('.layers').replaceChildren(...data.layers.map(l => {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = l.name;
    b.addEventListener('click', () => { state.layer = l.name; show(); });
    return b;
  }));
  $('.flavor').replaceChildren(...Object.keys(data.flavors).map(f => new Option(f, f, false, f === state.flavor)));
  $('.flavor').addEventListener('change', e => { state.flavor = e.target.value; applyFlavor(); show(); });
  $('.lang').addEventListener('click', () => { state.ru = !state.ru; show(); });
  $('.shift').addEventListener('click', () => { state.shift = !state.shift; show(); });
  $('.print').addEventListener('click', () => window.print());
  let held = false;
  addEventListener('keydown', e => { if (e.key === 'Shift' && !held) { held = true; state.shift = !state.shift; show(); } });
  addEventListener('keyup', e => { if (e.key === 'Shift' && held) { held = false; state.shift = !state.shift; show(); } });

  applyFlavor();
  show();
})();
