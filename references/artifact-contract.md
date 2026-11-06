# v9 文件契约

每篇在配置的 `workspace/articles/<工作标题>/`。UTF-8 JSON 是机器账本；时间带时区。
`publication-status.yaml` 使用 JSON 兼容 YAML 保存，不手改状态冒充审核与授权。

| 文件 | 用途 |
| --- | --- |
| article.json | 类别、主题、宽/方封面、交付方式 |
| editor-brief.md / brief.yaml | 读者、问题、主张、结构和原版 wewrite 任务书 |
| evidence.json / sources.md / image-ledger.md | 来源、主张、图片及其详细依据 |
| draft.md / cover-brief.md / assessment.yaml | 当前稿、封面计划与真实五项编辑判断 |
| reviews/ / review-state.json | 事实、编辑、视觉报告及版本绑定 |
| images/ / prompts/ | 实际素材、成图、设计源和真实提示词 |
| publishing/preview/ | HTML、375/390 px 截图与预览清单 |
| public.md / publishing/package-lock.json | 冻结稿与整包哈希 |
| publishing/wechat-*/ / publishing/upload-attempt.json | 可选上传、回查及不明确结果恢复 |
| publication-status.yaml / publishing/revisions/ | 当前状态与旧版本 |

```json
{
  "workflow_version": 9,
  "kind": "paper",
  "layout": "gzh-chuan-editorial",
  "delivery": "local-only",
  "cover": "images/cover.png",
  "square_cover": "images/cover-square.png",
  "cover_profile": "shared-master-v1",
  "cover_master": "images/cover-master.png",
  "contact_card": false
}
```

`delivery: local-only` 禁止上传；需要上传时由使用者改为 `wechat-draft`，重新检查、预览、审阅与冻结。
`contact_card` 为 false，或使用者提供的文章内图片相对路径；默认没有品牌卡。
`kind` 为 news/technical/software/career/paper/interdisciplinary。Markdown 的 layout 注释必须与配置相同。
`column` 来自本地配置；`content_type`、`series_id` 和 `project_id` 记录内容关系。

## evidence.json

- `sources`：id、真实标题、url、type（primary/secondary/community/user）、status、accessed_at 与 locator。非用户材料的 verified 来源必须有真实原始 URL。
- `claims`：id、text、kind（fact/inference/opinion）、sources、status、locator、used。推断另填 reasoning；未核实的关键结论不能仅标低置信度就留在正文。
- `assets`：文章相对 path、role、source_ids、origin、rights、generated；生成图另填实际 generator 与已保存的 prompt 路径。

role 为 evidence/explanation/editorial/cover-master/cover/square-cover/brand。
证据图必须真实且追溯到已核查来源；生成图不能充证据。宽图与方图的 `derived_from` 指向同一个母图。
所有正文图、母图和封面入账；使用依据需实际核实，程序只检查完整性。

审阅绑定报告、输入与截图的 SHA-256。修改文字、素材、配置、提示词或渲染代码会使相关验收失效。
冻结不自动进入 user-approved；只有明确上传请求才记录绑定账号和版本的 draft-upload-only 授权。
