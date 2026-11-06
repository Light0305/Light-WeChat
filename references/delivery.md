# 本地验收与可选草稿交付

命令从完整技能目录执行；使用已安装依赖的 Python。`<A>` 为配置工作区下本篇文章的绝对路径。
本地制作不需要账号或 API 密钥。

```sh
python scripts/article_workflow.py check "<A>"
python scripts/editorial_tools.py "<A>"
python scripts/article_workflow.py preview "<A>"
```

实际查看 375/390 px 首屏、正文转折、图表、代码和结尾。完成事实、编辑、视觉三份有具体依据的报告后登记：

```sh
python scripts/article_workflow.py record-review "<A>" --role factual --report reviews/factual.md
python scripts/article_workflow.py record-review "<A>" --role editorial --report reviews/editorial.md
python scripts/article_workflow.py record-review "<A>" --role visual --report reviews/visual.md
python scripts/article_workflow.py check "<A>" --delivery
python scripts/article_workflow.py freeze "<A>"
```

`record-review` 是登记，不代替真实审阅；不填写模板“通过”冒充检查。冻结复制 draft→public，绑定输入、预览和审阅，只进入 qa-passed。
源码或输入变动后，先重跑受影响的预览与审阅。不要直接修改冻结稿跳过质量检查。

## 用户请求上传时

先按 [README](../README.md) 配置自己的公众号、启用上传，并把本篇交付方式改为 `wechat-draft`。
该配置变化也需要重新验收。仅在用户明确要求上传当前版本后：

```sh
python scripts/article_workflow.py upload "<A>" --confirm-upload
python scripts/article_workflow.py verify "<A>"
```

每次上传都检查开关、文章交付方式、当前冻结包和明确上传动作。草稿状态绑定账号指纹，不借用其他配置或原稿的 media_id。
仅回查时也要求该用户自己的账号配置。成功后标记 `human_review: pending`；不能声称人工批准或已经发布。

| 情况 | 处理 |
| --- | --- |
| 原文、证据不足 | 补研究、缩小承诺或停止，不标 verified |
| 图片、生图或浏览器失败 | 保留材料和进度；不能以占位或检查脚本输出冒充完成 |
| 40164 白名单拒绝 | 记录实际返回的出口 IP 与同一冻结包，等待用户加好后恢复 |
| 凭据或权限错误 | 停止网络调用，说明本地配置动作，不输出密钥或持续试登录 |
| 上传超时/结果不明 | 保留 attempt，先 reconcile-upload，不盲目重建草稿 |
| 已上传、回查失败 | 标记 uploaded/unverified，修复只读回查，不重复上传 |

```sh
python scripts/article_workflow.py reconcile-upload "<A>"
```

找到唯一匹配才恢复 media_id；只有完整扫描未找到或确认未发送才可重传，结果含糊时保留暂停。
白名单已由用户确认加好且无需 reconcile 时，使用 `upload "<A>" --confirm-upload --resume-after-whitelist` 恢复同一包。
已有草稿修改优先更新原 ID；没有正式发布 API。测试与演示不得上传。
