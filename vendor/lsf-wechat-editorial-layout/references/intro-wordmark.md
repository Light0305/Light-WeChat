# 开篇动态署名字标

翻转贴纸与熔融显字参考 [Bakai Lab](https://www.bakai.me/lab) 的 Tumble type 和 Molten wordmark。两款编号保存在 [选样索引](../assets/style-picker/catalog.json)，其余编号以 [Design.how 效果索引](../assets/design-how/catalog.json) 为准。03 是文字点阵，12 是词语轮播，25 是滚动换页。源码集中在 `assets/intro-wordmark/`。

## 选样与进入公众号

1. 生成选样页时传 `--author "作者公开显示名"` 作为初次打开时的默认值。沿用用户确认的署名或缩写。只知道中文名时直接用中文，不替用户编缩写。输入会即时更新两款动效，并随「复制选择」复制。点署名文字旁的「保存」后，同一浏览器在同一预览地址（协议、主机和端口）打开时会自动填入上次保存的文字。
2. 「Agent 提炼文章」首次显示空白回填框。复制选择时，按所选效果附单句或分镜提炼任务。收到本篇正文后，返回能直接粘贴的短句。用户回填后可手改，文章开篇实时更新。使用 `--intro-line` 只载入已确认的文案。
3. 点左侧小样，右侧文章开篇实时切换。08 Logo 浮雕可上传 PNG、JPG 或 WebP。优先用透明底 PNG，导出前在预览中检查轮廓。点「导出 GIF」或「导出 PNG」输出 640×260 的循环 GIF 或静帧，宽高比约 2.46:1。翻转默认将单个署名重复为两行。轮播与换页见 [Design.how 效果库](design-how.md)。
4. 公众号使用实际上传的 GIF 地址。把 [开篇图文片段](../assets/intro-wordmark/wechat.html) 放在文章首段之前，替换图片地址及署名。图片占正文栏宽，下方留 24px，署名作为替代文字。封面和文章标题仍使用公众号自己的字段。
5. 在授权的公众号草稿中检查位置和尺寸，打开微信预览看 GIF 是否播放。只有在真实微信中播放过，才记录为公众号动效实测通过。

## 维护

在 `assets/intro-wordmark/` 内运行 `npm ci`、`npm run build` 重建离线脚本，再重新生成 HTML。一般选样和改字直接使用已打包的脚本。

React 组件 `Wordmark` 使用 `mode="tumble"` 或 `mode="molten"`，传 `wide` 使用公众号横幅。翻转款接收 `text`、`stagger`、`lineStagger`、`loop`、`turn`、`turnStart`、`bob`、`extrude`、`band`、`hairline`、`face`、`plate`、`ink`、`ground` 等参数。避免 plate 与 ground、face 与 ink、plate 与 ink、face 与 plate 同色。熔融款可以传入一个词或一组词，使用相同播放时钟的多份词组预览同步换词。减少动态效果设置下显示定格。
