# 05 · Vidu 组件版与直播工作台

回到 [主教程](../README.md)。接口理解基于固定上游源码；平台权限和 API 变化以 [Vidu 控制台](https://platform.vidu.cn/)官方文档为准。

## 1. 当前工作台不是全托管 quickstart

| 接入 | 职责 |
|---|---|
| `/live/s_avatar/realtime` | 你之前看到的实时全托管 Demo 路线 |
| `/live/s_avatar/component` | 本仓库上游工作台实际使用的组件版路线 |

组件版由本地程序调 LLM、合成语音、发送音频和动作。HTTP 创建场次 → WebSocket 控制 → RTC 收远端音视频，共同形成完整连接。WebSocket 只连上，不说明浏览器已经订阅到视频。

## 2. 哪些参数最重要

| 配置 | 说明 |
|---|---|
| `model` | 上游组件版的模型字段，模板为 `vidu-s2` |
| `vidu.host` | 域名，不带 `https://` |
| `vidu.api_key` | 服务端保存的 Key，不要写进 HTML |
| `avatar.avatar_id` | 字符串形象 ID |
| `avatar.image_uri` | 如果有值，上游优先使用它 |
| `rtc.mode` | 新手用 `managed` |
| `rtc.managed_provider` | 上游支持的托管 RTC provider，模板为 `artc` |
| `rtc.managed_recording` | 是否开启新场次服务端录播 |
| `llm.key_file` | 大模型 API Key 私有文件 |
| `tts.voices_dir` | 本地音色库目录 |

使用 managed 模式先不自行申请 RTC 的 app key。若出现具体的 RTC 权限/配置错误，应按当前平台的开通条件核对，而不是随意填一个 secret。

Key ID 不能代替完整 API Key。形象、Key 和动作库的账号权限必须匹配。`avatar is still processing` 要等平台处理完再试，不是重启本地 Python 就能加速。

## 3. 工作台如何操作

1. **右侧顶端**：连接状态、音色、设置。
2. **右侧工具**：点播歌单、快捷指令、参考图、口播工作台。
3. **右侧对话**：输入消息，走 LLM → 本地 TTS → 渲染。系统事件可展开查看详情。
4. **底部**：开始/结束连线、录播、拉取录播、直接动作、打断、全屏画面。
5. **右下角统计**：可拖动；双击或聚焦后按 Home 复位；箭头微调位置。
6. **中间分隔线**：拖动调整右栏，双击恢复默认宽度。

“直接动作”不会像聊天一样先问 LLM，但平台是否执行仍取决于动作库、权限、节流和当前状态。不要把“请求已受理”视为动画已经播放。

## 4. 更换配置后要不要重启

- 浏览器布局、CSS：Ctrl+F5。
- 设置面板保存：通常热更新，部分字段仅对下一场会话生效。
- 手改 `config.json`：调用本地 reload 或重启舞台；不要以为自动读到了新文件。
- 人物 / Key / RTC / 录播开关：结束当前场次，重新连线验收。
- 本地音色：影响之后生成的音频，现有队列不会重新合成。
- 加速代码 / CUDA / Python 包：先停止语音服务，再重新启动。

手改配置后的本地 reload，PowerShell：

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8795/api/settings/reload | Out-Null
```

`Out-Null` 是为了避免把返回的配置意外打印出来。服务仅绑定本机回环地址，不要在没有鉴权设计时改成公网可访问。

## 5. 更换成其他 OpenAI 兼容 LLM

先确认该服务确实支持 Chat Completions，且模型有权限。`base_url` 会由上游追加 `/chat/completions`，因此有的服务填 `https://example.com/v1`，有的官方服务填根 URL。不要重复成 `/v1/v1`。

模板用 `thinking: disabled` 让短互动直接输出回答；若其他服务不识别这个字段，清空 `thinking`，不要盲用 DeepSeek 专属参数。

本机曾配置过从 DSH 登录读取账号授权的适配器 8796。公共教程不复制账号凭据，也不依赖这条非通用认证路径。已有电脑继续保留原适配器即可；新手重新部署优先使用自己的正式 API Key。

## 6. 录播

先开启录播，再新建场次。挂断后等服务端处理，再点击“拉取录播”；没有在那场开始时开启，通常不能事后补录。是否可用、存储时长和费用以平台为准。

打开网页或本地 TTS 试听不等于创建付费场次；点击开始连线会进入云端会话流程。调试完要确认挂断，不要只关页面。
