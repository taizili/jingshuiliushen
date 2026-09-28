#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人学习笔记网站 - 本地后台管理

运行方式：
    python3 admin.py

然后访问：
    管理后台  http://localhost:8000/admin
    网站首页  http://localhost:8000
"""

import html
import json
import re
import threading
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
POSTS_JSON = BASE_DIR / "posts.json"
POSTS_DIR = BASE_DIR / "posts"
INDEX_HTML = BASE_DIR / "index.html"
SITE_JSON = BASE_DIR / "site.json"

CATEGORIES = ["实验方法", "学习心得", "踩坑记录"]
BADGE_CLASS = {
    "实验方法": "badge-experiment",
    "学习心得": "badge-learning",
    "踩坑记录": "badge-pit",
}

WRITE_LOCK = threading.Lock()

DEFAULT_SITE = {
    "name": "迟雨",
    "title": "迟雨的学习笔记",
    "heroTitle": "把学到的东西，\n写下来才算真的学会。",
    "description": "这里记录我的学习心得、实验方法和踩过的坑。\n每篇文章都尽量做到：看得懂、能复现、有结论。",
}


def inline_fmt(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(code_lines), quote=False) + "</code></pre>")

        elif line.startswith("### "):
            out.append("<h3>" + inline_fmt(line[4:]) + "</h3>")
            i += 1

        elif line.startswith("## "):
            out.append("<h2>" + inline_fmt(line[3:]) + "</h2>")
            i += 1

        elif line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            out.append("<blockquote>" + "<br>".join(inline_fmt(q) for q in quote_lines) + "</blockquote>")

        elif re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>" + inline_fmt(x) + "</li>" for x in items) + "</ol>")

        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join("<li>" + inline_fmt(x) + "</li>" for x in items) + "</ul>")

        elif stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1]):
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]

            header = cells(line)
            i += 2
            body_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body_rows.append(cells(lines[i]))
                i += 1
            table = "<table><thead><tr>" + "".join("<th>" + inline_fmt(c) + "</th>" for c in header) + "</tr></thead><tbody>"
            for row in body_rows:
                table += "<tr>" + "".join("<td>" + inline_fmt(c) + "</td>" for c in row) + "</tr>"
            table += "</tbody></table>"
            out.append(table)

        elif stripped == "":
            i += 1

        else:
            para = []
            while i < len(lines):
                current = lines[i]
                if (current.strip() == "" or current.startswith(("## ", "### ", "- ", "> ", "```"))
                        or re.match(r"^\d+\. ", current) or current.strip().startswith("|")):
                    break
                para.append(current)
                i += 1
            out.append("<p>" + " ".join(inline_fmt(x) for x in para) + "</p>")

    return "\n".join(out)


def extract_toc(md):
    toc = []
    for line in md.split("\n"):
        if line.startswith("## "):
            heading = re.sub(r"\*\*(.+?)\*\*", r"\1", line[3:])
            heading = heading.replace("`", "")
            toc.append(heading.strip())
    return toc


def post_html(post, site):
    title = html.escape(post["title"])
    category = html.escape(post["category"])
    badge = BADGE_CLASS.get(post["category"], "badge-experiment")
    reading_minutes = max(1, round(len(post["content"]) / 500))
    content_html = md_to_html(post["content"])
    toc_items = extract_toc(post["content"])
    toc_list = "".join("<li>" + html.escape(t) + "</li>" for t in toc_items)

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>""" + title + """ — """ + html.escape(site["title"]) + """</title>
  <link rel="stylesheet" href="../css/style.css">
  <script src="../js/main.js" defer></script>
</head>
<body class="post-page">
  <header class="site-header">
    <div class="container header-inner">
      <a href="../index.html" class="logo">""" + html.escape(site["name"]) + """<span class="logo-dot">.</span></a>
      <nav class="site-nav">
        <a href="../index.html#latest" class="nav-link">最新文章</a>
        <a href="../index.html#categories" class="nav-link">分类</a>
        <a href="../index.html#about" class="nav-link">关于</a>
      </nav>
      <button class="theme-toggle" id="theme-toggle" aria-label="切换深浅主题" title="切换深浅主题">
        <span class="theme-icon">◐</span>
      </button>
    </div>
  </header>

  <main class="container post-layout">
    <article class="post-article">
      <header class="post-header">
        <span class="badge """ + badge + """">""" + category + """</span>
        <h1>""" + title + """</h1>
        <div class="post-meta">
          <span>""" + html.escape(post["date"]) + """</span>
          <span>·</span>
          <span>约 """ + str(reading_minutes) + """ 分钟阅读</span>
        </div>
      </header>
      <div class="post-content">
""" + content_html + """
      </div>
    </article>

    <aside class="post-sidebar">
      <a href="../index.html" class="btn btn-ghost">← 返回首页</a>
      <div class="toc-card">
        <h3>本文结构</h3>
        <ul class="toc-list">
""" + toc_list + """
        </ul>
      </div>
    </aside>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>""" + footer_text(site) + """</p>
      <a href="../index.html" class="back-top">回到首页 ↑</a>
    </div>
  </footer>
</body>
</html>
"""


