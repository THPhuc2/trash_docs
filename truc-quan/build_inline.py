#!/usr/bin/env python3
"""Chèn các hình trực quan vào thẳng tài liệu gốc, ngay tại mục mà hình minh hoạ.

Nguồn: các trang *.html trong thư mục này (mỗi hình là một <section class="viz" id="...">).
Đích: research_docs_knowleadge/*.html. Chạy lại bao nhiêu lần cũng được: khối cũ (giữa các
dấu <!--TQ:...-->) bị gỡ ra trước rồi mới chèn lại. Lần đầu sao lưu bản gốc vào
trash_docs/backup-truoc-chen-hinh/.

    python3 build_inline.py            # chèn / cập nhật
    python3 build_inline.py --remove   # gỡ hết hình, trả tài liệu về như cũ
"""
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCDIR = HERE.parent.parent / 'research_docs_knowleadge'
BACKUP = HERE.parent / 'backup-truoc-chen-hinh'

PAGE_LABEL = {
    'frontier-training': 'Frontier', 'transformer': 'Transformer', 'vlm-training': 'VLM',
    'inference-deploy': 'Inference', 'training-recipes': 'Recipes',
}

# (id hình, cách đặt, anchor trong tài liệu[, chữ đầu của h4])
#   'end'       → cuối mục: ngay trước h2/h3 kế tiếp sau heading có id = anchor
#   'before_h4' → ngay trước <h4> đầu tiên (bỏ số thứ tự) bắt đầu bằng một trong các chữ cho trước, trong mục anchor
FRONTIER = [
    ('transformer', [
        ('tx-train', 'end', 't-lm-objective'),
        ('tx-overview', 'before_h4', 't-transformer-math', ('Embedding', 'Residual stream')),
        ('tx-attn', 'before_h4', 't-transformer-math', 'FFN SwiGLU'),
        ('tx-ffn', 'before_h4', 't-transformer-math', 'LM head'),
        ('tx-params', 'end', 't-param-count'),
        ('tx-infer', 'end', 'ar-kv-inference'),
    ]),
    ('frontier-training', [
        ('h-lifecycle', 'end', 'a-playbook-h'),
        ('h-memory', 'end', 't-memory-anatomy'),
        ('h-roof', 'end', 't-roofline'),
        ('h-attn', 'end', 'a-attention'),
        ('h-stab', 'end', 'b-stability-h'),
        ('h-lr', 'end', 'c-learning-rates'),
        ('h-scale', 'end', 'c-scaling-laws'),
        ('h-grpo', 'end', 'e-rl'),
        ('h-par', 'end', 's-5d-parallelism'),
    ]),
]
PLAN = {
    'frontier-model-training-vi.html': FRONTIER,
    'frontier-model-training-vi-nguyen-ly.html': FRONTIER,
    'vlm-training-vi.html': [
        ('vlm-training', [
            ('s-journey', 'end', 'v-three-blocks'),
            ('s-families', 'end', 'v-families'),
            ('s-contrastive', 'end', 'v-siglip'),
            ('s-connector', 'end', 'v-connectors-h'),
            ('s-tokens', 'end', 'v-high-res'),
            ('s-stages', 'end', 'v2-stage-overview'),
            ('s-mask', 'end', 'v2-loss-masking'),
            ('s-data', 'end', 'v-data-h'),
            ('s-post', 'end', 'v-post-h'),
            ('s-systems', 'end', 'v-systems-h'),
            ('s-eval', 'end', 'v-eval-h'),
            ('s-recipe', 'end', 'v3-recipe'),
        ]),
    ],
    'inference-deploy-vi.html': [
        ('transformer', [('tx-infer', 'end', 'i-gen-loop')]),
        ('inference-deploy', [
            ('f-journey', 'end', 'i-prefill-decode'),
            ('f-kv', 'end', 'i-kv-size'),
            ('f-batch', 'end', 'i-batching-theory'),
            ('f-cb', 'end', 'i-batching'),
            ('f-paged', 'end', 'i-paged'),
            ('f-chunk', 'end', 'i-disagg'),
            ('f-spec', 'end', 'i-spec-algo'),
            ('f-quant', 'end', 'i2-opt-choose'),
            ('f-compress', 'end', 'i2-opt-decision'),
            ('f-size', 'end', 'i3-cost'),
            ('f-check', 'end', 'i3-checklist'),
            ('f-ladder', 'end', 'i3-decision-order'),
        ]),
    ],
    'training-recipes-cam-nang.html': [
        ('training-recipes', [
            ('f-metro', 'end', 'a-guide-h'),
            ('f-logs', 'end', 'a-read-logs'),
            ('f-ops', 'end', 'a-guide-update-safety'),
            ('f-env', 'end', 'a-env-why'),
            ('f-data', 'end', 'b-r00-configs'),
            ('f-split', 'end', 'b-r00-split'),
            ('f-choose', 'end', 'c-decision-tree'),
            ('f-oom', 'end', 'f-tr-oom'),
            ('f-par', 'end', 'g-choose'),
            ('f-eval', 'end', 'j-r11-flow'),
            ('f-ci', 'end', 'j-d15-accept'),
            ('f-budget', 'end', 'k-gpu-budget-py'),
            ('f-share', 'end', 'k-sharing-table'),
        ]),
    ],
}

