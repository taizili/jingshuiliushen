---
title: 从codex到github上成功上线到底需要几步？
date: 2026-09-28
category: 学习心得
excerpt: 记录了成功上线第一个个人学习网站的整个环节
---
将纯静态的网页从无到有变成带后台管理的动态博客，核心流程分为代码生成、静态部署、后台接入和模板绑定四个阶段。以下是一套跑通全流程的标准操作指南。


### 一、 利用 AI 生成网站基础代码

1. 向 AI 下达指令：向大模型（如 Codex、Claude、ChatGPT）描述你的网站需求。例如：“请帮我写一个个人博客的主页 HTML 和配套的 CSS 样式。要求包含顶部导航栏、一个带大标题的介绍区，以及一个两列布局的文章列表区。”

2. 建立本地文件夹：在电脑上新建一个文件夹，将 AI 提供的代码分别保存为 

   `index.html`

    和 

   `css/style.css`

   。

3. 本地预览：双击 

   `index.html`

   ，确认网页的排版、颜色和静态占位文字都符合你的预期。此时，所有的文字都是写死在代码里的。


### 二、 部署到 GitHub Pages (静态上线)

1. 创建远程仓库：登录 GitHub，新建一个 Public 仓库（例如命名为 

   `my-blog`

   ）。

2. 上传代码：将第一步写好的 

   `index.html`

    和 

   `css`

    文件夹上传到该仓库的 

   `main`

    分支。

3. 开启 GitHub Pages：
   进入仓库的 Settings -> Pages。
   在 Build and deployment 下方的 Source 选择 Deploy from a branch。
   Branch 选择 

   `main`

    和 

   `/ (root)`

   ，点击 Save。

4. 等待生效：回到仓库主页点击 Actions，等待名为 "pages build and deployment" 的任务亮起绿色对勾 ✅。此时你的网站已经可以通过 

   `[https://你的用户名.github.io/仓库名/](https://你的用户名.github.io/仓库名/)`

    访问了。


### 三、 搭建 Decap CMS 后台骨架

1. 创建后台入口：在仓库根目录新建 

   `admin/index.html`

   ，填入固定的框架代码。注意：脚本必须放在 body 内部以防白屏。
   HTML<!DOCTYPE 

   **html**

   ><html>  <head><meta charset="utf-8" /><title>后台管理</title></head>  <body>    <script src="https://unpkg.com/decap-cms@^3.0.0/dist/decap-cms.js"></script>  </body></html>
2. 配置数据结构：在同目录下新建 

   `admin/config.yml`

   ，定义你要管理哪些内容。
   YAMLbackend:  # 暂时留空，下一步配置media_folder: "images/uploads"public_folder: "/images/uploads"collections:  - name: "blog"    label: "博客文章"    folder: "_posts"    create: true    slug: "{{year}}-{{month}}-{{day}}-{{slug}}" # Jekyll 要求的格式    fields:      - {label: "标题", name: "title", widget: "string"}      - {label: "日期", name: "date", widget: "datetime"}      - {label: "正文", name: "body", widget: "markdown"}

### 四、 打通认证桥接 (OAuth Bridge)

1. 获取桥接服务：使用如 DecapBridge 等第三方免部署桥接服务，或者通过 Vercel/Render 自己部署一个 OAuth 实例，获取到你的专属 Client ID 或 Endpoint。

2. 完善 Backend 配置：回到 

   `admin/config.yml`

   ，将顶部的 

   `backend`

    补全。
   YAMLbackend:  name: git-gateway  repo: 你的用户名/你的仓库名  branch: main  auth_type: pkce  base_url: https://auth.decapbridge.com # 以 DecapBridge 为例  auth_endpoint: /sites/你的专属ID/pkce  auth_token_endpoint: /sites/你的专属ID/token
3. 此时访问 

   `你的网址/admin/`

   ，点击登录即可成功唤起 GitHub 授权并进入后台界面。


### 五、 激活 Jekyll 动态渲染 (前后端数据绑定)

1. 锁定根目录路径：在仓库根目录新建 

   `_config.yml`

   ，防止子目录部署导致 CSS 样式丢失和内部链接 404。
   YAMLurl: "https://你的用户名.github.io"baseurl: "/你的仓库名"
2. 唤醒首页渲染引擎：打开根目录的 

   `index.html`

   ，在绝对第一行加上 Jekyll 的启动开关，并将内部链接改为动态拼接。
   HTML---layout: null---<!DOCTYPE 

   **html**

   ><!-- 引入 CSS 时加上 baseurl --><link rel="stylesheet" href="{{ site.baseurl }}/css/style.css">
3. 替换动态循环代码：将 

   `index.html`

    里写死的文章列表，替换为读取 

   `_posts`

    文件夹的 Liquid 循环代码。
   HTML{% for post in site.posts %}  <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a>{% endfor %}
4. 制作文章详情页模具：新建 

   `_layouts/post.html`

   ，这是所有文章点进去后共用的模板文件。
   HTML<!DOCTYPE 

   **html**

   ><html>  <body>    <h1>{{ page.title }}</h1>    <div class="content">{{ content }}</div>  </body></html>

在这个阶段，你的目标是拿到一套纯静态的、能在本地浏览器里完美打开的 HTML/CSS 文件。
这一步将你的本地网页挂载到公网上，让所有人都能访问。
静态网站没有数据库，我们需要引入 Decap CMS，让它代替我们向 GitHub 仓库里读写文件。
GitHub 不允许前端网页直接进行登录授权，必须经过一个后端服务。我们需要配置认证桥接来解决登录时的 404 问题。
后台虽然能生成 Markdown 文件了，但前台纯 HTML 不认识这些文件。必须激活 GitHub Pages 自带的 Jekyll 引擎，把数据“注入”到网页里。
当这套流程走完后，你只需要在 `/admin` 后台新建一篇文章并点击 Publish。GitHub 会在后台自动生成文件触发 Actions，一分钟后强制刷新（或使用无痕模式）前台页面，新文章就会完美渲染在你的博客上了。
