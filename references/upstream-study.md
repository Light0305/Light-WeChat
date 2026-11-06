# 实际复用清单

原件直接进入项目技能的 vendor，原版权/许可证保留，精确提交与逐文件 SHA-256 见
[manifest.json](../vendor/manifest.json)。这些模块均有当前入口，不是放进目录当摆设。

| 上游 | 带入的实际文件 | 进入默认流程的位置 |
| --- | --- | --- |
| [AIHOT](https://github.com/KKKKhazix/AIHOT) | 30 个行业提示词、精选/校准与来源文档、门槛配置 | 研究读取预筛、结构化、归组提示词；research_selection 提取原门槛，准备两轮原评分输入并汇总回执 |
| [wewrite](https://github.com/imraywang/wewrite) | 10 个技能模块及其参考/人格，content_eval.py、humanness_score.py | 建工作区直接提取原 brief；写作读原框架与增强；editorial_tools 运行两份原代码，交付检查重算原编辑门槛 |
| [baoyu-skills](https://github.com/JimLiu/baoyu-skills) | article-illustrator 与 cover-image 的完整技能、提示词、类型/风格/配色/工作流参考 | 配图和生成式封面按原参数系统与对应提示词模板制作，不复制首次问卷/全局安装 |
| [gzh-design-skill](https://github.com/isjiamu/gzh-design-skill) | 六套主题完整 HTML 组件库、通用组件、生成器、两份检查器及预览工具 | 本地后端实际装配提取的原 HTML；article_quality 调原 validate_gzh_html；复杂组件按主题原配方直接填入 |
| [guizang-social-card-skill](https://github.com/op7418/guizang-social-card-skill) | 两套完整种子模板、28 种布局配方、10 个配色、背景素材、生产与 QA 参考、R1–R9 检查器 | cover_pair 从种子填稿；validate_cover_deck 运行原检查器；布局/短标题/图像处理按原参考 |
| [humanizer](https://github.com/blader/humanizer) | 完整 SKILL 与 MIT LICENSE | 写作/编辑时处理夸张、虚假归因、模板表达，保留事实与术语 |

AIHOT/wewrite/baoyu/humanizer 为 MIT；gzh-design 原 LICENSE 为 AGPL-3.0-or-later，
归藏保留 AGPL LICENSE 与商业许可说明。仓库 package.json 的 license 字段与 LICENSE
不一致处以随附的 LICENSE 内容为准，不能改成自创代码后抹去来源。

## 适配边界

1. 所有 vendor 原件逐字保留；Chuan Lab 接口、模板提取结果与说明在 vendor 外。
2. AIHOT 活跃评分提示词只改读者/领域/细分论文的适用范围，五轴权重和输出不改。
3. wewrite 账本映射为本项目 evidence.json；路径从本技能配置读取，上传须使用者自己配置并明确授权。
4. gzh 保留原结构与 span leaf；表格扩展任意行列，代码保留可执行空格，不用全角替代缩进。
5. 归藏原母版 CSS 保留，导出稿去 CDN 依赖、使用本机字体，增加封面内容槽位。
   检查器适配跨平台文件 URL 与本地依赖定位，九条规则不改。
6. 制作期间持续完成质检；账户、付费调用和上传授权以当前使用者为准，上游示例不授予任何外部操作权限。
7. 当前默认 Chuan 编辑版明确标注为 Zen 方法的本项目适配；封面优先实际调用宿主生图工具。
   原主题与母版仍可选，不能拿模板和提示词代替最终视觉交付。

doocs/md、RSSHub、Folo、TrendRadar、MarkItDown 仅作为可选外部研究方向；本分发不附带其服务或私有研究目录。
详细许可证范围见 [第三方声明](../THIRD_PARTY_NOTICES.md)。