def card_html(post):
    badge = BADGE_CLASS.get(post["category"], "badge-experiment")
    return ('          <a href="posts/' + post["slug"] + '.html" class="post-card">\n'
            '            <div class="post-card-top">\n'
            '              <span class="badge ' + badge + '">' + html.escape(post["category"]) + '</span>\n'
            '              <span class="post-date">' + html.escape(post["date"]) + '</span>\n'
            '            </div>\n'
            '            <h3 class="post-card-title">' + html.escape(post["title"]) + '</h3>\n'
            '            <p class="post-card-excerpt">' + html.escape(post["excerpt"]) + '</p>\n'
            '            <span class="post-read-more">阅读全文 →</span>\n'
            '          </a>')


def load_posts():
    if POSTS_JSON.exists():
        return json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    return []


def load_site():
    site = dict(DEFAULT_SITE)
    if SITE_JSON.exists():
        try:
            data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
            for key in site:
                if isinstance(data.get(key), str) and data[key].strip():
                    site[key] = data[key]
        except (ValueError, OSError):
            pass
    return site


def save_site(site):
    SITE_JSON.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def site_multiline(text):
    return html.escape(text, quote=False).replace("\n", "<br>\n")


def footer_text(site):
    return "© " + str(date.today().year) + " " + html.escape(site["title"], quote=False) + " · 用文字固化思考"


def save_posts(posts):
    POSTS_JSON.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def regenerate_site():
    site = load_site()
    posts = sorted(load_posts(), key=lambda p: p["date"], reverse=True)
    for post in posts:
        path = POSTS_DIR / (post["slug"] + ".html")
        path.write_text(post_html(post, site), encoding="utf-8")

    index = INDEX_HTML.read_text(encoding="utf-8")
    cards = "\n".join(card_html(p) for p in posts)
    new_index = re.sub(
        r"<!-- POSTS:START -->.*?<!-- POSTS:END -->",
        "<!-- POSTS:START -->\n" + cards + "\n          <!-- POSTS:END -->",
        index,
        flags=re.DOTALL,
    )
    new_index = apply_site_to_index(new_index, site)
    INDEX_HTML.write_text(new_index, encoding="utf-8")


def apply_site_to_index(index, site):
    def replace_block(marker, content):
        pattern = r"<!-- SITE:" + marker + r":START -->.*?<!-- SITE:" + marker + r":END -->"
        replacement = "<!-- SITE:" + marker + ":START -->" + content + "<!-- SITE:" + marker + ":END -->"
        return re.sub(pattern, replacement, index, flags=re.DOTALL)

    index = replace_block("NAME", html.escape(site["name"], quote=False))
    index = replace_block("HERO", site_multiline(site["heroTitle"]))
    index = replace_block("DESC", site_multiline(site["description"]))
    index = replace_block("FOOTER", footer_text(site))
    index = re.sub(r"<title>.*?</title>", "<title>" + html.escape(site["title"]) + "</title>", index, flags=re.DOTALL)
    first_line = site["description"].split("\n")[0]
    index = re.sub(
        r'<meta name="description" content="[^"]*">',
        '<meta name="description" content="' + html.escape(first_line, quote=True) + '">',
        index,
    )
    return index


def make_slug(title, existing):
    base = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    if base and base not in existing:
        return base
    slug = "post-" + date.today().strftime("%Y%m%d-%H%M%S")
    while slug in existing:
        slug += "-x"
    return slug


def valid_post(data):
    return all(isinstance(data.get(k), str) and data[k].strip()
               for k in ("title", "date", "category", "excerpt", "content"))


ADMIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>后台管理 — __SITE_TITLE__</title>
  <link rel="stylesheet" href="/css/style.css">
  <style>
    body { background: var(--bg-alt); }
    .admin-wrap { max-width: 880px; margin: 0 auto; padding: 32px 20px 64px; }
    .admin-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; flex-wrap: wrap; gap: 12px; }
    .admin-head h1 { font-size: 1.5rem; letter-spacing: -0.02em; }
    .admin-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow); margin-bottom: 20px; }
    .admin-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
    .admin-table th, .admin-table td { text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--border); }
    .admin-table th { color: var(--text-muted); font-weight: 600; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .admin-table tr:last-child td { border-bottom: none; }
    .post-title-cell { font-weight: 600; }
    .post-title-cell a { color: var(--text); }
    .post-title-cell a:hover { color: var(--accent); }
    .btn-danger { background: rgba(220, 38, 38, 0.1); color: #dc2626; border: none; cursor: pointer; font: inherit; font-weight: 600; padding: 6px 12px; border-radius: 8px; }
    .btn-danger:hover { background: rgba(220, 38, 38, 0.18); }
    .btn-small { font-size: 0.85rem; padding: 6px 14px; }
    .editor { display: none; }
    .editor.open { display: block; }
    .form-grid { display: grid; grid-template-columns: 1fr 180px 180px; gap: 14px; }
    .form-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
    .form-field label { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
    .form-field input, .form-field select, .form-field textarea {
      font-family: inherit; font-size: 0.95rem; color: var(--text);
      background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px;
    }
    .form-field textarea { resize: vertical; }
    .form-field .content-area { font-family: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace; min-height: 340px; line-height: 1.7; }
    .form-actions { display: flex; gap: 10px; margin-top: 8px; }
    .empty-hint { color: var(--text-muted); text-align: center; padding: 24px 0; }
    .md-hint { font-size: 0.82rem; color: var(--text-muted); background: var(--bg-alt); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin-top: 4px; line-height: 1.8; }
    .md-hint code { background: var(--surface); padding: 1px 6px; border-radius: 4px; font-size: 0.78rem; }
    @media (max-width: 700px) { .form-grid { grid-template-columns: 1fr; } .admin-table .hide-sm { display: none; } }
  </style>
</head>
<body>
  <div class="admin-wrap">
    <div class="admin-head">
      <div>
        <h1>📝 后台管理</h1>
        <p style="color:var(--text-muted);font-size:0.9rem;">在这里写文章、改文章，网站会自动更新</p>
      </div>
      <div style="display:flex;gap:10px;">
        <a href="/" class="btn btn-ghost btn-small" target="_blank">查看网站 ↗</a>
        <button class="btn btn-primary btn-small" id="btn-new">＋ 新建文章</button>
      </div>
    </div>

    <div class="admin-card">
      <table class="admin-table">
        <thead>
          <tr><th>标题</th><th>分类</th><th class="hide-sm">日期</th><th style="text-align:right;">操作</th></tr>
        </thead>
        <tbody id="post-rows"></tbody>
      </table>
      <div class="empty-hint" id="empty-hint" style="display:none;">还没有文章，点击右上角「新建文章」开始写作</div>
    </div>

    <div class="admin-card">
      <h2 style="font-size:1.15rem;margin-bottom:18px;">⚙️ 网站设置</h2>
      <div class="form-grid" style="grid-template-columns:1fr 1fr;">
        <div class="form-field">
          <label>你的名字（logo、关于区）</label>
          <input id="s-name" placeholder="比如：迟雨">
        </div>
        <div class="form-field">
          <label>网站名称（标签页、页脚）</label>
          <input id="s-title" placeholder="比如：迟雨的学习笔记">
        </div>
      </div>
      <div class="form-field">
        <label>首页大标题（换行会自动分行显示）</label>
        <textarea id="s-hero" rows="2"></textarea>
      </div>
      <div class="form-field">
        <label>网站简介（显示在首页大标题下方）</label>
        <textarea id="s-desc" rows="3"></textarea>
      </div>
      <button class="btn btn-primary" id="btn-site-save">保存网站设置</button>
      <span id="site-saved" style="color:var(--accent);font-size:0.88rem;margin-left:10px;opacity:0;transition:opacity .3s;">✓ 已更新</span>
    </div>

    <div class="admin-card editor" id="editor">
      <h2 style="font-size:1.15rem;margin-bottom:18px;" id="editor-title">新建文章</h2>
      <div class="form-grid">
        <div class="form-field">
          <label>标题</label>
          <input id="f-title" placeholder="给这篇文章起个名字">
        </div>
        <div class="form-field">
          <label>分类</label>
          <select id="f-category">
            <option>实验方法</option>
            <option>学习心得</option>
            <option>踩坑记录</option>
          </select>
        </div>
        <div class="form-field">
          <label>日期</label>
          <input id="f-date" type="date">
        </div>
      </div>
      <div class="form-field">
        <label>摘要（显示在首页卡片上）</label>
        <textarea id="f-excerpt" rows="2" placeholder="一两句话概括这篇文章"></textarea>
      </div>
      <div class="form-field">
        <label>正文（支持简单格式，见下方说明）</label>
        <textarea id="f-content" class="content-area" placeholder="在这里写正文……"></textarea>
        <div class="md-hint">
          格式说明：<code>## 二级标题</code> · <code>**粗体**</code> · <code>- 列表项</code> · <code>1. 编号列表</code> · <code>&gt; 引用</code> · <code>`代码`</code> · <code>```代码块```</code> · 表格用 <code>| 分隔 |</code>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" id="btn-save">保存并更新网站</button>
        <button class="btn btn-ghost" id="btn-cancel">取消</button>
      </div>
    </div>
  </div>

  <script>
    let editingSlug = null;
    const $ = (id) => document.getElementById(id);

    async function loadPosts() {
      const res = await fetch('/api/posts');
      const posts = await res.json();
      const rows = $('post-rows');
      rows.innerHTML = '';
      $('empty-hint').style.display = posts.length ? 'none' : 'block';
      for (const p of posts) {
        const tr = document.createElement('tr');
        const badge = { '实验方法': 'badge-experiment', '学习心得': 'badge-learning', '踩坑记录': 'badge-pit' }[p.category] || 'badge-experiment';
        tr.innerHTML = '<td class="post-title-cell"><a href="/posts/' + p.slug + '.html" target="_blank">' + esc(p.title) + '</a></td>' +
          '<td><span class="badge ' + badge + '">' + esc(p.category) + '</span></td>' +
          '<td class="hide-sm" style="color:var(--text-muted)">' + esc(p.date) + '</td>' +
          '<td style="text-align:right;white-space:nowrap;">' +
          '<button class="btn btn-ghost btn-small" data-edit="' + esc(p.slug) + '">编辑</button> ' +
          '<button class="btn-danger btn-small" data-del="' + esc(p.slug) + '" data-title="' + esc(p.title) + '">删除</button></td>';
        rows.appendChild(tr);
      }
    }

    function esc(s) {
      return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    document.addEventListener('click', async (e) => {
      const editSlug = e.target.getAttribute && e.target.getAttribute('data-edit');
      const delSlug = e.target.getAttribute && e.target.getAttribute('data-del');
      if (editSlug) { await openEditor(editSlug); return; }
      if (delSlug) {
        const title = e.target.getAttribute('data-title');
        if (!confirm('确定要删除《' + title + '》吗？此操作不可恢复。')) return;
        await fetch('/api/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slug: delSlug }) });
        await loadPosts();
      }
    });

    async function openEditor(slug) {
      const res = await fetch('/api/posts');
      const posts = await res.json();
      const p = posts.find(x => x.slug === slug);
      if (!p) return;
      editingSlug = slug;
      $('editor-title').textContent = '编辑文章';
      $('f-title').value = p.title;
      $('f-category').value = p.category;
      $('f-date').value = p.date;
      $('f-excerpt').value = p.excerpt;
      $('f-content').value = p.content;
      $('editor').classList.add('open');
      $('editor').scrollIntoView({ behavior: 'smooth' });
    }

    $('btn-new').addEventListener('click', () => {
      editingSlug = null;
      $('editor-title').textContent = '新建文章';
      $('f-title').value = '';
      $('f-category').value = '实验方法';
      $('f-date').value = new Date().toISOString().slice(0, 10);
      $('f-excerpt').value = '';
      $('f-content').value = '';
      $('editor').classList.add('open');
      $('editor').scrollIntoView({ behavior: 'smooth' });
      $('f-title').focus();
    });

    $('btn-cancel').addEventListener('click', () => $('editor').classList.remove('open'));

    $('btn-save').addEventListener('click', async () => {
      const payload = {
        slug: editingSlug,
        title: $('f-title').value.trim(),
        category: $('f-category').value,
        date: $('f-date').value,
        excerpt: $('f-excerpt').value.trim(),
        content: $('f-content').value,
      };
      if (!payload.title || !payload.excerpt || !payload.content.trim()) {
        alert('请填写标题、摘要和正文');
        return;
      }
      const res = await fetch('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await res.json();
      if (!result.ok) { alert(result.error || '保存失败'); return; }
      $('editor').classList.remove('open');
      await loadPosts();
    });

    async function loadSettings() {
      const res = await fetch('/api/site');
      const s = await res.json();
      $('s-name').value = s.name;
      $('s-title').value = s.title;
      $('s-hero').value = s.heroTitle;
      $('s-desc').value = s.description;
    }

    $('btn-site-save').addEventListener('click', async () => {
      const payload = {
        name: $('s-name').value.trim(),
        title: $('s-title').value.trim(),
        heroTitle: $('s-hero').value,
        description: $('s-desc').value,
      };
      if (!payload.name || !payload.title || !payload.heroTitle.trim() || !payload.description.trim()) {
        alert('请填写完整的网站设置');
        return;
      }
      const res = await fetch('/api/site/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await res.json();
      if (!result.ok) { alert(result.error || '保存失败'); return; }
      const hint = $('site-saved');
      hint.style.opacity = '1';
      setTimeout(() => hint.style.opacity = '0', 2000);
    });

    loadPosts();
    loadSettings();
  </script>
</body>
</html>
"""


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, fmt, *args):
        print("[site] " + self.address_string() + " " + (fmt % args))

    def do_GET(self):
        if self.path in ("/admin", "/admin/"):
            page = ADMIN_PAGE.replace("__SITE_TITLE__", html.escape(load_site()["title"]))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
        elif self.path == "/api/posts":
            with WRITE_LOCK:
                posts = load_posts()
            posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)
            self._send_json(posts_sorted)
        elif self.path == "/api/site":
            with WRITE_LOCK:
                site = load_site()
            self._send_json(site)
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send_json({"ok": False, "error": "请求数据格式错误"}, status=400)
            return

        if self.path == "/api/save":
            self._handle_save(data)
        elif self.path == "/api/delete":
            self._handle_delete(data)
        elif self.path == "/api/site/save":
            self._handle_site_save(data)
        else:
            self._send_json({"ok": False, "error": "未知接口"}, status=404)

    def _handle_site_save(self, data):
        if not all(isinstance(data.get(k), str) and data[k].strip()
                   for k in ("name", "title", "heroTitle", "description")):
            self._send_json({"ok": False, "error": "请填写完整的网站设置"}, status=400)
            return
        with WRITE_LOCK:
            save_site({
                "name": data["name"].strip(),
                "title": data["title"].strip(),
                "heroTitle": data["heroTitle"].strip("\n"),
                "description": data["description"].strip("\n"),
            })
            regenerate_site()
        self._send_json({"ok": True})

    def _handle_save(self, data):
        if not valid_post(data):
            self._send_json({"ok": False, "error": "请填写完整：标题、日期、分类、摘要、正文"}, status=400)
            return
        if data["category"] not in CATEGORIES:
            self._send_json({"ok": False, "error": "分类不合法"}, status=400)
            return
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", data["date"]):
            self._send_json({"ok": False, "error": "日期格式应为 YYYY-MM-DD"}, status=400)
            return

        with WRITE_LOCK:
            posts = load_posts()
            slugs = set(p["slug"] for p in posts)
            slug = data.get("slug")
            post = {
                "slug": slug,
                "title": data["title"].strip(),
                "date": data["date"],
                "category": data["category"],
                "excerpt": data["excerpt"].strip(),
                "content": data["content"].rstrip(),
            }

            if slug and slug in slugs:
                posts = [post if p["slug"] == slug else p for p in posts]
            else:
                post["slug"] = make_slug(data["title"], slugs)
                posts.append(post)

            save_posts(posts)
            regenerate_site()

        self._send_json({"ok": True, "slug": post["slug"]})

    def _handle_delete(self, data):
        slug = data.get("slug")
        if not slug:
            self._send_json({"ok": False, "error": "缺少文章标识"}, status=400)
            return
        with WRITE_LOCK:
            posts = load_posts()
            remaining = [p for p in posts if p["slug"] != slug]
            if len(remaining) == len(posts):
                self._send_json({"ok": False, "error": "文章不存在"}, status=404)
                return
            save_posts(remaining)
            target = POSTS_DIR / (slug + ".html")
            if target.exists():
                target.unlink()
            regenerate_site()
        self._send_json({"ok": True})

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    POSTS_DIR.mkdir(exist_ok=True)
    if not POSTS_JSON.exists():
        save_posts([])
    if not SITE_JSON.exists():
        save_site(DEFAULT_SITE)
    regenerate_site()

    port = 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), SiteHandler)
    print()
    print("  ✅ 网站已启动")
    print()
    print("  📝 管理后台  http://localhost:" + str(port) + "/admin")
    print("  🏠 网站首页  http://localhost:" + str(port))
    print()
    print("  按 Ctrl+C 停止")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n  已停止，网站文件已保存在当前文件夹")


if __name__ == "__main__":
    main()
