# 章节标记样式

按章节在正文中的实际顺序标记。字母模式从 A 开始，超过 Z 继续用 AA、AB、AC……；数字模式从 1 开始，依次用 2、3、4……。图注、正文列表和文章标题沿用原稿自己的编号。

| 模式 | 用途 | 文件 |
| --- | --- | --- |
| `initialis` | 居中彩饰字母，每节随机抽一款 | [样式与上传说明](chapter-markers/initialis.md) |
| `numbers` | 居中彩饰数字，每节随机抽不同的边框与花纹 | [数字素材池与抽取说明](chapter-markers/numbers.md) |

正式排版每篇从 [INITIĀLIS 原站画廊 #54852375](https://initialis.azlen.me/#54852375) 抽款。样式预览里的四枚标记只用于比较字母与数字模式。原站格子每轮随机抽取，同轮每个格子只用一次，换轮时避开相邻重复。抽完保存每节的格子坐标、样式参数和编号，HTML、上传和复查共用这次结果。

在浏览器打开可访问 Skill 目录的本地静态页，导入 `assets/chapter-markers/gallery.mjs`。先抽取并保存 JSON，再生成每节的 GIF。字母模式用原站渲染器，数字模式将同一原站参数交给补入数字字形的 [本地引擎](chapter-markers/numbers.md#重渲染和两位以上数字)。

```js
const { drawGalleryChapters, createGalleryMarkerRenderer } =
  await import("/<Skill目录>/assets/chapter-markers/gallery.mjs");
const selection = await drawGalleryChapters("initialis", 4);
const render = await createGalleryMarkerRenderer(selection.mode);
const images = await render(selection.chapters[0]);
```

数字模式调用 `createGalleryMarkerRenderer("numbers", numericEngineUrl)`，引擎地址末尾加斜线。每次 `render(chapter)` 返回按顺序排列的 GIF Blob 数组。保存为任务内素材并目检 42px 下的清晰度。遇到原站访问失败时告知用户，再按用户选择使用离线素材或等原站恢复。

新增模式时，素材独立放在 `assets/chapter-markers/<模式名>/`，规则独立写在 `references/chapter-markers/<模式名>.md`，再加到表中。

新增模式或更新某模式下的款式时，同步刷新章节标题 HTML 动效预览。见 [动效预览生成方式](style-picker.md)。
