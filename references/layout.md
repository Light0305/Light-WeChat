# 排版：按整篇文章做编辑设计

## 当前默认：Chuan 编辑版

默认避免组件堆叠与塑料感。新稿使用 `gzh-chuan-editorial`，
具体设计、语义区块与装配骨架见 [chuan-editorial.md](chuan-editorial.md)。
开篇署名、章节标记、内容图背景和文末贴纸按 [排版动效](lsf-editorial.md) 轮换。
它吸收原 Zen 的编辑语法，重新设计正文与媒体，属于明确标注的本项目适配，
不冒称是上游未经修改的第七套主题。六套原件、来源哈希与检查器继续保留。

实际执行顺序是：读文章 → 确定首屏/论证/证据/收束的节奏 → 选择必要区块 → 排完整篇 →
375/390 px 查看真实截图并修改。不要先挑十几个卡片，再往里面填段落。
正文左对齐、段后 22px。内容图加背景；封面、开篇署名、章节标记和文末贴纸不加这层背景。
表格按内容分列。图注只写图是什么。

## 六套原主题：参考与可选路线

先读 [上游排版流程](../vendor/gzh-design/SKILL.md)、
[主题索引](../vendor/gzh-design/references/theme-index.md)，再完整读取选中主题和
[通用组件](../vendor/gzh-design/references/common-components.md)。
主题确认由本项目自主处理，其他操作按实际组件与文章类型配方执行。

| article.json 与 Markdown layout | 原主题组件库 |
| --- | --- |
| gzh-moyu-green | [摸鱼绿](../vendor/gzh-design/references/theme-moyu-green.md) |
| gzh-graphite-minimal | [石墨极简](../vendor/gzh-design/references/theme-graphite-minimal.md) |
| gzh-red-white | [红白](../vendor/gzh-design/references/theme-red-white.md) |
| gzh-moyu-ticket | [摸鱼票据](../vendor/gzh-design/references/theme-moyu-ticket.md) |
| gzh-olive-journal | [橄榄手记](../vendor/gzh-design/references/theme-olive-journal.md) |
| gzh-zen-whitespace | [留白禅意](../vendor/gzh-design/references/theme-zen-whitespace.md) |

`<!-- layout: gzh-moyu-green -->` 与 article.json 保持一致。
选择六套原主题时，渲染器使用 `gzh_components.json` 中从原库 HTML 代码块提取的组件，
保留每套不同的章节、段落、引用等结构；提取的源文件、块序号和哈希都有记录。
它不是用六种颜色套同一模板。默认组件支持章节编号、行内强调、图、列表、表格与代码。

需要更丰富结构时，先查该主题“文章类型 → 组件组合配方”表：教程用步骤，测评用对照，
论文用真实数据/局限说明，复盘可用时间线。直接复制主题内的真实 HTML 组件到正文，
填写实际内容，保持内联样式；带 style 的 section 在转换时原样保留并接受原版验证。
同一篇不混主题。不要为了用卡片把普通连续论证全拆碎，也不要让所有强调都变粗体。
遵循原版的关键词下划线层次：排版时按语义给重点段选择短语，以 `<u>短语</u>` 标记；
转换器使用原主题索引指定的下划线 CSS。没有重点的段落不硬标，避免整段划线。

上游的 span leaf 结构在此保留，以兼顾复制粘贴兜底；API 路径仍通过回读实际验证，
不把粘贴经验夸成官方 API 保证。为保证代码可复制执行，代码区保留原空格/换行，
不采用示例中的全角空格替代；任意行列表格按原主题表格样式扩展，窄屏检查真实内容。

原版检查器已进入 article_quality 自动检查，也可单独运行：

```powershell
python "<技能>/vendor/gzh-design/scripts/validate_gzh_html.py" "<文章>/publishing/preview/wechat-body.html"
```

修复 ERROR，逐条处理 warning；代码/URL 不全角化。截图检查文字与图片、表格/代码
可读性及手机端段距，不以桌面预览代替手机检查。
需要新主题时用 [theme-generator](../vendor/gzh-design/references/theme-generator.md)
生成完整区块库，再跑原版 component_lint，不临时写几条 CSS 宣称新增完整主题。
前一尝试的 editorial/paper/guide 仅留兼容已有 v9 夹具，不再作为新稿默认主题。
