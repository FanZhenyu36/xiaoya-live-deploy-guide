# 06 · 每日启动、关闭、修改和备份

回到 [主教程](../README.md)。首次安装才需要装依赖和下载模型，日常启动不用重复安装。

## 1. 正常开机

1. 网络可用，代理处于你已验证的状态。
2. 双击教程目录 `Start-OmniVoice.cmd`。出现已运行则复用；否则等待模型初始化。
3. 打开 `http://127.0.0.1:9877/`，确认语音网页可用。
4. 双击 `Start-Stage.cmd`，打开 `http://127.0.0.1:8795/stage`。
5. 先试听，再连线，再手动对话一次。
6. 最后接弹幕和 OBS。

OmniVoice 是前台常驻，关语音窗口会中断服务。舞台使用后台进程，启动成功后可以关它的启动窗口。这两个窗口的行为不同。

## 2. 已经在运行时

不要因为窗口没了就判断服务没了。先开网页，或者：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\Test-Environment.ps1
```

舞台启动器检查 8795 的健康接口，已有兼容舞台就复用，不会硬停其他程序。如果你原来就在另一目录跑了一份舞台，它会继续复用那份；要测试新的运行目录，先确认结束旧场次并停止旧实例。

## 3. 关闭顺序

1. 工作台挂断，确认 Vidu 会话已结束；异常断线时到平台检查活动场次。
2. 停止平台直播推流。
3. relay 终端 Ctrl+C；采集器可能仍在后台，按其 PID 确认后再结束。
4. 运行 `Stop-Stage.ps1`，只停止本教程记录并核验身份的进程，不杀全部 Python。
5. OmniVoice 窗口 Ctrl+C。

`Stop-Stage.ps1` 找不到匹配进程记录时会拒绝操作。这时使用启动它的前台窗口 Ctrl+C，或在任务管理器核对完整命令行后手动结束；不要猜 PID。

## 4. 修改后如何生效

| 修改 | 生效方式 |
|---|---|
| UI HTML / CSS | 浏览器 Ctrl+F5 |
| 设置面板保存 | 多数热更新，部分影响下一场 |
| 手改 config.json | `/api/settings/reload` 或重启舞台 |
| Vidu 形象 / RTC / 录播 | 结束旧场，重新连线 |
| 音色预设 | 刷新音色列表，选择后测试新语音 |
| Python 包 / 加速参数 | 停语音服务后再启动 |
| .wslconfig | 保存工作后 `wsl --shutdown` 再开 |

## 5. 日志在哪里

| 服务 | 日志 |
|---|---|
| 新教程后台舞台 | `xiaoya-runtime/logs/stage.out.log`、`stage.err.log` |
| 上游舞台内部日志 | `xiaoya-runtime/stage/logs/bridge.log` |
| 新教程前台 OmniVoice | 启动它的终端输出 |
| 新教程采集器 | `xiaoya-runtime/logs/collector.out.log`、`collector.err.log` |
| 旧 DSH 语音桥 | 旧项目 `bridge/logs/bridge.log` 或其前台终端 |

PowerShell 读末尾：

```powershell
Get-Content C:\AI\xiaoya-runtime\logs\stage.err.log -Tail 60
```

不要把完整日志直接公开，先检查是否含凭据、带签名的链接、用户消息或私有路径。

## 6. 要备份什么

私下备份 `config.json`、`secrets`、`voices`、你自己的素材、歌单/人设与确实需要的录播。不要把模型环境和日志整个塞进 GitHub；模型通常可从官方重下，自己的授权素材不一定能找回。

UI 补丁和教程脚本可以跟 Git 走；Key 和 Cookie 始终放 Git 以外或被明确忽略的私有位置。`.gitignore` 不会自动删除已经提交过的密钥；若曾公开，先在服务端撤销更换，随后再清理历史。

## 7. 升级策略

本教程钉住上游提交，目的是防止今天和明天装到不同代码。不要直接 `git pull` 覆盖已定制舞台。先在新的 runtime 目录测试上游新版本，确认 API、音色和界面后再迁移私人配置；不能把旧版本补丁硬套到任意新版本。
