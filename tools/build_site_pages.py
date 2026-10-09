from pathlib import Path
import html, re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/Admin/Documents/1-code/wiki_exports_md_local_images')

def title_of(raw, name):
    for line in raw.splitlines():
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            candidate = m.group(1)
            if '<title' in candidate.lower(): return name.rsplit('.', 1)[0]
            candidate = re.sub(r'<[^>]+>', ' ', candidate)
            return re.sub(r'\s+', ' ', re.sub(r'[*_`]', '', candidate)).strip()
    return name.rsplit('.', 1)[0]

def excerpt(raw):
    s = re.sub(r'[#>*_`\[\]()]', ' ', raw)
    s = re.sub(r'\s+', ' ', s).strip()
    return (s[:170] + '…') if len(s) > 170 else s

def category_slug(title):
    if any(x in title for x in ('材料', '化学', '催化', '分子', '聚合物', '电池', '晶体')): return 'materials'
    if any(x in title for x in ('Agent', '智能体', '大模型', 'LLM', 'GPT', 'DeepSeek', 'RAG')): return 'agents'
    if any(x in title for x in ('数据', '信息抽取', '基准', '评估', '推理')): return 'methods'
    return 'notes'

files = sorted(SOURCE.glob('*.md'), key=lambda p: p.name)
latest = []
for i, p in enumerate(files[:3], 1):
    raw = p.read_text(encoding='utf-8', errors='ignore')
    latest.append((category_slug(title_of(raw, p.name)), f'{i:03d}-article', title_of(raw, p.name), excerpt(raw)))

nav = '<nav class="nav"><a href="{p}about/">关于</a><a href="{p}essays/">文章</a><a href="{p}projects/">项目</a><a href="{p}research/">研究</a><a href="{p}contact/">联系</a></nav>'

def header(prefix=''):
    return f'<header class="topbar"><a class="brand" href="{prefix}index.html"><span class="brand-mark">虾</span><span>你好不吃虾</span></a>{nav.format(p=prefix)}<a class="nav-cta" href="{prefix}essays/">文章 ↗</a></header>'

def footer(prefix=''):
    return f'<footer><span>你好不吃虾 · AI for Science</span><span>研究、构建、验证</span><div class="footer-links"><a href="{prefix}contact/">联系 ↗</a><a href="{prefix}index.html#top">回到顶部 ↑</a></div></footer>'

def page(title, body, prefix=''):
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜你好不吃虾</title><meta name="description" content="你好不吃虾：AI for Science 个人主站"><link rel="stylesheet" href="{prefix}css/index.css"></head><body><div class="site-shell">{header(prefix)}{body}{footer(prefix)}</div></body></html>'

def write_route(route, title, body):
    folder = ROOT / route
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'index.html').write_text(page(title, body, '../' if route else ''), encoding='utf-8')

hero = '''<section class="hero" id="top"><div class="hero-copy"><p class="eyebrow"><span class="dot"></span> AI FOR SCIENCE · PERSONAL NOTES</p><h1>你好，<br><em>我是Vinci。</em></h1><p class="hero-lede">我在这里记录自己如何用 AI 读论文、整理知识、做研究，也分享一路上真正有用的工具和想法。</p><div class="hero-actions"><a class="button button-dark" href="about/">认识我 <span>↗</span></a><a class="text-link" href="essays/">看看文章 <span>↗</span></a></div></div><div class="hero-art hero-art-image"><img src="assets/ai-for-science-square.png" alt="AI for Science 工作流示意图"></div></section>'''
latest_cards = ''.join(f'<a class="home-essay" href="essays/{cat}/{slug}/"><span class="essay-category">FIELD NOTE / {i:02d}</span><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><span class="home-essay-arrow">阅读文章 ↗</span></a>' for i, (cat, slug, title, desc) in enumerate(latest, 1))
project_preview = '<section class="home-project-section"><div class="home-project-heading"><div><p class="section-kicker">02 / PERSONAL PROJECTS</p><h2>最近在做<br><span>什么。</span></h2></div><a class="outline-button" href="projects/">查看全部项目 ↗</a></div><div class="home-project-grid"><a class="home-project-card easy" href="projects/"><span>01 / KNOWLEDGE PRODUCT</span><h3>EasyToPPT</h3><p>把论文、研究笔记与复杂知识，整理成结构清晰、适合表达的演示内容。</p><b>EXPLORE ↗</b></a><a class="home-project-card agent" href="projects/"><span>02 / RESEARCH AGENT</span><h3>自动化科研智能体</h3><p>探索从文献检索、阅读理解到知识整理与研究写作的自动化科研工作流。</p><b>EXPLORE ↗</b></a></div></section>'
home_body = f'<main id="top">{hero}<section class="home-strip"><div><p class="section-kicker">01 / THE LATEST</p><h2>最近在写<br><span>什么。</span></h2></div><a class="outline-button" href="essays/">查看全部文章 ↗</a></section><section class="home-essays">{latest_cards}</section>{project_preview}<section class="home-cta"><div><p class="section-kicker">03 / KEEP EXPLORING</p><h2>从一个问题<br><span>开始。</span></h2></div><div><p>看看我正在关注的研究线索、工具和实验。</p><a class="button button-dark" href="research/">查看研究 ↗</a></div></section></main>'
(ROOT / 'index.html').write_text(page('你好不吃虾', home_body), encoding='utf-8')

