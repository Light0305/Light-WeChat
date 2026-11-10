# Design.how 效果库

[Design.how Vault](https://design.how/vault) 的技能及其适配模板位于 `assets/design-how/<名称>/`。原有素材取自上游版本 `b4140241a1b1b3d0b417c8c01b3462b0388f6a09`，许可保存在 `assets/design-how/LICENSE`。在册的 27 款与翻转贴纸、熔融显字排在同一个网格。维护或查找具体款式时按 [动效索引](../assets/design-how/catalog.json) 的编号和 `kind` 定位。

| 分类 | 用途 |
| --- | --- |
| `text` | 用单句或署名 |
| `scenes` | 支持分镜文案，每行一句 |
| `logo` | 08 Logo 浮雕，选中后出现上传控件，可使用自己的 Logo 或署名 |

- Word Carousel 和 Roll Type 复用上游 Canvas 动效，支持文章短句轮换。Roll Type 每次换句也切换背景。
- 其余款使用预制 WebP 小样，选中后在右栏用可编辑文案运行效果。逐字翻牌按实际字宽适配，叠字收拢按画布高度保留上下叠字。
- 29 虚线展开逐字测量、保留字间空隙并整体等比缩放。展开后字形分开，收拢时聚回中轴。适配代码从 [字形布局](../assets/intro-wordmark/dash-cascade-layout.ts) 进入。
- 31 流墨显字取自 [Smear Type](https://design.how/vault/smear-type)。开篇横幅等比取原场景的中段，短署名单行居中，长署名分两行按实际字宽缩放。预览、PNG 和 GIF 使用同一画布比例。GIF 保留 48 帧、每帧 50ms，静帧在文字完整显现时取样。
- 04、21 保留空号。导出用当前文案或 Logo 生成 640×260 循环 GIF，文件名包含显示编号和款名。较长效果的 GIF 使用较低采样帧率。

Agent 提炼按 [开篇署名流程](intro-wordmark.md) 回填。优先使用正文里的对象、动作和判断。单句款给 1 条，分镜款可给 1–4 条，每条尽量简短。
