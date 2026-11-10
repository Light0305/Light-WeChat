# INITIĀLIS 彩饰首字母

字母按 A、B、C、D……顺排。正式排版按 [原站画廊抽取流程](../chapter-markers.md) 生成。紫金方印、墨色卷枝、玫红花纹和墨绿边框是预览与离线备用款，每款都备齐 A–Z 透明 GIF。

## 用在公众号

1. 按 [原站画廊抽取流程](../chapter-markers.md) 生成，顺序上传到微信公众号图片库。经用户选择使用离线备用款时，可在 Skill 根目录运行 `python -X utf8 scripts/pick-chapter-markers.py --mode initialis --chapters 4`，按输出的 `assets` 取 GIF。
2. 将微信上传后的 URL 填入 [正文模板](../../assets/article-template.html) 的 `UPLOADED_CHAPTER_GIF_URL`。单个 GIF 设 42 × 42px，居中放在原章节标题上方。字母填入 `CHAPTER_LABEL` 和图片替代文本。AA、AB 等组合用两个相邻的字母图，中间留 4px。
3. 保存草稿后重新打开，核对字母与标题的对应关系、位置与大小，并检查微信图片仍是多帧 GIF。要确认手机播放情况，在微信客户端打开草稿预览。

## 修改配色或动画

字母素材可离线复用。[styles.json](../../assets/chapter-markers/initialis/styles.json) 登记可选目录，`.` 对应紫金方印。需要新增样式时，在新目录写入 `preset.json` 并登记目录。启动本地静态服务，打开 [render.html](../../assets/chapter-markers/initialis/render.html) 选择样式并导出 A–Z。导出页调用官方渲染器，需浏览器支持 WebGL2 Worker。可通过 `?upstream=http://127.0.0.1:端口/` 指向本地托管的 [上游源码](https://github.com/azlen/initialis) 固定版本。新增样式后刷新 [HTML 动效预览](../style-picker.md)。

GIF 采用 192 × 192px 源图、固定色板和单一透明索引。每个字母 34 帧，循环约 4.3 秒。字体及代码许可见 [INITIĀLIS 第三方声明](https://github.com/azlen/initialis/blob/6cf93f7d3d2922efdbeb86cafa27f39758be9398/THIRD-PARTY.md)。
