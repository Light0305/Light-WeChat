# INITIĀLIS 动态数字

按正文顺序放 1、2、3、4……。正式排版按 [原站画廊抽取流程](../chapter-markers.md) 取得样式参数，再用数字引擎渲染。朱红卷纹、橄榄四瓣、钴蓝花框、粉蓝藤枝是预览与离线备用款。每款的 `preset.json` 记录画廊种子、格子坐标、原款链接和原始参数，`0.gif` 至 `9.gif` 可离线使用。

新增数字样式时，用 INITIĀLIS 的 `Field.at(q, r)` 读取指定画廊格子的参数，选出在 42px 可辨认且保留生长动效的样式。保存原始参数和来源，生成数字 GIF，再把目录名追加到 [styles.json](../../assets/chapter-markers/numbers/styles.json)。

## 抽取和上传

正式稿按原站抽取记录生成 GIF。经用户选择使用离线备用款时，用以下命令抽取。

```sh
python -X utf8 scripts/pick-numeric-chapter-markers.py --chapters 4
```

命令输出每节的数字、样式、素材路径和随机种子。首次排版抽一次，保留输出；素材池相同时，使用 `--seed` 可重现同一次抽取。首轮用过的样式从候选里移除，池空后重新抽，首个候选也避开上一节。

按输出通过公众号图片库上传 GIF，再套用 [正文模板](../../assets/article-template.html) 的 42 × 42px 居中标记。数字填入 `CHAPTER_LABEL` 和图片替代文本。保存后用微信实际预览确认动效。图片库中的 GIF 保留透明背景，文章截图配图走 [内置背景流程](../style-picker.md#截图背景)。

## 重渲染和两位以上数字

素材路径为 `null` 时，使用抽中的预设生成对应的完整数字标记。生成器支持一至三位数字。上游默认只附 A–Z 大写字形，数字模式在 [INITIĀLIS](https://github.com/azlen/initialis/tree/6cf93f7d3d2922efdbeb86cafa27f39758be9398) 的本地副本上补入 [Cinzel 900](https://github.com/google/fonts/blob/main/ofl/cinzel/METADATA.pb) 的数字轮廓。渲染时换成章节数字、限制字形大小，沿用画廊格子的边框、配色、装饰和动画参数。字形来源文件的 Git blob 为 `d218a0b9c8879fd5a708872cc0ef357e507b35ca`，许可见 [Cinzel-OFL.txt](../../assets/chapter-markers/numbers/Cinzel-OFL.txt)。

1. 取固定版本的 INITIĀLIS 源码，将 Skill 副本和引擎放在同一个临时工作目录下。在该目录运行 `python <Skill目录>/assets/chapter-markers/numbers/prepare-engine.py initialis-upstream numeric-engine`。生成的是新目录，源代码目录可直接复用。
2. 在同一个临时目录运行 `python -m http.server 8876 --bind 127.0.0.1`，用浏览器打开 `http://127.0.0.1:8876/<Skill目录>/assets/chapter-markers/numbers/render.html?upstream=http://127.0.0.1:8876/numeric-engine/`。
3. 输入数字、选择抽中的样式并下载。浏览器需支持 WebGL2 Worker。预生成的单个数字 GIF 可直接离线取用。
