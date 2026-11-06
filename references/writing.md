# 写作：直接沿用 wewrite 的任务书与七种框架

同时读 [内容深度](depth-standard.md)，按本篇形态决定需要走通的机制、案例和判断。
简报中的长度按承诺调整，原版示例不是 1200–2500 字硬上限。长文不等于深度；
短动态也不强加教学结构。系列稿件再读 [内容体系](content-system.md)。

依次读原版 [任务书](../vendor/wewrite/skills/wewrite-write/references/article-brief.md)、
[框架](../vendor/wewrite/skills/wewrite-write/references/frameworks-quick.md)、
[增强策略](../vendor/wewrite/skills/wewrite-write/references/content-enhance.md)。
`create_article_workspace.py` 已直接提取原版 brief.yaml 模板；先填它再写正文。

| 原版字段 | 本篇必须说清 |
| --- | --- |
| audience.who/context/question | 哪一类读者、在什么场景、真正在问什么 |
| goal.takeaway/action | 一个读后结论和相称的行动或判断方法 |
| thesis.statement/novelty/boundary/counterpoint | 主张、信息增量、边界、最强反方 |
| personal_materials | 本次用户明确提供的经历；没有则 false，不编亲历 |
| sections.purpose/claim_ids | 每节推进的任务与主张，去掉无关段落 |

原版要求的 claims/sources 关系在本项目统一落到 `evidence.json`，字段映射见
[artifact-contract](artifact-contract.md)。`editor-brief.md` 保留给人读的选题与包装决策。

框架直接用原版七种：痛点、故事、清单、对比、热点解读、观点、复盘。
论文通常用“问题—方法—结果—边界”的推演组织，技术教程通常先呈现具体任务和可用操作，
工具对比先定共同标准，职业文先限定人群与选择条件。它们不是统一章节配额。

增强也按原版执行：观点补有依据的新角度；教程补条件、成本、失败信号；对比补决策标准；
故事只用有出处细节。标题、摘要、封面与开头共同兑现一件事，不为了反转制造假内幕。

参考 [技术码农](../vendor/wewrite/skills/wewrite-write/personas/tech-coder.yaml) 的精简与版本意识，
及 [行业观察者](../vendor/wewrite/skills/wewrite-write/personas/industry-observer.yaml) 的解释方式。
不沿用其中句长、第一人称/情绪比例配额，不把示范语句当真实经历。
必要时用 [humanizer 原版](../vendor/humanizer/SKILL.md) 查虚假权威、夸大意义、套话和机械转折，
保留技术术语和证据边界；不靠加入错别字、吐槽或随机碎句“去 AI 味”。

起草完整版本，审稿直接改具体段落。代码可运行性、版本和测试结果逐项说明；仅是示例就标为示例。
正文稳定后进入原版编辑质量门槛，不以生成了一份 Markdown 作为写作完成。