EMBED_CSS = """
.tq{container-type:inline-size;container-name:tq;font-size:15.5px;line-height:1.65;margin:30px 0;
  border:1px solid var(--border);border-radius:14px;background:var(--bg);padding:2px 16px 18px}
.tq>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;padding:10px 0 2px;
  font:600 11.5px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.tq>summary::-webkit-details-marker{display:none}
.tq>summary::before{content:"▾";font-size:13px;transition:transform .2s}
.tq>summary .tq-hide{margin-left:auto;font-weight:500;color:var(--muted);text-transform:none;letter-spacing:0}
.tq:not([open]){padding-bottom:6px}
.tq:not([open])>summary::before{transform:rotate(-90deg)}
.tq:not([open])>summary .tq-hide{display:none}
.tq h1,.tq h2,.tq h3,.tq h4,.tq h5{border:0;padding:0;margin:0;color:inherit}
.tq p,.tq ul,.tq ol,.tq li,.tq figure,.tq .callout{margin:0}
.tq table{display:table;margin:0;font-size:inherit}
.tq th,.tq td{border:0;border-bottom:1px solid var(--border)}
.tq thead th,.tq tbody tr:nth-child(n){background:none}
.tq pre{border:0}
.tq svg{margin:0}
.tq .viz{padding-top:6px}
.tq .viz-head h4.tq-title{font-size:clamp(19px,2.4vw,23px);font-weight:700;letter-spacing:-.01em}
.tq [hidden]{display:none!important}
"""

