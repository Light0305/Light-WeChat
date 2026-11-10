---
name: light-wechat
description: 为微信公众号研究选题、撰写有证据的文章、审稿、配图、排版与移动预览；使用者配置自己的账号并明确授权后，可上传和回查草稿箱。
---

# Light-WeChat：公众号内容工作流

这是一套可独立安装的技能。研究、写作、审核、排版和预览工具均在本目录；不依赖维护者的电脑目录、账号或全局技能。
首次使用按 [README](README.md) 安装依赖，运行 `python scripts/doctor.py`。执行命令时使用本技能目录的绝对路径。
配置读取本目录 `chuanlab.toml`；凭据只读本目录 `.env` 或使用者明确指定的文件，不向上搜索其他项目。

## 范围与任务路由

- 按 [内容体系](references/content-system.md) 及配置中的栏目、读者与品牌开展工作。默认覆盖 AI、论文、计算机行业就业和用户提供材料的项目案例。
- 泛指“写一篇”：按 [请求入口](references/request-routing.md) 对适用方向研究精选，给出候选与首选理由，等用户选题。已有题目或明确授权自主选题时直接研究制作。
- 只要求审稿、排版或配图时，只完成该阶段。默认完整制作的终点是通过检查的本地预览；不把制作请求自动当作上传或付费服务授权。
- 公众号上传需要配置自己的账号、设置 `wechat.enabled = true`、将本篇 `delivery` 设为 `wechat-draft`，并明确授权上传这个版本；届时使用 `--confirm-upload`。所有测试只用合成夹具，不上传。
- 人工审核状态始终如实记录。草稿箱上传、接口回查和正式发布是不同状态；本技能没有群发或正式发布命令。
- 每篇在配置的 `workspace/articles/<工作标题>/` 独立保存。接续时先读本篇 `article.json`、简报、证据、正文、审阅及上传记录，不自动迁移其他工作流的旧稿。

## 1. 研究与选题

读 [研究接入](references/topic-research.md)，并实际读取
[AIHOT 精选流程](vendor/aihot/docs/selection.md)、
[适配评分提示词](assets/prompts/selection-score.md)、
[wewrite 选题规则](vendor/wewrite/skills/wewrite-topic/references/topic-selection.md)。
从读者问题、知识缺口和可增加的价值出发；事件类再预筛、归组与评分，常青内容不硬套新闻热度门槛。
评分必须来自实际材料与实际回执，不伪称独立模型验证。RSS/讨论只作为线索，结论回到原论文、官方文档与原始数据。

动笔前研究同题写法，记录标题承诺、案例、结构和本篇增量；没有传播数据不声称样本是爆款，不拼接他人正文。
`python scripts/create_article_workspace.py "工作标题" --kind paper --column papers --content-type paper-reading`
创建 v9 工作区。栏目可配置；类型为 news / technical / software / career / paper / interdisciplinary。

## 2. 写作与深度

读 [写作接入](references/writing.md)、[内容深度](references/depth-standard.md)，实际使用
[article-brief](vendor/wewrite/skills/wewrite-write/references/article-brief.md)、
[框架](vendor/wewrite/skills/wewrite-write/references/frameworks-quick.md)、
[内容增强](vendor/wewrite/skills/wewrite-write/references/content-enhance.md)。
先填 `brief.yaml` 与 `editor-brief.md`，说清读者、核心判断、信息增量、机制、贯穿案例、边界和最强反方。
按承诺决定篇幅，不固定字数或段落配额。事实、推断与观点分开；不虚构经历、测试、引用、数据或发表状态。
来源、主张、图片统一登记到 `evidence.json`，格式见 [文件契约](references/artifact-contract.md)。
按 [标题研究](references/title-packaging.md) 统一标题、摘要、封面与首屏的阅读承诺。

## 3. 编辑审核

读 [审核接入](references/review.md) 和 [原版编辑标准](vendor/wewrite/skills/wewrite-write/references/editorial-quality.md)。
逐项核查来源、机制、案例与边界，再做准确、观点、有用、合声、好读五项判断，直接改稿并重审。
将实际判断写入 `assessment.yaml`，运行 `python scripts/editorial_tools.py "文章目录"`；
原版计算器平均至少 4、单项至少 3、无阻断问题。分数和语言信号不能替代事实、深度或真实审阅。
需要时读取 [humanizer](vendor/humanizer/SKILL.md)，只自然化表达，不改变事实。

## 4. 配图与封面

读 [视觉接入](references/visuals.md)，按任务使用 baoyu 的 Type × Style × Palette 与实际提示词模板，
并参考归藏的构图与短标题方法。论文原图、真实界面与原始数据承担证据，生成图不冒充实测。
封面默认使用宿主生图工具制作有具体主体的主视觉，再以同一母图交付公众号宽图与方图，见 [封面规范](references/covers.md)。
仅有提示词不算完成。实际检查文字、缩略图和裁切；必要时使用有权使用的真实素材并记录理由。
宿主工具缺失或技术失败，且使用者已启用并授权备用服务时，才按 [生图配置](references/image-provider.md) 调用自配接口。
安全拒绝不切换供应商绕过；调用结果不明确时保留记录、不盲目重复付费。
联系卡默认省略，可由使用者配置自己的素材。

## 5. 排版与真实移动预览

读 [排版接入](references/layout.md) 与所选 [主题原件](vendor/gzh-design/references/theme-index.md)、
[通用组件](vendor/gzh-design/references/common-components.md)。默认 [Chuan 编辑版](references/chuan-editorial.md)，
按整篇组织字图与阅读节奏。开篇动效、章节标记、内容图背景和文末贴纸按 [排版动效](references/lsf-editorial.md) 执行。
避免机械堆卡片、阴影、标签和品牌装饰。它是对上游 Zen 语法的适配，不冒称未修改原件。
图表与代码保持可读、完整和可复制。运行实际 375/390 px 浏览器截图，查看首屏、章节、证据图、表格、代码和结尾；
HTML 生成或检查器通过不等于视觉验收。

## 6. 冻结与可选草稿交付

按 [交付命令](references/delivery.md) 执行 check → preview → 三类实际审阅 → delivery check → freeze。
冻结绑定正文、图片、提示词、配置、渲染器和审阅版本，只记录质量通过，不自动生成用户同意。
得到明确上传请求后，用自配账号上传或更新原草稿，再回读核对全文、封面与图片。
IP 白名单拒绝时保留原冻结包等待用户配置；结果不明确时先 reconcile-upload，不盲目重建草稿。
上传完成只报告草稿箱待人工审核，不能声称已正式发布。

## 上游与授权边界

上游原件在 `vendor/`；精确提交、逐文件哈希与实际接入见 [复用清单](references/upstream-study.md)。
执行阶段要读取对应成熟模块，而不是只概括仓库介绍。上游示例中的账号、路径、人格、服务授权和确认规则不自动适用于本用户。
原件不修改，适配代码在外层；用 `python scripts/verify_upstream.py` 复核。
本项目代码采用 AGPL-3.0-only；上游保留各自许可证，详情见 [第三方声明](THIRD_PARTY_NOTICES.md)。
