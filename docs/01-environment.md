# 01 · 环境和目录：先不要同时装两套

回到 [主教程](../README.md)。

## 1. 建议的安装顺序

| 顺序 | 你在装什么 | 装完以后检查 |
|---|---|---|
| 1 | Windows Git / Python 3.12 / uv / ffmpeg | 各自的版本命令 |
| 2 | Windows NVIDIA 驱动 | Windows `nvidia-smi` |
| 3 | WSL2 + Ubuntu 22.04 | `wsl --list --verbose` 的 VERSION=2 |
| 4 | Ubuntu git / ffmpeg / uv | Ubuntu 的版本命令及 `nvidia-smi` |
| 5 | OmniVoice 源码和 Python 依赖 | `diagnose.py` 能导入所需包 |
| 6 | 模型文件 | `check_model.py` 成功 |
| 7 | 加速语音服务 | 9877 网页实际合成成功 |
| 8 | 舞台 | 8795 网页打开、音色试听成功 |
| 9 | 云端 Key / 形象 / LLM | 连线并完成手动对话 |
| 10 | 弹幕、OBS | 真实房间和平台预览验收 |

每过一层再装下一层。网页 404、模型没找到、显卡不可用、Key 错误是不同层的问题。

## 2. 目录是两套路径表示同一块盘

| Windows | Ubuntu / WSL |
|---|---|
| `C:\AI\xiaoya-live-deploy-guide` | `/mnt/c/AI/xiaoya-live-deploy-guide` |
| `E:\models\OmniVoice` | `/mnt/e/models/OmniVoice` |
| Ubuntu 的 `/home/你的Linux用户名/omnivoice-wsl` | `~/omnivoice-wsl` |

推荐把 Linux 虚拟环境和源码留在 Linux 家目录，避免在 `/mnt/c` 上反复创建大量小文件。教程文件位于 Windows 盘没关系。

`C:\AI\xiaoya-runtime` 是生成的私有运行目录；不要将它设置成公开仓库。更换默认路径时，在教程根目录创建 `settings.local.json`，同时改 `runtime_root` 和 `stage_root`。

## 3. 端口表

| 端口 | 地址 | 用途 | 主线需要 |
|---|---|---|---|
| 9877 | `http://127.0.0.1:9877/` | 本地 OmniVoice 网页 | 是 |
| 8795 | `http://127.0.0.1:8795/stage` | 直播工作台 | 是 |
| 1088 | `http://127.0.0.1:1088/health` | 可选抖音采集器 | 否 |
| 8765 | `http://127.0.0.1:8765/api/health` | 旧 DSH 语音桥 | 否 |
| 3080 | 以 DSH 启动输出为准 | 旧 DSH 网页 | 否 |
| 9000 | Docker 端口映射 | 旧 DUIX 视频生成 | 否 |
| 8796 | 本机曾配置的账号模型适配器 | 非通用的私有登录适配 | 公共教程不用 |

端口不能重复绑定。看到 `Address already in use` / `WinError 10048` 先检查：

```powershell
Get-NetTCPConnection -LocalPort 8795 -State Listen
```

再用返回的 `OwningProcess` 查询是谁：

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId=把这里换成进程号" | Select-Object ProcessId,Name,CommandLine
```

不要使用“一键杀掉所有 python.exe”的方式解决冲突，会把其他模型一并关掉。

## 4. 显存与空间

- TTS 空闲、合成峰值、Graph 缓存会占不同显存，不能只看模型文件大小。
- 第一次模型加载/内核编译慢，不代表所有调用都慢。
- 同时打开本地视频生成、其他大模型、游戏，可能导致 OmniVoice OOM。
- 本教程默认仅 `5,10` Graph 桶；不要一开始加到 `30,60`。
- Docker 镜像、录播、合成缓存属于另一部分磁盘消耗。

## 5. 已有可用环境的人

不要为了跟教程一致而清空现有 `.venv` 或模型缓存。先照 `VERSIONS.md` 记录版本，再在一个新的目标目录试安装。本文编写时没有重装已运行电脑上的模型环境。