DROP = ('html', 'body', '.wrap', '.top', '.jump', '.foot', '.crumb', '.doc-row')


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def match_brace(s, i):
    """s[i] == '{' → vị trí '}' khớp."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return j
    raise ValueError('CSS thiếu dấu }')


def split_top(sel):
    parts, depth, cur = [], 0, ''
    for ch in sel:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def scope_sel(sel):
    out = []
    for p in split_top(sel):
        if p.startswith(':root'):
            out.append(p)
        elif any(p == d or p.startswith(d + ' ') or p.startswith(d + ':') or p.startswith(d + '.')
                 or p.startswith(d + '>') or p.startswith(d + '[') or p.startswith(d + '::') for d in DROP):
            continue
        else:
            out.append('.tq ' + p)
    return ','.join(out)


def scope_css(css):
    css = strip_comments(css)
    out, i = [], 0
    while True:
        j = css.find('{', i)
        if j < 0:
            break
        head = css[i:j].strip()
        k = match_brace(css, j)
        body = css[j + 1:k]
        if head.startswith('@media') or head.startswith('@supports'):
            inner = scope_css(body)
            if re.search(r'\((max|min)-width', head) and 'prefers' not in head:
                head = head.replace('@media', '@container tq', 1)
            if inner.strip():
                out.append(f'{head}{{{inner}}}')
        elif head.startswith('@'):
            out.append(f'{head}{{{body}}}')
        else:
            sel = scope_sel(head)
            if sel:
                out.append(f'{sel}{{{body}}}')
        i = k + 1
    return '\n'.join(out)


def sections_of(page_html):
    """id → outer HTML của <section class="viz" id=...>"""
    res = {}
    for m in re.finditer(r'<section class="viz"[^>]*\bid="([^"]+)"', page_html):
        start, depth, pos = m.start(), 0, m.start()
        for t in re.finditer(r'<(/?)section\b', page_html[start:]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                end = start + t.start()
                end = page_html.index('>', end) + 1
                break
        res[m.group(1)] = page_html[start:end]
    return res


def page_parts(name):
    html = (HERE / f'{name}.html').read_text(encoding='utf-8')
    styles = re.findall(r'<style>(.*?)</style>', html, flags=re.S)
    scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.S)
    return sections_of(html), '\n'.join(styles), scripts[-1]


def adapt_section(name, sid, sec):
    sec = re.sub(r'<h2\b', '<h4 class="tq-title"', sec).replace('</h2>', '</h4>')
    sec = re.sub(r'<span class="fig">Hình (\d+)', lambda m: f'<span class="fig">{PAGE_LABEL[name]} {m.group(1)}', sec)
    title = re.search(r'<h4 class="tq-title"[^>]*>(.*?)</h4>', sec, flags=re.S)
    plain = re.sub(r'<[^>]+>', '', title.group(1)).strip() if title else sid
    return (f'<!--TQ:BEGIN {name}#{sid}--><details class="tq tex2jax_ignore" open>'
            f'<summary>Hình trực quan<span class="tq-hide">bấm để thu gọn</span></summary>\n{sec}\n</details><!--TQ:END-->'), plain


def remove_old(doc):
    doc = re.sub(r'<!--TQ:BEGIN .*?<!--TQ:END-->\n?', '', doc, flags=re.S)
    doc = re.sub(r'<!--TQ:STYLE-->.*?<!--/TQ:STYLE-->\n?', '', doc, flags=re.S)
    doc = re.sub(r'<!--TQ:SCRIPT-->.*?<!--/TQ:SCRIPT-->\n?', '', doc, flags=re.S)
    return doc


def insert_pos(doc, mode, anchor, h4=None):
    m = re.search(rf'<h[23][^>]*\bid="{re.escape(anchor)}"', doc)
    if not m:
        raise SystemExit(f'không thấy mục #{anchor}')
    after = doc.index('>', m.end()) + 1
    nxt = re.compile(r'<h[23][\s>]').search(doc, after)
    sec_end = nxt.start() if nxt else doc.index('</main>')
    if mode == 'end':
        return sec_end
    wanted = (h4,) if isinstance(h4, str) else h4
    for h in re.finditer(r'<h4\b[^>]*>(.*?)</h4>', doc[after:sec_end], flags=re.S):
        text = re.sub(r'^\d+\.\s*', '', re.sub(r'<[^>]+>', '', h.group(1)).strip())
        if any(text.startswith(w) for w in wanted):
            return after + h.start()
    raise SystemExit(f'không thấy h4 "{h4}" trong #{anchor}')


def build(remove_only=False):
    BACKUP.mkdir(exist_ok=True)
    shared_css = (HERE / 'shared.css').read_text(encoding='utf-8')
    shared_js = (HERE / 'shared.js').read_text(encoding='utf-8')
    for docname, groups in PLAN.items():
        path = DOCDIR / docname
        if not (BACKUP / docname).exists():
            shutil.copy2(path, BACKUP / docname)
        doc = remove_old(path.read_text(encoding='utf-8'))
        if remove_only:
            path.write_text(doc, encoding='utf-8')
            print(f'{docname}: đã gỡ hình')
            continue
        css, js, inserts, n = [scope_css(shared_css)], [], [], 0
        for name, places in groups:
            secs, page_css, page_js = page_parts(name)
            css.append(scope_css(page_css))
            js.append(f'/* {name} */\n(function(){{\n{page_js}\n}})();')
            for spec in places:
                sid, mode, anchor = spec[:3]
                block, _ = adapt_section(name, sid, secs[sid])
                inserts.append((insert_pos(doc, mode, anchor, spec[3] if len(spec) > 3 else None), n, block))
                n += 1
        # chèn từ cuối lên để vị trí không bị lệch; cùng vị trí thì giữ thứ tự khai báo
        for pos, _, block in sorted(inserts, key=lambda x: (x[0], x[1]), reverse=True):
            doc = doc[:pos] + block + '\n' + doc[pos:]
        style = '<!--TQ:STYLE--><style>\n' + '\n'.join(css) + EMBED_CSS + '</style><!--/TQ:STYLE-->\n'
        doc = doc.replace('</head>', style + '</head>', 1)
        script = ('<!--TQ:SCRIPT--><script>window.TQ_EMBED={file:' + repr(docname) + '};</script>\n<script>\n'
                  + shared_js + '\n' + '\n'.join(js) + '\n</script><!--/TQ:SCRIPT-->\n')
        doc = doc.replace('</body>', script + '</body>', 1)
        path.write_text(doc, encoding='utf-8')
        print(f'{docname}: chèn {n} hình')


if __name__ == '__main__':
    build(remove_only='--remove' in sys.argv)
