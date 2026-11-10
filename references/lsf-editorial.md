# 排版动效

开篇署名、章节标记、内容图背景和文末贴纸使用
[lsf-wechat-editorial-layout](https://github.com/leishifu666/lsf-wechat-editorial-layout)
`f442dc948e176e5a12ab6cb23fcff9827d500a06`。原件在
`vendor/lsf-wechat-editorial-layout/`，不改文件。轮换、截图加底和文末合成在 vendor 外，
入口是 `assets/lsf-editorial/selection.json` 与 `scripts/lsf_editorial.py`。

正文仍用 Chuan 编辑版。动效只加在开篇署名、章节标记、内容图和文末，不把正文改回卡片堆叠。

## 固定选择

默认署名文字是 ChuanLab。可以在 `selection.json` 里改 `author` 和 `footer.center_text`。
`ChuanLab` 会排成两行，上行 Chuan、下行 Lab。动图下方留 22px，再接正文。

正文段后 22px，左对齐，字重 300。章节标题居中，标题下 18px。表格按内容分列，表头浅底。
图注只写这张图是什么。正文不写「官方发布页」「模型文档」这类来源链接标签，文末不写资料核对说明。
来源留在 evidence.json。

开篇动效按文章顺序轮换，用完一轮再从头：

| 编号 | 名称 | 编号 | 名称 |
| --- | --- | --- | --- |
| 01 | 翻转贴纸 | 14 | 文字拆解 |
| 02 | 熔融显字 | 15 | 印章切页 |
| 05 | 像素扫描 | 17 | 弹性变形 |
| 07 | 彩色字块 | 19 | 文字涌动 |
| 08 | Logo 浮雕 | 29 | 虚线展开 |
| 09 | 光晕换词 | 30 | 色散辉光 |
| 11 | 像素换页 | 31 | 流墨显字 |

08 用署名文字，不另换 Logo。

章节标记在动态字母和动态数字之间按文章来回轮换。同一篇里每节抽一款，抽完再重复，相邻两节不用同一款。字母从 A 起，数字从 1 起。

正文里的图都加背景，证据图、解释图和截图一样处理。用原目录里除 `07 浅灰` 以外的全部 27 款。同一篇文章里每张内容图随机一款，彼此不重复；超过 27 张时用尽后再抽，并避开刚用过的一款。封面、开篇署名、章节标记和文末贴纸不加这层背景。

文末贴纸左边是 AI 图标旋转环，环心是两行署名，字为黑色。右边放使用者自己提供的二维码，不带旧卡片外框。
二维码由使用者准备，技能不附带维护者的联系卡或账号。

## 排版时执行

在技能目录运行：

```powershell
python -X utf8 scripts/lsf_editorial.py assign "<文章目录>" --chapters 4 --screenshot "images/界面.png"
```

命令把本篇结果写入 `editorial-motion.json`。同一篇文章再运行会沿用已经分到的署名动效和章节模式。截图列表变化时按原来的随机种子重算，保证同一张图还是同一款背景。`--reseed` 只重抽背景和章节花纹，不改这一篇已经轮到的署名动效。给内容图加背景需要已安装的 NumPy。

- 开篇：按 JSON 里的编号，用预览页把署名设好，导出 640×260 GIF，保存为 `images/intro-wordmark.gif`，放在正文最前。
- 章节：标记 GIF 复制到 `images/chapter-markers/`。按 `markers` 的顺序放在对应章节标题上方，文字标题仍保留。
- 截图：成品在 `images/backgrounds/`，正文用成品，原截图留在来源位置。
- 文末：先用自己的二维码生成贴纸，再把 `assets/brand/chuan-lab-footer.gif` 复制进文章。

```powershell
python -X utf8 scripts/lsf_editorial.py footer --qr "你的二维码.png"
```

单张截图也可以单独出图：

```powershell
python -X utf8 scripts/lsf_editorial.py render-screenshot "原图.png" 14 "成品.png"
```

全库预览：

```powershell
python -X utf8 scripts/lsf_editorial.py preview --output "预览目录\index.html"
```

预览页各组一次只能看中一款。正式文章以 `selection.json` 的轮换为准，不把预览里临时点中的一款写成新的默认。

## 来源

上游说明见 vendor 内的 `LICENSE` 和 `THIRD_PARTY_NOTICES.md`。开篇动效来自 Design.how Vault，章节标记来自 INITIĀLIS，截图柔光参数来自 Moonvy「旷」，馆藏背景来自公有领域藏品。AI 图标旋转环使用 Lobe Icons 的品牌标识，标识和商标仍归各品牌所有，只作辨识。
