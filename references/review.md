# 编辑审核：wewrite 原标准、原代码

读取 [review 原流程](../vendor/wewrite/skills/wewrite-review/SKILL.md) 和
[editorial-quality](../vendor/wewrite/skills/wewrite-write/references/editorial-quality.md)。
顺序为对齐任务 → 逐项查来源 → 五项编辑判断 → 直接改稿 → 重审。
五项判断要包含 [深度复核](depth-standard.md)：在 reviews/editorial.md 标出解释主线、关键案例、
本篇增量、反例和读者迁移能力的具体位置及缺口。update 按其较窄承诺审核。
“有来源、分数够、排版通过”不自动等于内容完成。
准确、观点、有用、合声、好读各 1–5 分，平均至少 4、单项至少 3、无阻断问题才通过。
最多两轮常规编辑；仍不通过就删不可靠内容、缩小承诺并重新审阅，不贴“通过”标签了事。

实际判断写入文章根目录 `assessment.yaml`：

```yaml
decision: pass
pass_number: 1
dimensions:
  accuracy: 4
  viewpoint: 4
  usefulness: 4
  voice: 4
  readability: 4
blockers: []
major_issues: []
notes: "填写核对了哪些主张、修改了哪里和剩余边界，不能照抄此示例作为审阅。"
```

运行 `scripts/editorial_tools.py "文章目录"`，实际调用原版
[content_eval.py](../vendor/wewrite/src/wewrite/commands/content_eval.py) 和
[humanness_score.py](../vendor/wewrite/src/wewrite/commands/humanness_score.py)。
输出 `reviews/wewrite-editorial-eval.json` 与 `reviews/wewrite-style-signals.json`。
评分计算器判断编辑给出的分数是否达到门槛，它不能替编辑核实事实。
语言风险分仅定位重复、套话和节奏，不设“人类写作百分比”或机械通过线。

事实审阅记录具体原文定位、数字与口径、反证、版本和图片。编辑审阅记录读者问题、
新增价值、论证和实际改动。视觉审阅必须实际看过当前截图，写明首屏、章节、图表、代码、
封面对、文末、375/390 px 的观察和修复；脚本无报错不代表视觉优秀。
用 `article_workflow.py record-review` 绑定这三份报告，改稿后重新登记受影响审阅。

发布后按 [learn-edits 原方法](../vendor/wewrite/skills/wewrite-learn/references/learn-edits.md)
记录原稿/人工终稿差异，按内容类型、框架、人设限定范围。一条临时修改不自动变全局要求。
真实后台数据用于复盘打开、读完、分享及关注，缺数据不编“爆款规律”。