pages = {
 'about': ('关于', '<main class="subpage about-page"><section class="sub-hero"><div><p class="section-kicker">ABOUT / VINCI</p><h1>我是 Vinci，<br><span>也是「你好不吃虾」。</span></h1><p class="sub-lede">一个持续学习 AI for Science 的研究者与内容创作者。我喜欢把读过的论文、试过的工具和想明白的问题，整理成下一次还能用的东西。</p></div><div class="identity-orbit"><span>READ</span><span>BUILD</span><span>VERIFY</span><strong>V</strong></div></section><section class="signal-grid"><article class="signal-card green"><span>01 / CURIOSITY</span><h2>我在关注什么</h2><p>科学大模型、科研 Agent、材料与化学智能、文献理解，以及知识如何真正进入研究决策。</p></article><article class="signal-card orange"><span>02 / PRACTICE</span><h2>我在做什么</h2><p>阅读、拆解、复现、写作。把复杂方法翻译成图、文章、代码和能继续迭代的工作流。</p></article><article class="signal-card blue"><span>03 / BELIEF</span><h2>我相信什么</h2><p>好工具应该扩大人的判断力。比“看起来聪明”更重要的，是结果可验证、过程可追踪。</p></article></section><section class="quote-panel"><p>“这里不是答案仓库，而是一份持续更新的个人研究现场。”</p><a href="../essays/">从文章开始认识我 ↗</a></section></main>'),
 'directions': ('方向', '<main class="subpage"><p class="section-kicker">DIRECTIONS / 研究方向</p><h1>从模型到工作流，<br><span>把 AI 放进科学问题里。</span></h1><p class="sub-lede">不追逐“万能工具”，只记录那些能被复现、验证和继续推进的交叉实践。</p><div class="large-grid"><article><span>01 / AI FOR SCIENCE</span><h2>科学发现</h2><p>关注文献理解、知识抽取、实验设计、材料发现与科研 Agent，探索模型如何成为科学家的协作者。</p></article><article><span>02 / RESEARCH WORKFLOW</span><h2>科研工作流</h2><p>把搜索、阅读、整理、写作和复现实验串成一条透明、可复用的链路。</p></article><article><span>03 / KNOWLEDGE PRODUCTS</span><h2>知识产品</h2><p>把个人研究沉淀为内容、模板和小工具，让一次阅读变成下一次行动的起点。</p></article></div></main>'),
 'projects': ('项目', '<main class="subpage projects-page"><section class="projects-hero"><div><p class="section-kicker">PROJECTS / PERSONAL LAB</p><h1>把想法做成<br><span>可以使用的东西。</span></h1><p class="sub-lede">这里放置我正在构建的个人项目。它们从真实的学习与科研问题出发，持续迭代，而不是一次性的概念展示。</p></div><div class="project-console"><span>VINCI / PROJECT LOG</span><div><i></i><i></i><i></i></div><strong>BUILD<br>TEST<br>REFINE</strong><small>02 ACTIVE PROJECTS</small></div></section><section class="project-showcase"><article class="project-feature easy"><div class="project-index"><span>01</span><em>KNOWLEDGE PRODUCT</em></div><div class="project-copy"><h2>EasyToPPT</h2><p>把论文、研究笔记与复杂知识转化为结构清晰的演示内容，减少整理素材和搭建叙事框架的重复工作。</p><ul><li>研究内容结构化</li><li>演示叙事与页面规划</li><li>面向科研表达的内容工作流</li></ul></div><div class="project-status"><span>STATUS</span><b>持续迭代中</b></div></article><article class="project-feature agent"><div class="project-index"><span>02</span><em>RESEARCH AGENT</em></div><div class="project-copy"><h2>自动化科研智能体</h2><p>探索如何让智能体参与文献检索、论文理解、知识整理和研究写作，形成可追踪、可验证的科研协作流程。</p><ul><li>检索与论文阅读</li><li>结构化知识沉淀</li><li>任务规划、执行与验证</li></ul></div><div class="project-status"><span>STATUS</span><b>研究与开发中</b></div></article></section><section class="project-next"><span>NEXT / MORE TO COME</span><p>新的工具与实验，会继续在这里出现。</p><a href="../contact/">聊聊项目与合作 ↗</a></section></main>'),
 'research': ('研究', '<main class="subpage research-page"><section class="sub-hero"><div><p class="section-kicker">RESEARCH / LIVE MAP</p><h1>我正在追踪的<br><span>研究坐标。</span></h1><p class="sub-lede">不是一份静态成果清单，而是我持续更新的问题、方法和实验路径。</p></div><div class="research-radar"><i></i><i></i><i></i><b>AI × SCI</b></div></section><section class="research-track"><article><span class="track-no">01</span><div><small>KNOWLEDGE</small><h2>文献 → 结构化知识</h2><p>从论文中提取实体、关系、实验条件与证据链，让知识能够被检索、比较和复用。</p></div><em>READ / PARSE / LINK</em></article><article><span class="track-no">02</span><div><small>AGENTS</small><h2>模型 → 科研 Agent</h2><p>研究检索、规划、工具调用、验证和人机协作如何组成真正可用的科研系统。</p></div><em>PLAN / ACT / REFLECT</em></article><article><span class="track-no">03</span><div><small>DISCOVERY</small><h2>知识 → 下一次实验</h2><p>让研究记录成为下一次假设与实验的上下文，而不是读完即消失的信息。</p></div><em>QUESTION / TEST / LEARN</em></article></section><section class="research-footer-panel"><div><span>OPEN NOTEBOOK</span><h2>研究仍在发生。</h2></div><a class="button button-light" href="../essays/">查看研究笔记 ↗</a></section></main>'),
 'collaborate': ('合作', '<main class="subpage"><p class="section-kicker">COLLABORATE / 合作</p><h1>一起把一个想法，<br><span>做成可以验证的东西。</span></h1><p class="sub-lede">欢迎围绕 AI for Science 内容共创、科研工具、知识库与研究工作流展开合作。</p><div class="collab-grid"><article><span>CONTENT</span><h2>内容共创</h2><p>论文解读、专题策划、研究趋势与复杂技术的通俗表达。</p></article><article><span>TOOLS</span><h2>工具与工作流</h2><p>面向科研团队的检索、阅读、整理和知识复用系统。</p></article><article><span>PILOT</span><h2>研究试点</h2><p>把一个值得验证的 AI for Science 想法推进到原型。</p></article></div><a class="button button-dark" href="../contact/">联系我 ↗</a></main>'),
 'contact': ('联系', '<main class="subpage contact-page"><section class="contact-hero"><p class="section-kicker">CONTACT / SAY HELLO</p><h1>如果你也在探索<br><span>AI 与科学的交界。</span></h1><p class="sub-lede">无论是一个尚未成形的问题、一篇值得讨论的论文，还是一个想做出来的科研工具，都欢迎来聊聊。</p><div class="contact-channels"><a class="contact-email" href="mailto:invinciby@gmail.com"><span>EMAIL</span>invinciby@gmail.com <b>↗</b></a><div class="wechat-channel"><span>WECHAT OFFICIAL ACCOUNT</span><div class="wechat-mark">虾</div><div><h2>你好不吃虾</h2><p>在微信中搜索公众号「你好不吃虾」</p></div></div></div></section><section class="contact-grid"><article class="green"><span>01</span><h2>论文与研究</h2><p>AI for Science 论文、方法与开放问题。</p></article><article class="orange"><span>02</span><h2>工具与产品</h2><p>科研工作流、知识库和研究型产品。</p></article><article class="blue"><span>03</span><h2>内容与交流</h2><p>文章共创、访谈、分享与跨领域讨论。</p></article></section><section class="contact-note"><span>NOT READY TO WRITE?</span><p>先从文章开始，看看我们是否在关心相似的问题。</p><a href="../essays/">浏览全部文章 →</a></section></main>')
}
for route, (title, body) in pages.items(): write_route(route, title, body)
print('built home and', len(pages), 'section pages')
