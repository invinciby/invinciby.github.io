from pathlib import Path
import html, re, shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/Admin/Documents/1-code/wiki_exports_md_local_images')
OUT = ROOT / 'dist'
POSTS = OUT / 'essays'
if POSTS.exists(): shutil.rmtree(POSTS)
POSTS.mkdir(parents=True, exist_ok=True)

def inline(text):
    # Feishu occasionally leaves escape-only backslashes around line breaks.
    text = text.replace('\\', '')
    text = text.replace('<br/>', ' ').replace('<br>', ' ')
    text = html.escape(text, quote=False)
    text = re.sub(r'!\[([^]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noreferrer">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text

def render_md(raw):
    # Feishu exports contain a few presentation-only tags. Keep their text,
    # but remove the tags so they never leak into the published article.
    raw = re.sub(r'<title[^>]*>.*?</title>', '', raw, flags=re.I | re.S)
    raw = re.sub(r'</?(?:callout|sheet|colgroup|col|tbody|thead)[^>]*>', '', raw, flags=re.I)
    lines = raw.replace('\r\n', '\n').split('\n')
    out, para, list_tag, in_code = [], [], None, False
    table_open, table_header = False, False

    def flush_para():
        nonlocal para
        if para:
            out.append('<p>' + inline(' '.join(x.strip() for x in para)) + '</p>')
            para = []

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f'</{list_tag}>')
            list_tag = None

    def close_table():
        nonlocal table_open
        if table_open:
            out.append('</tbody></table>')
            table_open = False

    for line in lines:
        s = line.strip()
        if in_code:
            if s.startswith('```'):
                out.append('</code></pre>')
                in_code = False
            else:
                out.append(html.escape(line, quote=False))
            continue
        if not s:
            flush_para(); close_list(); close_table(); continue
        if s.startswith('```'):
            flush_para(); close_list(); close_table(); out.append('<pre><code>'); in_code = True; continue
        # Raw HTML tables from Feishu are safe structural markup; strip
        # attributes but preserve the table cells and row structure.
        if re.match(r'^</?(?:table|tr|th|td)(?:\s|>)', s, re.I):
            flush_para(); close_list(); close_table()
            clean = re.sub(r'\s+(?:vertical-align|rowspan|colspan|style|class)="[^"]*"', '', s, flags=re.I)
            out.append(clean)
            continue
        # Markdown tables: separator rows are skipped and the first row is
        # promoted to a header for readable article typography.
        if '|' in s and s.startswith('|') and s.endswith('|'):
            flush_para(); close_list()
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(re.match(r'^:?-{1,}:?$', c) for c in cells):
                table_header = True
                continue
            if not table_open:
                out.append('<table><thead><tr>')
                out.extend(f'<th>{inline(c)}</th>' for c in cells)
                out.append('</tr></thead><tbody>')
                table_open = True
                continue
            tag = 'td'
            out.append('<tr>')
            out.extend(f'<{tag}>{inline(c)}</{tag}>' for c in cells)
            out.append('</tr>')
            continue
        m = re.match(r'^(#{1,6})\s+(.+)$', s)
        if m:
            flush_para(); close_list(); close_table(); level = min(len(m.group(1)) + 1, 6)
            out.append(f'<h{level}>{inline(m.group(2))}</h{level}>'); continue
        if re.match(r'^[-*_]{3,}$', s):
            flush_para(); close_list(); close_table(); out.append('<hr>'); continue
        if s.startswith('>'):
            flush_para(); close_list(); close_table(); out.append(f'<blockquote>{inline(s[1:].strip())}</blockquote>'); continue
        list_match = re.match(r'^([-*+]\s+|\d+[.)]\s+)(.+)$', s)
        if list_match:
            flush_para(); close_table()
            wanted = 'ol' if re.match(r'^\d', list_match.group(1)) else 'ul'
            if list_tag != wanted:
                close_list(); out.append(f'<{wanted}>'); list_tag = wanted
            out.append('<li>' + inline(list_match.group(2)) + '</li>'); continue
        close_list(); close_table(); para.append(s)
    flush_para(); close_list(); close_table()
    if in_code: out.append('</code></pre>')
    return '\n'.join(out)

def title_from(raw, filename):
    title_tag = re.search(r'<title[^>]*>(.*?)</title>', raw, flags=re.I | re.S)
    if title_tag:
        candidate = re.sub(r'<[^>]+>', ' ', title_tag.group(1))
        return re.sub(r'\s+', ' ', candidate).strip()
    for line in raw.splitlines():
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            candidate = m.group(1)
            if '<title' in candidate.lower():
                return filename.rsplit('.', 1)[0]
            candidate = re.sub(r'<[^>]+>', ' ', candidate)
            return re.sub(r'\s+', ' ', re.sub(r'[*_`]', '', candidate)).strip()
    return filename.rsplit('.', 1)[0]

