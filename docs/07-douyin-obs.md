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
4. 单条弹幕不一定逐条读：系统有间隔、去重、批量、过滤、礼物合并等规则。
5. 观察一次完整回复后，再验收真实直播音画。

**匿名配置未必能接入所有房间。** 按采集器的具体错误决定是否需要合法获取并在本机配置 Cookie；只改 `xiaoya-runtime/douyin-live/config.yaml`，不要贴到聊天或仓库。平台协议可能变化，本文没有把模拟测试写成真实采集成功。

## 4. OBS / 直播伴侣

1. 安装并打开你使用的官方直播工具。账号资格、推流方式及平台规范按平台当前要求办理。
2. 新建场景，先添加**窗口捕获**，选择打开舞台的浏览器窗口。对于当前需要点击连接和 RTC 的工作台，这比一开始就上 OBS 无界面浏览器源更容易排错。
3. 调整裁切，只留下人物区域；需要右下角统计时保留该区域。不希望显示后台按钮就裁掉底部操作区。
4. 设置画布尺寸，比如横屏 1920×1080，或按你的平台要求设竖屏。
5. 先做本地 20 秒录制，回放检查画面、口型、音量和字幕，而不是直接正式开播。

如果改用 OBS 浏览器源，它有独立的页面实例、播放策略和权限状态；不能假定你在 Chrome 已连接就等于 OBS 那个页面也连接。需要单独按实际行为验证，别同时开两场云端会话。

## 5. 声音说两遍 / 有回音

先检查**重复播放和重复采集**，不要先改模型：

- 舞台页是否开了两个标签并都在播放？
- relay 是否启动了两份，导致同一弹幕触发两次？
- OBS 是否既采桌面音频，又采同一浏览器的应用音频？
- 音频监听是否把输出再送回输入？
- 旧 DSH 插件自动朗读是否还在另一个网页运行？

保留一条可控的输出链路，用耳机做测试。在 OBS 混音器逐个静音确认来源，不要一次改所有设置。

## 6. 停播

先在舞台挂断并确认场次结束，再停止推流。采集和转发停止不等于 Vidu 场次自动结束。
