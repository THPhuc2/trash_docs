/* Bản đồ trực quan — helper dùng chung.
   TQ.explorer : bấm node [data-k] → hiện giải thích trong [data-panel]
   TQ.stepper  : chạy từng bước; phần tử có data-on="2" | "2-4" | "3-" | "1,3,5" chỉ sáng ở các bước đó
   TQ.tabs     : nút [data-tab] ↔ khối [data-pane]
   TQ.docLink  : link về đúng mục trong tài liệu gốc (thư mục cha) */
(function () {
  const TQ = (window.TQ = {});

  TQ.DOCS = {
    frontier: { file: 'frontier-model-training-vi.html', name: 'Frontier Training (bản đầy đủ)' },
    nguyenly: { file: 'frontier-model-training-vi-nguyen-ly.html', name: 'Frontier Training (bản nguyên lý)' },
    inference: { file: 'inference-deploy-vi.html', name: 'Inference & Deploy' },
    vlm: { file: 'vlm-training-vi.html', name: 'VLM Training' },
    camnang: { file: 'training-recipes-cam-nang.html', name: 'Cẩm nang Training Recipes' },
  };

  // Link chỉ chạy được khi mở trang từ máy (file://) hoặc server local cùng thư mục.
  const h = location.hostname;
  TQ.canLinkDocs = location.protocol === 'file:' || h === 'localhost' || h === '127.0.0.1' || h === '';

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  TQ.esc = esc;

  TQ.docHref = (doc, anchor) => '../' + encodeURI(TQ.DOCS[doc].file) + (anchor ? '#' + anchor : '');

  TQ.docLink = (doc, anchor, label) => {
    const d = TQ.DOCS[doc];
    if (!d) return '';
    const text = esc(label || d.name);
    if (TQ.canLinkDocs) {
      return `<a class="doc-link" href="${TQ.docHref(doc, anchor)}" target="_blank" rel="noopener" title="${esc(d.name)}">${text}</a>`;
    }
    return `<span class="doc-link is-ref" title="Mở file ${esc(d.file)} trên máy để nhảy tới mục này">${text} · ${esc(d.name)}</span>`;
  };

  // item = { eyebrow, title, chips:[[text, variant]], html, doc:[[docKey, anchor, label], ...] }
  TQ.renderItem = (it) => {
    if (!it) return '<p class="panel-empty">Chưa có mô tả.</p>';
    const chips = (it.chips || []).map(([t, v]) => `<span class="chip${v ? ' chip--' + v : ''}">${esc(t)}</span>`).join('');
    const docs = (it.doc || []).map((d) => TQ.docLink(d[0], d[1], d[2])).join('');
    return (
      (it.eyebrow ? `<div class="p-eyebrow">${esc(it.eyebrow)}</div>` : '') +
      `<h3>${esc(it.title || '')}</h3>` +
      (chips ? `<div class="chips">${chips}</div>` : '') +
      (it.html || '') +
      (docs ? `<div class="doc-links">${docs}</div>` : '')
    );
  };

  const activate = (el, fn) => {
    el.addEventListener('click', fn);
    if (el.tagName !== 'BUTTON' && el.tagName !== 'A') {
      if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(e); }
      });
    }
  };

  // root chứa các [data-k] và một [data-panel]. opts: {initial, onShow(k)}
  TQ.explorer = (root, items, opts = {}) => {
    if (typeof root === 'string') root = document.querySelector(root);
    const panel = root.querySelector('[data-panel]');
    const nodes = [...root.querySelectorAll('[data-k]')];
    const show = (k) => {
      nodes.forEach((n) => {
        const on = n.dataset.k === k;
        n.classList.toggle('is-active', on);
        n.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      if (panel) panel.innerHTML = TQ.renderItem(items[k]);
      if (opts.onShow) opts.onShow(k);
    };
    nodes.forEach((n) => activate(n, () => show(n.dataset.k)));
    const first = opts.initial || (nodes[0] && nodes[0].dataset.k);
    if (first) show(first);
    return { show };
  };

  const inSpec = (spec, i) =>
    spec.split(',').some((part) => {
      part = part.trim();
      if (!part) return false;
      if (part.includes('-')) {
        const [a, b] = part.split('-');
        return i >= (a === '' ? 1 : +a) && i <= (b === '' ? Infinity : +b);
      }
      return +part === i;
    });

  // steps: [{title, text}] (đánh số từ 1). root chứa sơ đồ + [data-stepbar] + [data-caption].
  // opts: {onStep(i, step), autoplayMs}
  TQ.stepper = (root, steps, opts = {}) => {
    if (typeof root === 'string') root = document.querySelector(root);
    const bar = root.querySelector('[data-stepbar]');
    const cap = root.querySelector('[data-caption]');
    let i = 1, timer = null;
    bar.innerHTML =
      '<button class="btn" data-act="prev" aria-label="Bước trước">◀ Trước</button>' +
      '<button class="btn btn--primary" data-act="next" aria-label="Bước tiếp">Tiếp ▶</button>' +
      '<button class="btn" data-act="play" aria-label="Tự chạy">⏵ Tự chạy</button>' +
      '<span class="stepcount"></span><div class="dots"></div>';
    const dots = bar.querySelector('.dots');
    dots.innerHTML = steps.map((_, k) => `<button aria-label="Bước ${k + 1}"></button>`).join('');
    const count = bar.querySelector('.stepcount');
    const prev = bar.querySelector('[data-act=prev]');
    const next = bar.querySelector('[data-act=next]');
    const play = bar.querySelector('[data-act=play]');
    const go = (n) => {
      i = Math.max(1, Math.min(steps.length, n));
      root.querySelectorAll('[data-on]').forEach((el) => el.classList.toggle('off', !inSpec(el.dataset.on, i)));
      root.querySelectorAll('[data-hl]').forEach((el) => el.classList.toggle('hl', inSpec(el.dataset.hl, i)));
      const s = steps[i - 1];
      if (cap) cap.innerHTML = `<b>Bước ${i}/${steps.length} · ${esc(s.title || '')}</b><br>${s.text || ''}`;
      count.textContent = `${i} / ${steps.length}`;
      prev.disabled = i === 1;
      next.disabled = i === steps.length;
      [...dots.children].forEach((d, k) => d.classList.toggle('is-on', k < i));
      if (opts.onStep) opts.onStep(i, s);
    };
    const stop = () => { clearInterval(timer); timer = null; play.textContent = '⏵ Tự chạy'; play.classList.remove('is-on'); };
    prev.onclick = () => { stop(); go(i - 1); };
    next.onclick = () => { stop(); go(i + 1); };
    [...dots.children].forEach((d, k) => (d.onclick = () => { stop(); go(k + 1); }));
    play.onclick = () => {
      if (timer) return stop();
      if (i === steps.length) go(1);
      play.textContent = '⏸ Dừng'; play.classList.add('is-on');
      timer = setInterval(() => (i >= steps.length ? stop() : go(i + 1)), opts.autoplayMs || 2400);
    };
    go(1);
    return { go, get step() { return i; } };
  };

  TQ.tabs = (root, onChange) => {
    if (typeof root === 'string') root = document.querySelector(root);
    const btns = [...root.querySelectorAll('[data-tab]')];
    const panes = [...root.querySelectorAll('[data-pane]')];
    const show = (t) => {
      btns.forEach((b) => { const on = b.dataset.tab === t; b.classList.toggle('is-active', on); b.setAttribute('aria-selected', on); });
      panes.forEach((p) => (p.hidden = p.dataset.pane !== t));
      if (onChange) onChange(t);
    };
    btns.forEach((b) => b.addEventListener('click', () => show(b.dataset.tab)));
    if (btns[0]) show(btns[0].dataset.tab);
    return { show };
  };

  TQ.fmt = (n, d = 1) => Number(n).toLocaleString('vi-VN', { maximumFractionDigits: d, minimumFractionDigits: 0 });
  TQ.bytes = (b) => {
    const u = ['B', 'KB', 'MB', 'GB', 'TB'];
    let k = 0;
    while (b >= 1024 && k < u.length - 1) { b /= 1024; k++; }
    return TQ.fmt(b, b < 10 ? 2 : 1) + ' ' + u[k];
  };

  // nút copy cho mọi pre.code
  const addCopy = () =>
    document.querySelectorAll('pre.code').forEach((pre) => {
      if (pre.querySelector('.copy')) return;
      const b = document.createElement('button');
      b.className = 'copy'; b.type = 'button'; b.textContent = 'Copy';
      b.onclick = () => {
        const clone = pre.cloneNode(true);
        clone.querySelector('.copy').remove();
        const txt = clone.textContent.trim();
        const done = () => { b.textContent = 'Đã copy'; setTimeout(() => (b.textContent = 'Copy'), 1400); };
        if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, () => selectText(pre));
        else selectText(pre);
      };
      pre.appendChild(b);
    });
  const selectText = (el) => { const r = document.createRange(); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); };

  // điền [data-doclinks="frontier,nguyenly"] ở header
  const fillDocRow = () =>
    document.querySelectorAll('[data-doclinks]').forEach((el) => {
      el.innerHTML = el.dataset.doclinks.split(',').map((k) => TQ.docLink(k.trim(), '', 'Mở ' + TQ.DOCS[k.trim()].name)).join('');
    });

  // tô sáng mục hiện tại trên thanh .jump
  const spy = () => {
    const links = [...document.querySelectorAll('.jump a[href^="#"]')];
    if (!links.length || !('IntersectionObserver' in window)) return;
    const map = new Map(links.map((a) => [a.getAttribute('href').slice(1), a]));
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((a) => a.classList.remove('is-current'));
          const a = map.get(e.target.id);
          if (a) { a.classList.add('is-current'); a.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
        }
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    map.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
  };

  document.addEventListener('DOMContentLoaded', () => { addCopy(); fillDocRow(); spy(); });
})();
