# 文末动效素材库

| 贴纸设计 | 素材目录 | 可用素材 |
| --- | --- | --- |
| 01 星球变火箭 | `assets/footer-motion/planet-rocket/` | [六款配色](../assets/footer-motion/planet-rocket/palette-index.json) |
| 02 AI 图标旋转环 | `assets/footer-motion/ai-sticker-ring/` | [透明 GIF](../assets/footer-motion/ai-sticker-ring/ai-sticker-ring.gif) · [原始 HTML](../assets/footer-motion/ai-sticker-ring/ai_sticker_ring.html) |
| 03 趣味贴纸旋转环 | `assets/footer-motion/fun-sticker-ring/` | [透明 GIF](../assets/footer-motion/fun-sticker-ring/fun-sticker-ring.gif) · [静帧](../assets/footer-motion/fun-sticker-ring/fun-sticker-ring.png) · [原始 HTML](../assets/footer-motion/fun-sticker-ring/fun_sticker_ring.html) |

长文开工时先发 HTML 动效预览，请用户选贴纸设计或本篇不加。01 按文章挑配色，02 和 03 直接用固定的透明 GIF。新增设计时单独建立 `assets/footer-motion/<设计名>/`，将素材放入该目录，再更新 [选样索引](../assets/style-picker/catalog.json) 和上表。单一成品用 `file`，多配色设计用 `index` 指向配色清单。可选 `poster` 用于静态小样及开启减少动态效果时的预览。增减设计或配色时重新生成 HTML。见 [动效预览生成方式](style-picker.md)。

星球变火箭的六款配色使用同一动画，固定全局中轴，沿用修正后的星环前后遮挡和弧线。

## 01 星球变火箭的配色

1. 有指定款时直接选。其余先看用户给出的参考公众号，提取反复出现的品牌色、封面主色或插图配色，并判断整体偏暖或偏冷、明快或克制。白色页底和黑色正文通常跳过，若它们本身是设计配色的一部分，则计入判断。
2. 对照配色目录筛出主色、饱和度和风格都接近的款式。多款都适配时，可用本篇封面或配图的强调色进一步缩小范围。只有一款匹配时直接使用；有多个时在这个名单内随机选一个。若没有参考账号，按本篇封面或配图判断；两者都缺时，用原版粉紫试样并说明依据。
3. 在 skill 根目录执行抽取命令，把编号换成本篇筛出来的候选。脚本返回选中的编号和 GIF 本地路径。一次只放一枚，重试时沿用选中的文件。

```bash
python -X utf8 scripts/pick-footer-motion.py 03 06
```

## 插入和验证

- 上传原始 GIF 并在公众号正文文末居中插入。可从草稿实测过的 144px 显示宽度起步，按版面调整。若加图注，末尾省略句号。
- 01 为 500 × 500、61 帧、3.05 秒循环。检查变形中轴和星环遮挡。02 由用户给的 HTML 逐帧渲染，保留 28 秒公转与反转扶正，将摆动节拍对齐到整圈，透明 GIF 为 320 × 320、280 帧。分别在白底和文章底色上检查边缘、循环和透明区域。
- 03 由用户给的 HTML 逐帧渲染，保留 14 个贴纸的公转、反向扶正与摆动，摆动节拍对齐整圈。透明 GIF 为 320 × 320、300 帧、30 秒循环。HTML 的悬停互动用于独立浏览，GIF 自动循环。
- 保存后重新打开草稿，核对微信托管的 GIF、显示尺寸和正文。桌面编辑器与微信手机预览分别记录，只有实际在手机端打开才计为手机验证。
- 新制作 GIF 时，先确认生图工具实际返回的文件。若得到的是单帧图，组帧后核实 GIF，说明单帧素材和最终动画各自的生成方式。
