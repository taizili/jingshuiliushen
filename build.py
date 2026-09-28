#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 content/ 里的 Markdown 文章生成静态网站。
GitHub Actions 会在每次内容更新后自动运行这个脚本。
也可以本地手动运行：python3 build.py
"""

import html
import json
import re
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content" / "posts"
POSTS_DIR = BASE_DIR / "posts"
INDEX_HTML = BASE_DIR / "index.html"
SITE_JSON = BASE_DIR / "site.json"

BADGE_CLASS = {
    "实验方法": "badge-experiment",
    "学习心得": "badge-learning",
    "踩坑记录": "badge-pit",
}


# ---------- 设置 ----------

def load_site():
    site = {
        "name": "我的名字",
        "title": "我的学习笔记",
        "heroTitle": "把学到的东西，\n写下来才算真的学会。",
        "description": "这里记录我的学习心得和实验方法。",
    }
    if SITE_JSON.exists():
        data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
        for key in site:
            if isinstance(data.get(key), str) and data[key].strip():
                site[key] = data[key]
    return site


def site_multiline(text):
    return html.escape(text, quote=False).replace("\n", "<br>\n")


def footer_text(site):
    return "© " + str(date.today().year) + " " + html.escape(site["title"], quote=False) + " · 用文字固化思考"


# ---------- Frontmatter / Markdown ----------

def parse_post(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    idx = 1
    while idx < len(lines) and lines[idx].strip() != "---":
        line = lines[idx]
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            meta[key.strip()] = value
        idx += 1
    if idx >= len(lines):
        return None
    body = "\n".join(lines[idx + 1:]).strip()
    for field in ("title", "date", "category", "excerpt"):
        if not meta.get(field):
            return None
    return {"meta": meta, "body": body}


def inline_fmt(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(md):
    lines = md.split("\n")
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
            heading = re.sub(r"\*\*(.+?)\*\*", r"\1", line[3:]).replace("`", "")
            toc.append(heading.strip())
    return toc


def make_slug(meta, existing):
    slug = meta.get("slug", "").strip()
    if slug and slug not in existing:
        return slug
    base = re.sub(r"[^a-zA-Z0-9]+", "-", meta["title"]).strip("-").lower()
    if base and base not in existing:
        return base
    slug = "post-" + meta["date"].replace("-", "")
    while slug in existing:
        slug += "-x"
    return slug


# ---------- 页面生成 ----------

def post_html(post, site):
    title = html.escape(post["title"])
    category = html.escape(post["category"])
    badge = BADGE_CLASS.get(post["category"], "badge-experiment")
    reading_minutes = max(1, round(len(post["body"]) / 500))
    content_html = md_to_html(post["body"])
    toc_list = "".join("<li>" + html.escape(t) + "</li>" for t in extract_toc(post["body"]))

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


def main():
    site = load_site()
    POSTS_DIR.mkdir(exist_ok=True)

    posts = []
    slugs = set()
    for path in sorted(CONTENT_DIR.glob("*.md")):
        parsed = parse_post(path)
        if parsed is None:
            print("跳过格式不对的文件:", path.name)
            continue
        meta = parsed["meta"]
        slug = make_slug(meta, slugs)
        slugs.add(slug)
        posts.append({
            "slug": slug,
            "title": meta["title"],
            "date": meta["date"],
            "category": meta["category"],
            "excerpt": meta["excerpt"],
            "body": parsed["body"],
        })

    posts.sort(key=lambda p: p["date"], reverse=True)

    for post in posts:
        (POSTS_DIR / (post["slug"] + ".html")).write_text(post_html(post, site), encoding="utf-8")

    for old in POSTS_DIR.glob("*.html"):
        if old.stem not in slugs:
            old.unlink()

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

    print("构建完成：", len(posts), "篇文章")


if __name__ == "__main__":
    main()
