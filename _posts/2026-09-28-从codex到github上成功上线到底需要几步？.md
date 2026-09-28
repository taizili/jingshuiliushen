---
title: 从codex到github上成功上线到底需要几步？
date: 2026-09-28
category: 学习心得
excerpt: 记录了成功上线第一个个人学习网站的整个环节
render_with_liquid: false
---

将纯静态的网页从无到有变成带后台管理的动态博客，核心流程分为代码生成、静态部署、后台接入和模板绑定四个阶段。以下是一套跑通全流程的标准操作指南。

### 一、利用 AI 生成网站基础代码

1. **向 AI 下达指令**：向大模型（如 Codex、Claude、ChatGPT）描述你的网站需求。例如：“请帮我写一个个人博客的主页 HTML 和配套的 CSS 样式。要求包含顶部导航栏、一个带大标题的介绍区，以及一个两列布局的文章列表区。”
2. **建立本地文件夹**：在电脑上新建一个文件夹，将 AI 提供的代码分别保存为 `index.html` 和 `css/style.css`。
3. **本地预览**：双击 `index.html`，确认网页的排版、颜色和静态占位文字都符合你的预期。此时，所有的文字都是写死在代码里的。

### 二、部署到 GitHub Pages (静态上线)

1. **创建远程仓库**：登录 GitHub，新建一个 Public 仓库（例如命名为 `my-blog`）。
2. **上传代码**：将第一步写好的 `index.html` 和 `css` 文件夹上传到该仓库的 `main` 分支。
3. **开启 GitHub Pages**：
   * 进入仓库的 **Settings** -> **Pages**。
   * 在 Build and deployment 下方的 Source 选择 **Deploy from a branch**。
   * Branch 选择 `main` 和 `/ (root)`，点击 **Save**。
4. **等待生效**：回到仓库主页点击 Actions，等待名为 "pages build and deployment" 的任务亮起绿色对勾 ✅。此时你的网站已经可以通过 `https://你的用户名.github.io/仓库名/` 访问了。

### 三、搭建 Decap CMS 后台骨架

静态网站没有数据库，我们需要引入 Decap CMS，让它代替我们向 GitHub 仓库里读写文件。

1. **创建后台入口**：在仓库根目录新建 `admin/index.html`，填入固定的框架代码。注意：脚本必须放在 body 内部以防白屏。
   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <meta charset="utf-8" />
       <title>后台管理</title>
     </head>
     <body>
       <script src="[https://unpkg.com/decap-cms](https://unpkg.com/decap-cms)@^3.0.0/dist/decap-cms.js"></script>
     </body>
   </html>
