# 可选、自配置的 Images API

默认使用宿主内置生图能力。本入口只作为使用者主动配置、授权的备用，或用户明确指定服务时使用。
技术不可用可切换到已授权备用；质量不满意先沿原路线修改，安全拒绝不能通过换服务绕过。
不附带服务商、模型或密钥，不读取用户全局生图配置，也不依赖其他已安装技能的私有运行环境。

在本机执行 `python scripts/configure.py images` 隐藏输入自己的密钥。编辑 `chuanlab.toml`：

```toml
[images]
enabled = true
base_url = "https://your-provider.example/v1"
model = "your-model-name"
```

地址和模型是占位，必须换成你自己的、实际支持 Images API 的配置。根地址会补 `/v1`；已有路径不重复追加。
配置目录中的 `.env` 保存 `IMAGE_API_KEY`。调用不会读取上级项目或其他全局凭据。

先把实际提示词保存在本篇 `prompts/`，例如 `prompts/cover.txt`，再运行：

```sh
python scripts/generate_image.py generate --prompt-file "<文章>/prompts/cover.txt" --out "<文章>/images/cover-master.png" --dry-run
python scripts/generate_image.py generate --prompt-file "<文章>/prompts/cover.txt" --out "<文章>/images/cover-master.png" --confirm-paid
```

dry-run 不读取密钥、不联网、不付费。实际调用需要启用服务及明确授权 `--confirm-paid`。
改图使用 `edit` 并追加一个或多个 `--image "<文章>/images/原图.png"`，按供应商实际支持设置 `--size`。
兼容接口的模型、编辑参数和尺寸支持各异；接口拒绝时保留记录，不擅自换模型或宣称能力已验证。
本入口使用 requests，不需要额外 SDK；它不是对任何具体供应商服务可用性的保证。

成功响应缓存到本篇 `.imagegen-private/responses/`；该目录可能含签名图片地址，不能提交或展示。
保存失败时使用 `recover --response-cache "<缓存JSON>" --out "<输出PNG>"` 恢复，只重做下载/解码，不再付费生成。
请求超时的结果记为 unknown，先查供应商记录，不把超时当成“没有生成”。不自动重试或换服务。

生成结束实际打开检查，在 `image-ledger.md` 与 `evidence.json` 登记实际服务、模型、提示词、生成/编辑输入和用途。
不能把自配服务标成宿主内置生图，也不能把生成图标成论文或产品的真实证据。
