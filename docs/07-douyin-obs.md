# 07 · 抖音弹幕与 OBS：最后再接

回到 [主教程](../README.md)。先确保手动输入已能完成文本、声音和画面三项验收。

## 1. 数据流和端口

```text
你的抖音直播间
  → douyinLive :1088（采集）
  → 上游 tools/douyin_relay.py（格式转换）
  → 工作台 :8795/api/danmaku
  → 过滤 / 节流 / LLM / TTS / Vidu
```

使用上游 [jwwsjlm/douyinLive](https://github.com/jwwsjlm/douyinLive)，固定官方 release v2.3.2。脚本校验 Windows x64 ZIP 的 SHA256，再解压；仓库不打包 EXE，不包含 Cookie。

本教程设 **1088**，不要照旧 README 把 relay 设成 1089。端口与实际配置必须一致。

## 2. 安装与启动

Windows PowerShell，进入教程目录：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\Install-DouyinCollector.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\Start-Danmaku.ps1 -Room https://live.douyin.com/数字房间号
```

也可以只填数字房间号。这里不是昵称、抖音账号 ID，也不是短分享链接；先在浏览器打开真实直播间并复制 `live.douyin.com/...` 地址。

脚本先启动/复用采集器，再在前台运行 relay；Ctrl+C 只停 relay，后台采集器仍可能在运行。切房间前结束旧 relay，避免启动多份造成重复回答。

## 3. 按顺序验收

1. 启动后的本机健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:1088/health
Invoke-RestMethod http://127.0.0.1:1088/api/v1/rooms/数字房间号/status
```

2. 从真实房间发送一条新弹幕，看采集端/relay 是否收到了消息。
3. relay 正常、舞台连线正常且互动开关允许时，再看舞台是否生成回复。
4. 默认按到达顺序逐条回答，先称呼观众昵称，不复读弹幕原文；相同事件 ID 重放会去重，过滤掉的内容不回答。队列最多 200 条，满时拒收新条，保留已排队的问题。
5. 观察一次完整回复后，再验收真实直播音画。

**匿名配置未必能接入所有房间。** 按采集器的具体错误决定是否需要合法获取并在本机配置 Cookie；只改 `xiaoya-runtime/douyin-live/config.yaml`，不要贴到聊天或仓库。平台协议可能变化，本文没有把模拟测试写成真实采集成功。

## 4. 入场欢迎、按序回答和句尾打断

2026-11-14 增补：采集器的 `WebcastMemberMessage` 会转成入场事件，不需要识别屏幕文字。

- 画面底部显示「（昵称）来了，欢迎～」，约 6 秒自动淡出；右侧保留一条入场记录。
- 没有待答问题时，数字人会说一句欢迎；有问题时先回答，欢迎排在后面。
- 同一观众 60 秒内反复进入不重复欢迎。未带昵称的入场事件不朗读。
- 回答先说观众昵称，再直接答问题；昵称与首句一起合成，后续句子不重复叫名。缺少昵称时直接回答，不改念账号 ID。
- 问题按到达顺序回答，VIP 不插队；欢迎、礼物感谢、空闲搭话让位给问题。
- 正常打断会完成当前整句再停止后续句子；保留云端已经收到的句尾音频，不发送清缓冲指令。实际听感仍受 RTC 网络和播放缓冲影响。
- 主播操作、歌曲保留原有控制权；「停止演唱」和挂断仍立即生效。
- 右侧字幕标题显示待答及待欢迎数量。只有舞台已经连线才会接收并安排播报。

新安装由模板自动写入下列选项；升级现有安装先备份，停播后换新运行目录并迁移私有配置，不要强制把补丁覆盖到已修改的源码上。

```json
{
  "danmaku": {
    "queue_mode": "fifo",
    "answer_call_nick": true,
    "queue_max_items": 200,
    "welcome_enabled": true,
    "welcome_cooldown_s": 60,
    "read_interval_ms": 1000,
    "answer_max_sentences": 0,
    "batch": {"enabled": false, "read_max": 0}
  },
  "session": {"finish_sentence_before_interrupt": true}
}
```

出现 `ROOM_OFFLINE` 表示保存的房间尚未开播，连接会继续轮询；它不代表数字人已建立收费连线。

补丁应用顺序：银白界面（可选）→ 语音完整性 → 弹幕队列。测试不创建 Vidu 场次：

```powershell
$env:PYTHONPATH = "C:\AI\xiaoya-runtime\stage"
& "C:\AI\xiaoya-runtime\stage\.venv\Scripts\python.exe" -m unittest discover -s .\tests_stage -v
```

## 5. OBS / 直播伴侣

1. 安装并打开你使用的官方直播工具。账号资格、推流方式及平台规范按平台当前要求办理。
2. 新建场景，先添加**窗口捕获**，选择打开舞台的浏览器窗口。对于当前需要点击连接和 RTC 的工作台，这比一开始就上 OBS 无界面浏览器源更容易排错。
3. 调整裁切，只留下人物区域；需要右下角统计时保留该区域。不希望显示后台按钮就裁掉底部操作区。
4. 设置画布尺寸，比如横屏 1920×1080，或按你的平台要求设竖屏。
5. 先做本地 20 秒录制，回放检查画面、口型、音量和字幕，而不是直接正式开播。

如果改用 OBS 浏览器源，它有独立的页面实例、播放策略和权限状态；不能假定你在 Chrome 已连接就等于 OBS 那个页面也连接。需要单独按实际行为验证，别同时开两场云端会话。

## 6. 声音说两遍 / 有回音

先检查**重复播放和重复采集**，不要先改模型：

- 舞台页是否开了两个标签并都在播放？
- relay 是否启动了两份，导致同一弹幕触发两次？
- OBS 是否既采桌面音频，又采同一浏览器的应用音频？
- 音频监听是否把输出再送回输入？
- 旧 DSH 插件自动朗读是否还在另一个网页运行？

保留一条可控的输出链路，用耳机做测试。在 OBS 混音器逐个静音确认来源，不要一次改所有设置。

## 7. 停播

先在舞台挂断并确认场次结束，再停止推流。采集和转发停止不等于 Vidu 场次自动结束。

## 欢迎话术轮换（2026-11-15）

内置 8 句欢迎语按顺序轮换，每句带观众昵称，第 8 句后回到第 1 句；服务进程重启后从第 1 句开始。话术直接走本地 TTS，不额外调用大模型。欢迎为问题或麦克风让位后，缓存文字和已合成的音频保持对应，不会切成下一句话。

可以在私有 `config.json` 的 `danmaku.welcome_templates` 列表中编辑话术，使用 `{nick}` 插入昵称，每条建议写成一句短句。没有占位符时会自动在前面补昵称；空列表或无效配置回退到内置话术。已有配置不强制覆盖，未配置该字段时直接使用内置 8 句。
