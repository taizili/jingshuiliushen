# 迟雨的学习笔记

一个专为「学习心得 + 实验方法」设计的个人知识网站。

在这里，我把学到的东西写成笔记、把实验过程记录成可复现的文档。
网站本身部署在 GitHub Pages 上，完全免费、没有服务器、没有数据库，
却拥有和 WordPress 类似的在线写作体验。

## ✨ 功能特性

- **个人主页**：首屏大标题 + 简介，展示「我是谁、这个网站写什么」
- **博客系统**：文章按「学习心得 / 实验方法 / 踩坑记录」三类管理，自动生成文章页和首页卡片
- **在线后台**：访问 `/admin` 用 GitHub 登录，在浏览器里直接写文章、编辑、发布，像用 WordPress 一样
- **Markdown 写作**：支持标题、粗体、列表、引用、表格、代码块，写作时所见即所得
- **图片上传**：在后台编辑器里直接拖拽上传图片，自动保存到仓库
- **网站设置可视化**：网站名称、首页大标题、简介都能在后台改，保存即全站生效
- **自动构建**：发布文章后 GitHub Actions 自动重新生成页面，1～2 分钟上线
- **深浅色主题**：一键切换，自动记住访客偏好
- **手机自适应**：手机、平板、电脑都有良好的阅读体验
- **零成本运营**：静态托管 + 免费无头 CMS，没有服务器费用

## 🧭 网站结构

访客看到的部分：

- **首页**：个人介绍 + 最新文章 + 内容分类 + 关于我
- **文章页**：正文 + 目录侧栏 + 阅读时长 + 分类徽章

你使用的部分（别人进不去）：

- **后台**：`你的网址/admin`，写文章、改设置、管理内容

## 🚀 部署指南

### 第一步：上传到 GitHub

1. 在 GitHub 创建公开仓库，推荐命名为 `你的用户名.github.io`
2. 上传本文件夹里的**所有内容**（注意是文件夹里面的文件，不是文件夹本身）
3. 等 1～2 分钟，访问 `https://你的用户名.github.io` 能看到网站即可

### 第二步：开通在线后台（一次性，约 10 分钟）

后台基于 [Decap CMS](https://decapcms.org)，登录需要 OAuth 授权，推荐使用免费服务
[Decap Bridge](https://decapbridge.com)：

1. 打开 decapbridge.com，用 GitHub 账号登录
2. 按引导创建一个 Bridge（会得到一个 Site ID）
3. 按引导在 GitHub 创建 OAuth App：
   - GitHub → 头像 → Settings → Developer settings → OAuth Apps → New OAuth App
   - 回调地址填 Bridge 页面显示的地址
   - 创建后把 Client ID 和 Client Secret 填回 Bridge
4. 打开仓库里的 `admin/config.yml`，修改三处：
   - `repo: 你的用户名/仓库名`
   - `auth_endpoint: auth/Bridge给你的SiteID`
   - `site_url: https://你的用户名.github.io`
5. 提交修改（可直接在 GitHub 网页上编辑这个文件）

### 第三步：开始写作

1. 打开 `https://你的用户名.github.io/admin`
2. 点「Login with GitHub」授权
3. 「文章」→「新增文章」，填写标题、分类、摘要和正文
4. 点「Publish / 发布」——文章以 Markdown 存入仓库，自动构建上线

## 🔒 安全说明

- 后台通过 GitHub OAuth 登录，**只有你的 GitHub 账号**（或你明确添加的协作者）有权发布
- 访客打开 `/admin` 最多看到登录页，没有你的授权无法做任何修改
- 网站是纯静态文件：没有数据库、没有服务端逻辑，天然没有常见攻击面

## 📁 目录结构

```
├── index.html              # 首页（卡片和设置由构建自动生成）
├── content/posts/          # 文章源文件（Markdown，后台编辑的就是这里）
├── site.json               # 网站设置（名字、简介）
├── posts/                  # 生成的文章页（自动生成，不用手动改）
├── admin/                  # Decap CMS 后台界面
├── .github/workflows/      # GitHub 自动构建配置
├── build.py                # 网站生成脚本
├── css/ js/                # 样式和脚本
└── assets/images/          # 后台上传的图片
```

## 🛠 本地预览（可选）

双击 `index.html` 可以离线查看当前已生成的页面。
本地改文件后想手动重新生成：

```bash
python3 build.py
```

## 🎨 自定义

- **主题色**：修改 `css/style.css` 顶部的 `--accent` 变量
- **分类**：`admin/config.yml` 里的分类选项 + `css/style.css` 里对应的徽章颜色
- **关于我**：首页 `index.html` 中「关于我」区域的文字