def category(title):
    if any(x in title for x in ('材料', '化学', '催化', '分子', '聚合物', '电池', '晶体')): return ('AI × MATERIALS', 'materials')
    if any(x in title for x in ('Agent', '智能体', '大模型', 'LLM', 'GPT', 'DeepSeek', 'RAG')): return ('AI × RESEARCH', 'agents')
    if any(x in title for x in ('数据', '信息抽取', '基准', '评估', '推理')): return ('METHODS & EVALUATION', 'methods')
    return ('RESEARCH NOTE', 'notes')

def strip_md(raw):
    text = re.sub(r'```.*?```', '', raw, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'!\[[^]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'\[[^]]+\]\([^)]*\)', ' ', text)
    text = re.sub(r'[#>*_`|()]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

files = sorted(SOURCE.glob('*.md'), key=lambda p: p.name)
articles = []
for i, path in enumerate(files, 1):
    raw = path.read_text(encoding='utf-8', errors='ignore')
    title = title_from(raw, path.name)
    plain = strip_md(raw)
    excerpt = (plain[:190] + '…') if len(plain) > 190 else plain
    words = max(1, len(plain) // 2)
    minutes = max(3, round(words / 280))
    category_label, category_slug = category(title)
    slug = f'{i:03d}-article'
    folder = POSTS / category_slug / slug
    folder.mkdir(parents=True, exist_ok=True)
    raw_body = re.sub(r'^\s*#\s+.*\n', '', raw, count=1)
    body = render_md(raw_body).replace('src="assets/', 'src="../../../article-assets/')
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜你好不吃虾</title><meta name="description" content="{html.escape(excerpt[:150])}"><link rel="stylesheet" href="../../../css/index.css"></head><body><div class="site-shell"><header class="topbar"><a class="brand" href="../../../index.html"><span class="brand-mark">虾</span><span>你好不吃虾</span></a><nav class="nav"><a href="../../../about/">关于</a><a href="../../index.html">文章</a><a href="../../../research/">研究</a><a href="../../../contact/">联系</a></nav><a class="nav-cta" href="../../index.html">文章 ↗</a></header><main class="article-page"><a class="back-link" href="../../index.html">← 返回文章列表</a><div class="article-meta"><span>{category_label}</span><span>{minutes} MIN READ</span></div><h1>{html.escape(title)}</h1><p class="article-lede">{html.escape(excerpt)}</p><div class="article-layout"><article class="article-body">{body}</article><aside><div class="aside-card"><span class="section-kicker">ABOUT THIS NOTE</span><p>这是「你好不吃虾」的 AI for Science 研究笔记，记录论文、方法与可复用的科研工作流。</p><a href="../../index.html">更多文章 ↗</a></div></aside></div></main><footer><span>你好不吃虾 · AI for Science</span><span>研究、构建、验证</span></footer></div></body></html>'''
    (folder / 'index.html').write_text(page, encoding='utf-8')
    articles.append({'title': title, 'excerpt': excerpt, 'slug': slug, 'category': category_label, 'category_slug': category_slug, 'minutes': minutes})

if (OUT / 'article-assets').exists(): shutil.rmtree(OUT / 'article-assets')
shutil.copytree(SOURCE / 'assets', OUT / 'article-assets')
cards = ''.join(f'<a class="essay-row" href="{a["category_slug"]}/{a["slug"]}/"><span class="essay-number">{i:02d}</span><div><span class="essay-category">{a["category"]}</span><h3>{html.escape(a["title"])}</h3><p>{html.escape(a["excerpt"])}</p></div><span class="essay-time">{a["minutes"]} min ↗</span></a>' for i, a in enumerate(articles, 1))
filters = '<div class="essay-filters"><a href="index.html">全部</a><a href="materials/">AI × Materials</a><a href="agents/">AI × Research</a><a href="methods/">Methods</a><a href="notes/">Research Notes</a></div>'
index = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>文章｜你好不吃虾</title><link rel="stylesheet" href="../css/index.css"></head><body><div class="site-shell"><header class="topbar"><a class="brand" href="../index.html"><span class="brand-mark">虾</span><span>你好不吃虾</span></a><nav class="nav"><a href="../about/">关于</a><a href="index.html">文章</a><a href="../research/">研究</a><a href="../contact/">联系</a></nav><a class="nav-cta" href="index.html">文章 ↗</a></header><main class="essays-page"><p class="section-kicker">04 / ESSAYS &amp; FIELD NOTES</p><h1>把读过的东西，<br><span>变成自己的地图。</span></h1><p class="essays-intro">这里收录「你好不吃虾」关于 AI for Science 的文章、论文解读与研究笔记。按主题持续更新。</p>{filters}<div class="essay-list">{cards}</div></main><footer><span>你好不吃虾 · {len(articles)} 篇文章</span><a href="../index.html">回到首页 ↑</a></footer></div></body></html>'''
(POSTS / 'index.html').write_text(index, encoding='utf-8')

category_names = {'materials': 'AI × MATERIALS', 'agents': 'AI × RESEARCH', 'methods': 'METHODS & EVALUATION', 'notes': 'RESEARCH NOTES'}
for cat, label in category_names.items():
    subset = [a for a in articles if a['category_slug'] == cat]
    cat_cards = ''.join(f'<a class="essay-row" href="{a["slug"]}/"><span class="essay-number">{i:02d}</span><div><span class="essay-category">{a["category"]}</span><h3>{html.escape(a["title"])}</h3><p>{html.escape(a["excerpt"])}</p></div><span class="essay-time">{a["minutes"]} min ↗</span></a>' for i, a in enumerate(subset, 1))
    cat_page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{label}｜文章｜你好不吃虾</title><link rel="stylesheet" href="../../css/index.css"></head><body><div class="site-shell"><header class="topbar"><a class="brand" href="../../index.html"><span>你好不吃虾</span></a><nav class="nav"><a href="../../about/">关于</a><a href="../index.html">文章</a><a href="../../research/">研究</a><a href="../../contact/">联系</a></nav><a class="nav-cta" href="../index.html">文章 ↗</a></header><main class="essays-page"><a class="back-link" href="../index.html">← 全部文章</a><p class="section-kicker">{label}</p><h1>这一类文章，<br><span>集中讨论什么。</span></h1><div class="essay-list">{cat_cards}</div></main><footer><span>你好不吃虾 · {len(subset)} 篇</span><a href="../index.html">回到文章列表 ↑</a></footer></div></body></html>'''
    cat_folder = POSTS / cat
    cat_folder.mkdir(parents=True, exist_ok=True)
    (cat_folder / 'index.html').write_text(cat_page, encoding='utf-8')

for target in (ROOT / 'index.html', OUT / 'index.html'):
    if target.exists():
        text = target.read_text(encoding='utf-8')
        text = re.sub(r'href="https://mp.weixin.qq.com/"', 'href="essays/"', text)
        text = re.sub(r'去公众号阅读全部', '阅读全部文章', text)
        text = text.replace('AI for Science 到底在改变什么？', articles[0]['title'])
        text = text.replace('把知识库做成第二大脑之前', articles[1]['title'])
        text = text.replace('从“帮我总结论文”走向“帮我提出下一个可验证的问题”，科研工作流的重心正在移动。', articles[0]['excerpt'])
        text = text.replace('先别急着堆工具。真正重要的是，决定哪些信息值得被留下，以及如何再次找到它。', articles[1]['excerpt'])
        text = text.replace('href="#notes"', 'href="essays/"')
        text = text.replace('href="essays/" target="_blank" rel="noreferrer">阅读文章', 'href="essays/001-article/" target="_blank" rel="noreferrer">阅读文章', 1)
        text = text.replace('href="essays/" target="_blank" rel="noreferrer">阅读文章', 'href="essays/002-article/" target="_blank" rel="noreferrer">阅读文章', 1)
        text = text.replace('href="essays/" target="_blank" rel="noreferrer"', 'href="essays/"')
        text = text.replace('href="essays/001-article/" target="_blank" rel="noreferrer"', 'href="essays/001-article/"')
        text = text.replace('href="essays/002-article/" target="_blank" rel="noreferrer"', 'href="essays/002-article/"')
        target.write_text(text, encoding='utf-8')

# GitHub Pages for this repository publishes from the repository root. Keep
# the dist build for local/portable previews, and mirror the generated article
# library into the root so /essays/ exists on the live site. Root pages reuse
# the already-published dist assets instead of committing a second 66 MB copy.
root_posts = ROOT / 'essays'
if root_posts.exists():
    shutil.rmtree(root_posts)
shutil.copytree(POSTS, root_posts)
for page in root_posts.rglob('*.html'):
    page_html = page.read_text(encoding='utf-8')
    page.write_text(
        page_html.replace('../../../article-assets/', '../../../dist/article-assets/'),
        encoding='utf-8',
    )

print(f'generated {len(articles)} articles')
