---
title: 纯手写 HTML 静态网站接入 Decap CMS 踩坑与完整实战记录
date: 2026-09-29
category: 学习心得
excerpt: 将一个纯手写的静态 HTML 页面，升级为可通过 Decap CMS
  后台管理的动态博客，中间会经历认证、数据读取、路径跳转等多个环节的磨合。以下是整个改造过程中的核心踩坑记录与解决方案。
layout: post
---
### 1. 登录与后台加载：白屏与 404 迷局

问题现象：

* 访问 `/admin` 页面直接白屏，控制台报错 `Cannot read properties of null (reading 'appendChild')`。
* 成功进入后台点击“使用 GitHub 登录”时，弹出 404 错误（`ROUTE_NOT_FOUND`）。

根本原因与解决：

* 白屏是因为 Decap CMS 的核心 `<script>` 脚本放错了位置。脚本试图向 `<body>` 中注入后台界面，但此时 HTML 的 `body` 尚未加载。对策：必须确保 `admin/index.html` 拥有完整的 HTML 结构，并将脚本严格放置在 `<body>` 标签内部。
* 登录 404是因为第三方认证桥接（DecapBridge）的 API 路径与默认的 GitHub backend 路径不匹配。Decap CMS 默认请求 `/auth/`，而 DecapBridge 需要 `/sites/`。对策：在 `admin/config.yml` 中必须使用官方指定的 `git-gateway` 与精确的端点配置：

### 2. 前后端断层：后台已发布，前台无变化

问题现象：在 Decap CMS 后台成功修改了网站设置并发布了新文章，GitHub 仓库里也确实生成了数据文件，但前台网页刷新后依然显示旧的“写死”的文字。

根本原因与解决：纯静态的 HTML 网页没有主动“读取”外部文件的能力。Decap CMS 只是一个“文件生成器”，还需要引入 Jekyll（GitHub Pages 原生支持）作为“组装流水线”，将数据和 HTML 模具结合。

对策（开启 Jekyll 渲染的三步走）：

1. 激活 Jekyll：在 `index.html` 的绝对第一行（没有任何空格或换行）加入三横线：
2. 规范文件路径：将 `config.yml` 中的数据保存路径改为 Jekyll 识别的标准规范：文章存入 `_posts` 文件夹并自带日期前缀（`slug: "{{year}}-{{month}}-{{day}}-{{slug}}"`），网站全局设置存入 `_data/site.json`。
3. 替换动态占位符：将 HTML 中写死的文字替换为 Liquid 语法标签。例如用 `{{ site.data.site.title }}` 读取全站标题，用 `{% for post in site.posts %}` 循环遍历渲染文章列表。

### 3. 子目录路径陷阱：CSS 样式丢失与链接 404

问题现象：通过无痕模式排除了缓存干扰后，发现由 `_layouts/post.html` 生成的文章详情页变成了纯白底色（样式丢失），且点击导航栏的“返回首页”会跳转到 404 页面。

根本原因与解决：当 GitHub Pages 托管在子目录（如 `[https://username.github.io/repo-name/](https://username.github.io/repo-name/)`）时，如果在 HTML 中直接写 `/css/style.css` 或 `/`，浏览器会默认跳转到最顶级的根域名（`username.github.io`），从而导致资源迷路。

对策（强制物理路径拼接）：

1. 在仓库根目录新建 `_config.yml` 文件，声明基础路径：
2. 在所有涉及跨层级的跳转与资源引入处，强制加上 `{{ site.baseurl }}` 前缀：

   * 引入样式：`<link rel="stylesheet" href="{{ site.baseurl }}/css/style.css">`
   * 跳转首页：`<a href="{{ site.baseurl }}/#latest" class="nav-link">返回首页</a>`

**总结与经验**

在 GitHub Pages 环境下调试动态化渲染，排查缓存与检查 Actions 状态是最重要的基本功。每次推送代码后，必须先确认 GitHub Actions 绿灯通过，再通过浏览器的无痕模式进行测试。Jekyll 虽然配置简单，但对格式（如 YAML 的缩进与空格、文件开头的 `---`）极其敏感，确保语法严丝合缝是跑通全流程的关键。
