# 李西奥的学习笔记

一个专为「学习心得 + 实验方法 + 踩坑记录」设计的个人知识网站。

网站基于 **Jekyll** 构建，托管在 GitHub Pages（免费、无服务器、无数据库），
并通过 **Decap CMS** 提供类似 WordPress 的在线写作后台。

线上地址：https://taizili.github.io/jingshuiliushen/

## ✨ 功能

- **个人主页**：首屏大标题 + 简介 + 最新文章 + 关于我
- **分类系统**：三个分类各有独立版块，首页分类卡片和文章页徽章都能点进去
- **在线后台**：访问 `/admin` 用 GitHub 登录，浏览器里直接写文章、传图片、发布
- **自动构建**：GitHub Pages 原生 Jekyll，发布后 1～2 分钟上线
- **文章体验**：阅读时长、分类徽章、上一篇 / 下一篇导航、返回首页
- **深浅色主题**：一键切换，自动记住访客偏好
- **手机自适应**：手机、平板、电脑都有良好的阅读体验

## 📁 目录结构

```
├── _posts/             # 文章（Markdown，后台发布写到这里）
├── _layouts/post.html  # 文章页模板（导航、分类、上下篇都在这）
├── _data/site.json     # 网站设置（名字、标题、简介，后台可改）
├── categories.html     # 分类目录页
├── index.html          # 首页（Jekyll 模板）
├── admin/              # Decap CMS 后台
├── css/ js/            # 样式和脚本
└── assets/images/      # 后台上传的图片
```

## ✍️ 日常写作

1. 打开 `https://taizili.github.io/jingshuiliushen/admin`
2. 用 GitHub 账号登录
3. 「文章」→ 新增/编辑 → 发布

新文章会保存到 `_posts/`，网站自动更新，无需任何手动操作。

## 🔒 安全

- 后台通过 GitHub OAuth 授权，只有仓库所有者（你）能登录发布
- 访客打开 `/admin` 只能看到登录页，无法做任何修改
- 网站是纯静态页面，没有数据库和服务端逻辑，天然安全

## 🛠 本地开发（可选）

```bash
bundle install
bundle exec jekyll serve
```

然后访问 http://localhost:4000/jingshuiliushen/
