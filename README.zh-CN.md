<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/logo-dark.svg">
    <img src="assets/readme/logo-light.svg" alt="Light-WeChat" width="500">
  </picture>
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

<p align="center">
  <a href="https://github.com/Light0305/Light-WeChat/releases/tag/v1.0.0"><img src="https://img.shields.io/badge/Release-v1.0.0-16875D?style=flat" alt="Release v1.0.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPL--3.0--only-202126?style=flat" alt="许可证：AGPL-3.0-only"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-202126?style=flat" alt="Python 3.11 及以上">
  <img src="https://img.shields.io/badge/Default-local%20preview-16875D?style=flat" alt="默认本地预览">
</p>

**从一个好问题，到一篇可以认真审阅的公众号文章。**

Light-WeChat 是给 AI Agent 使用的公众号内容 Skill，完成选题研究、写作、审稿、配图、排版和真实移动预览。来源和主张可追溯；需要时，可以连接**你自己的公众号**，上传指定版本并回查草稿。

覆盖 AI、论文、计算机行业就业，以及有真实材料的项目案例。账号名称、作者、栏目和文末联系卡均可配置。默认完成本地制作；公众号上传与付费生图按需开启。

[网站](https://lightchuan.space/) · [安装](#安装) · [自定义生图模型](#自定义生图模型) · [支持与反馈](#支持与反馈)

## 安装

适用于 Codex 或能够读取 `SKILL.md`、运行本地命令并查看浏览器截图的 Agent。需要 **Python 3.11+**、**Node.js 22.20+**，以及本机 **Chrome、Edge 或 Chromium**。搜索和内置生图由你的 Agent 提供；本项目不附带模型订阅或 API 额度。

### 交给 Agent

```text
帮我安装 Light-WeChat 这个 skill，项目地址：https://github.com/Light0305/Light-WeChat
安装到当前项目的 skills 目录，保留完整目录，在独立虚拟环境安装锁定的 Python
依赖并运行 doctor.py。默认只做本地预览，需要时我会配置自己的公众号和生图服务。
```

### 命令安装

也可以从 [Releases](https://github.com/Light0305/Light-WeChat/releases/latest) 下载完整源码包，再按下方手动安装与依赖准备步骤操作。

Windows：

```powershell
npx.cmd skills@latest add Light0305/Light-WeChat --skill light-wechat
```

macOS / Linux：

```bash
npx skills@latest add Light0305/Light-WeChat --skill light-wechat
```

[skills CLI](https://github.com/vercel-labs/skills) 还需要 Git。按提示选择 Agent 和安装范围；项目安装请先进入目标项目。安装 Skill **不会自动安装**下方 Python 依赖。

手动安装时，把**整个源码目录**放到项目的 `.agents/skills/light-wechat/`，或你所用 Agent 对应的技能目录。`SKILL.md` 应直接位于该目录，与 `scripts/`、`shared/`、`tools/`、`vendor/` 同级，不能只复制入口文件。

### 准备本地环境

在安装后的 Skill 目录打开终端。

Windows PowerShell：

```powershell
python -m venv .venv
./.venv/Scripts/python -m pip install --require-hashes -r requirements.txt
./.venv/Scripts/python scripts/configure.py init
./.venv/Scripts/python scripts/doctor.py
```

macOS / Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
.venv/bin/python scripts/configure.py init
.venv/bin/python scripts/doctor.py
```

后续 `python` 命令均使用这个虚拟环境的解释器，或先激活环境。本次本机验收在 Windows 完成；macOS/Linux 已有路径发现支持，尚未在对应系统实测。详见 [验证记录](RELEASE_AUDIT.md)。

## 作品展示

[![Chuan Lab 网站：书架式文章首页](assets/readme/site-home.png)](https://lightchuan.space/)

[Chuan Lab · lightchuan.space](https://lightchuan.space/)：我的内容网站，收录 AI、论文、计算机行业就业和个人项目文章。上图为本次提供的真实首页截图。网站是独立的作品展示，Light-WeChat 开源版不包含网站部署和同步功能。

## 从一个问题开始

安装后，让 Agent 调用 Skill：

```text
用 $light-wechat 从 AI、论文、计算机行业就业三个方向各推荐一个选题，
说明读者能得到什么，并给出首选。等我选定后，完成正文、配图和移动预览，先留本地。
```

已经有题目或材料，也可以直接开始：

```text
用 $light-wechat 把这篇论文讲给开发者听：<论文链接或本地 PDF>。
回到原始证据，讲清机制、案例和局限，完成公众号正文、封面和实际移动预览。先不上传。
```

也可以只做一个环节：检查现有稿、调整结构、更换封面，或把 Markdown 排成微信文章。单独配图、审稿和排版请求只处理对应阶段。

### 它怎么做

| 环节 | 交付内容 |
| --- | --- |
| 研究 | 选题候选、原始来源、编辑简报与明确的阅读承诺 |
| 写作 | 围绕机制、案例、证据和边界组织正文 |
| 审核 | 事实核对、编辑修改与绑定版本的审阅记录 |
| 视觉 | 同一母图的宽封面、方封面，以及按信息任务选择的配图 |
| 排版 | 微信兼容 HTML、Chuan 编辑版动效，以及真实 375 / 390 px 浏览器预览 |
| 可选交付 | 绑定账号与版本的草稿箱上传，以及接口回查 |

每篇文章独立保存在 `workspace/articles/`，正文、证据、图片、审阅、预览和交付记录放在一起。HTML 和检查脚本用于辅助验收；来源、图片与实际版面仍需 Agent 认真阅读和查看。

### 配成你自己的公众号

`configure.py init` 创建本地模板，不覆盖已有设置。编辑 `chuanlab.toml`：

```toml
[publication]
name = "你的公众号名称"
author = "你的作者名"
columns = ["ai", "papers", "careers", "projects"]
contact_card = ""
```

`chuanlab.toml` 保留为兼容配置名。公开版入口为 `light-wechat`，可与单独的 `chuan-lab` 安装共存。

- `paths.workspace` 设置文章工作区，默认 `workspace/`。
- `publication.contact_card` 可填自己的联系卡图片，默认留空；README 中作者的二维码不会加进你的文章。
- `preview.browser` 可指定浏览器可执行文件。
- 相对路径以 Skill 目录为基准；高级用法可显式设置 `CHUANLAB_CONFIG` 或 `CHUANLAB_WORKSPACE`。

## 自定义生图模型

默认优先使用 Agent **自带的生图工具**。宿主工具不可用或技术失败时，可以启用你自己的 **HTTPS Images 兼容 API** 作为备用；也可在任务中明确指定使用已配置的服务。不预置服务商、模型和密钥。

先在本机终端隐藏输入密钥：

```bash
python scripts/configure.py images
```

再编辑 `chuanlab.toml`：

```toml
[images]
enabled = true
base_url = "https://your-provider.example/v1"
model = "your-model-name"
```

填写服务的 **Base URL**，不要填完整 `/images/generations` 地址。适配器会追加 `/images/generations` 或 `/images/edits`；没有路径的根地址会补上 `/v1`。模型名称、尺寸和编辑能力以服务商实际支持为准。

密钥以 `IMAGE_API_KEY` 保存在被忽略的本地 `.env`，不读取其他项目或全局生图配置。`--dry-run` 不读取密钥、不联网、不付费；实际调用需要启用配置，并明确授权 `--confirm-paid`。结果不明确时先保留记录再查证，已保存的成功响应可以恢复下载，避免重复生成付费。

完整示例见 [生图配置](references/image-provider.md)。安全拒绝不会通过切换服务绕过。

## 连接自己的公众号

本地写作和预览不需要公众号凭据。需要上传时，请使用自己有接口权限的账号，并在微信后台配置 IP 白名单。

```bash
python scripts/configure.py wechat
```

本机提示输入 AppID，AppSecret 隐藏输入。然后在 `chuanlab.toml` 设置 `[wechat] enabled = true`。密钥留在本地 `.env`，不要贴到聊天、截图或 Issue 中。

对要上传的文章，将 `delivery` 设为 `wechat-draft`，完成检查与冻结，再明确要求上传这个版本。流程需要 `--confirm-upload`，把账号与冻结版本绑定，并回读核对结果。修改已有稿件优先更新原草稿；结果不明确时先回查，避免重复创建。

上传后的状态是**微信草稿箱待你审核**。冻结表示质量检查通过，不等于授权上传；本项目没有群发或正式发布命令。详见 [交付命令](references/delivery.md)。

## 包含哪些资源

完整目录自带发布后端、工作流脚本和固定版本的上游资源，不依赖他人的本机安装。

| 资源 | 说明 |
| --- | --- |
| [技能入口](SKILL.md) | 任务路由与完整编辑流程 |
| [文件契约](references/artifact-contract.md) | 文章文件、证据和审阅记录 |
| [上游接入](references/upstream-study.md) | AIHOT、WeWrite、Baoyu、Humanizer、gzh-design 与归藏 |
| [源码清单](vendor/manifest.json) | 六个上游的 202 个原文件及哈希 |
| [第三方声明](THIRD_PARTY_NOTICES.md) | 许可证、适配关系与依赖归属 |
| [安全说明](SECURITY.md) | 本地密钥、敏感信息扫描和发布范围 |

<details>
<summary>开发验证与公开打包</summary>

```bash
python -m pip install --require-hashes -r requirements-dev.txt
python -m pytest
python scripts/verify_upstream.py
python scripts/install_gitleaks.py
python scripts/release_check.py
python scripts/build_release.py
```

设置 `RUN_BROWSER_QA=1` 可运行可选的真实浏览器测试。依赖带版本与哈希锁定。发布检查在本机运行敏感文件规则和 Gitleaks，扫描允许发布的源码；有独立 Git 历史时同时扫描历史。源码不会上传给扫描服务。源码包排除凭据、文章工作区、已安装依赖和 Git 元数据，附逐文件 SHA-256 清单。

可选的归藏 HTML 封面检查器需要 `npm ci --ignore-scripts` 及 Playwright 浏览器。常规文章预览直接使用 Node 与本机浏览器。实际完成的检查及限制见 [验证记录](RELEASE_AUDIT.md)。

</details>

## 支持与反馈

- 网站：[lightchuan.space](https://lightchuan.space/)，持续分享文章和项目。
- 问题、建议与使用反馈：[GitHub Issues](https://github.com/Light0305/Light-WeChat/issues)。欢迎 PR 和具体案例，提交前请移除密钥与私人稿件。
- 邮箱：[1833058953@qq.com](mailto:1833058953@qq.com) · GitHub：[@Light0305](https://github.com/Light0305)。
- AI小店：[LightChuan-Shop](https://lightchuan.shop)

<table align="center">
  <tr>
    <th align="center">微信赞赏</th>
    <th align="center">微信交流</th>
    <th align="center">微信公众号</th>
  </tr>
  <tr>
    <td align="center" width="33%"><img src="assets/readme/wechat-donation.jpg" alt="微信赞赏码" width="200"></td>
    <td align="center" width="33%"><img src="assets/readme/wechat-contact.png" alt="作者个人微信二维码" width="200"></td>
    <td align="center" width="33%"><img src="assets/readme/wechat-official-account.jpg" alt="Chuan Lab 微信公众号二维码" width="200"></td>
  </tr>
</table>

<p align="center">随意赞赏、交流或关注，感谢使用 Light-WeChat。</p>

## 许可证

项目原创代码、文档与适配采用 **[AGPL-3.0-only](LICENSE)**。带入的第三方原件保留各自许可证，MIT 原件仍采用 MIT。完整说明见 [NOTICE](NOTICE)、[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 及 `vendor/` 内的原始许可文本。

网站截图与联系／赞赏二维码获准用于 README 展示，不作为可复用文章素材，也不授予冒用作者身份的权利。来源和使用边界见 [README 素材说明](assets/readme/README.md)。你的文章和外部图片仍需分别确认使用权。Light-WeChat 是独立项目，与微信或腾讯无隶属或背书关系。
