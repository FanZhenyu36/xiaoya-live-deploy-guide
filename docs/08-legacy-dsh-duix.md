# 08 · 可选旧路线：DSH 语音插件 + FunASR + DUIX

**这不是直播主线的前置步骤。** 只想用 8795 Vidu 工作台，请回 [README](../README.md)。本章记录从最初语音聊天到本地口播数字人的另一条路径。

来源：[原语音项目](https://github.com/beiyege-01/dsh-voice-ai-girlfriend)、[独立插件](https://github.com/beiyege-01/dsh-voice-ai-girlfriend-plugin)、[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)。旧插件是否兼容 DSH 将来的版本需要重新核对，不能把旧教程当成全版本兼容承诺。

## A. 安装 DSH

### A1. Windows 基础环境

安装 Node.js，使用 DSH 源码 `package.json → engines` 要求的版本。这次实际电脑使用 Node 24；主版本相同也要看最低小版本。可通过官方安装包或：

```powershell
winget install --id OpenJS.NodeJS.LTS --exact
```

重开 PowerShell：

```powershell
node --version
npm.cmd --version
```

### A2. 克隆源码，别用没有 Git 历史的 ZIP 构建

```powershell
cd C:\AI
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd C:\AI\deepseek-harness
```

查看 `package.json` 的 `packageManager`。该次源码为 `pnpm@11.28.5`，请以你自己下载的版本为准：

```powershell
npm.cmd install -g pnpm@11.28.5
pnpm.cmd install
```

Windows PowerShell 下使用 `pnpm.cmd`，避免同名 `pnpm.ps1` 被执行策略阻止。提示“modules directory will be removed and reinstalled”时，先理解是在当前工作区重建依赖；不要在不清楚目录时盲按 Y。

### A3. 构建

```powershell
pnpm.cmd run build
```

构建可能占用数分钟和较多内存。出现一系列 PASS 且退出码 0，才进入下一步。

常见错误：

- `Cannot find package tsx`：依赖没装完，不是插件配置问题。回 A2。
- `Cannot find ... lib/typert.host.js`：内部包尚未构建，先完成 build。
- `git rev-parse HEAD` 失败：没有真正 Git checkout，优先重新 clone；不要把 `0000000` 当真实版本号。`DSH_CLIENT_COMMIT_HASH` 只能作为明确标记的本地开发兜底，不能伪装可复现版本。

### A4. 安装两个插件到同一个 profile

本次使用 `web-v021` profile。以下在 DSH 根目录：

```powershell
node --import tsx/esm apps/cli/src/bin.ts plugin --profile web-v021 add github:beiyege-01/dsh-voice-ai-girlfriend-plugin
node --import tsx/esm apps/cli/src/bin.ts plugin --profile web-v021 add @deepseek-ai/dsh-web-app@0.2.1-rc.2
```

不要把语音插件装在一个 profile、网页插件装在另一个 profile，然后疑惑为什么按钮不出现。若目标版本不存在，查看上游当前说明，不能无限重试旧包名。

### A5. allowBuilds 报错的正确处理

如果显示 `ERR_PNPM_GIT_DEP_PREPARE_NOT_ALLOWED`，它会打印一个带包名、codeload URL 和具体提交号的**完整键**。只允许这次确实安装的那个包，不要全局放开所有构建。

profile 文件通常是：

```text
%USERPROFILE%\.dsh\profiles\web-v021\pnpm-workspace.yaml
```

参考结构（其中第一行键必须替换成 pnpm 本次报错打印的原文，不能照抄占位词）：

```yaml
allowBuilds:
  "这里替换成报错里完整的包名@https://codeload.github.com/.../tar.gz/提交号": true
  koffi: true
```

- 两个条目都是 `allowBuilds` 下的同级属性，前面两个空格。
- 不要使用 Tab，不要重复添加第二个 `allowBuilds` 段。
- `true  koffi: true` 不能写在同一行。
- 已有其他 YAML 项要保留，不要用这个小片段覆盖整份配置。
- `ERR_PNPM_IGNORED_BUILDS: koffi` 时再确认是否确实需要批准它；可以在该 profile 目录用 `pnpm.cmd approve-builds` 逐项操作。

修好后重跑失败的 plugin add 命令。`git ls-remote ... connection reset` 先按网络章处理，不是 allowBuilds 错误。

### A6. 打开 DSH 网页

先看该 profile 的帮助，去掉 `--help` 后按帮助支持的选项启动：

```powershell
node --import tsx/esm apps/cli/src/bin.ts --profile web-v021 --help
node --import tsx/esm apps/cli/src/bin.ts --profile web-v021 --port 3080
```

以终端实际打印的网页链接为准，某些版本有浏览器访问 token。登录或填好你实际使用的模型服务。页面右下角选择可用模型；`MISSING_CREDENTIAL` 表示对应模型路线缺凭据，不是麦克风坏了。

## B. 旧语音桥 8765 和识别模型

### B1. 下载原语音项目

新开 Windows PowerShell：

```powershell
cd C:\AI
git clone https://github.com/beiyege-01/dsh-voice-ai-girlfriend.git
cd C:\AI\dsh-voice-ai-girlfriend
uv venv venv-speech --python 3.12
uv pip install --python .\venv-speech\Scripts\python.exe torch --index-url https://download.pytorch.org/whl/cu130
uv pip install --python .\venv-speech\Scripts\python.exe -r .\bridge\requirements.txt
```

这是旧项目的依赖路线，和 OmniVoice WSL 虚拟环境分开，**不要往一个环境里乱混所有模型**。如果原项目当前约束与上述 Python/CUDA 档位冲突，按其当时版本逐项解决；本教程未进行第二套空白环境的完整 GPU 重装。

### B2. 下载 FunASR 中文识别模型

仍在旧语音项目根目录，Windows PowerShell：

```powershell
.\venv-speech\Scripts\python.exe -c "from modelscope import snapshot_download; snapshot_download('iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch', local_dir='models/funasr/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')"
```

这是“听你说话”的识别模型，和 OmniVoice“让她说话”的 TTS 不同。源码路径存在不等于权重已下完。

### B3. 下载 VAD 打断模型

原项目约定 `models/silero-vad/silero_vad_v4.jit`：

```powershell
New-Item -ItemType Directory -Path .\models\silero-vad -Force
curl.exe -fL https://raw.githubusercontent.com/snakers4/silero-vad/v4.0/files/silero_vad.jit -o .\models\silero-vad\silero_vad_v4.jit
```

文件应是真实 JIT 权重，不是 404 HTML。来源为 [官方 v4.0](https://github.com/snakers4/silero-vad/tree/v4.0)。

### B4. 配置桥接

```powershell
Copy-Item .\bridge\bridge-config.example.json .\bridge\bridge-config.json
notepad .\bridge\bridge-config.json
```

先配置纯语音，把 `digital_human.enabled` 设为 `false`，QQ 也先保持关闭。按实际路径设置：

```json
{
  "omnivoice": {"base": "http://127.0.0.1:9877"},
  "persona": {"default_voice": "my_voice"},
  "digital_human": {"enabled": false},
  "stt": {
    "backend": "funasr",
    "model_name": "models/funasr/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "device": "cuda"
  }
}
```

这是需要**合并到原模板**的局部片段，不要拿它覆盖原模板里所有参数。复制你自己的音色文件夹到旧项目 `voices/my_voice`，结构与主教程一致。检查 `bridge/voice_bridge.py` 中 `VOICES_DIR`；如果下载的版本写死作者电脑路径，把它改为你的 `voices` 目录，推荐基于源码位置计算，而不是沿用作者的盘符。

旧模板里可能仍有 Qwen3-TTS 示例路径。走 OmniVoice 时，要让默认音色被识别为 `omni-clone`；如果日志显示还在加载 Qwen，先检查音色标记和默认音色，不要为消除示例路径再下载一份不使用的模型。

### B5. 启动和冒烟测试

先启动主教程的 OmniVoice，再在旧项目：

```powershell
.\bridge\start-bridge.cmd
```

新开终端到同目录测试：

```powershell
curl.exe --noproxy "*" http://127.0.0.1:8765/api/health
.\venv-speech\Scripts\python.exe .\bridge\smoke_tts.py --text "你好，我是小雅。" --out .\tts-check.wav
.\venv-speech\Scripts\python.exe .\bridge\smoke_stt.py --help
```

识别测试按 `smoke_stt.py --help` 支持的参数传你自己录的音频。先让离线识别成功，再排查浏览器麦克风。8765 的根地址 `/` 返回 Not Found 不说明桥坏了；查真正的 API。

`.\` 表示当前目录；`--out` 只是指定文件保存位置。作者省略 `--out` 时应使用脚本默认值。如果只有一种命令成功，比较工作目录、脚本版本和默认输出权限，而不是把不同的测试句子当成修复原因。

### B6. 浏览器麦克风

1. 用 `localhost` / `127.0.0.1` 本地网页，允许该页面的麦克风权限。
2. Windows 隐私设置允许桌面应用/浏览器使用麦克风。
3. 确认浏览器选的输入设备有音量，设备未被其他软件独占。
4. 检查 CORS 是否包含你实际的 DSH 网页地址和端口。
5. 识别成功但重复朗读，排查多标签、多个插件监听或音频双路播放。

## C. 可选 DUIX 本地视频生成

### C1. 安装 Docker Desktop

按 [Docker 官方 Windows 安装说明](https://docs.docker.com/desktop/setup/install/windows-install/)安装、启用 WSL2 后端，打开 Docker Desktop，等待 Engine running。

```powershell
docker version
docker info
```

要能看到 Server 信息。`open //./pipe/docker_engine ... not found` 表示引擎没有启动或 context 不正确，和你的形象视频无关。

### C2. 获取镜像

```powershell
docker pull guiji2025/duix.avatar-5090:latest
```

历史教程出现过 `:trt10.9`，本次实际拉取该 tag 返回 not found，改用当时可用的 latest。`latest` 会变，本教程附的 compose 固定到实际下载记录里的 digest；若上游已删除该 digest，请明确核对新镜像再更新，不要把任意第三方镜像当同一个版本。

Docker 拉取需要独立网络/代理配置；`TLS handshake timeout` 按网络章排查，不需要自动改成第三方镜像源。

### C3. 共享目录与视频

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Path D:\duix_avatar_data\face2face\temp -Force
```

用教程中的 `Convert-Avatar.ps1` 把你自己的 24fps 视频转成新文件 `bg3_15fps.mp4`，复制到上述 temp 目录。原文件保留。

本地 `D:\duix_avatar_data\face2face` 挂载为容器 `/code/data`；桥和容器必须看到同一份音频与形象。不同硬盘时改 compose 的 `DUIX_DATA_DIR` 与桥的 `data_dir`，不要只改一边。

### C4. 启动容器

在本教程根目录：

```powershell
docker compose -f .\config\legacy.duix.compose.yml config
docker compose -f .\config\legacy.duix.compose.yml up -d
docker logs --tail 100 duix-avatar-gen-video
```

映射为 **127.0.0.1:9000 → 容器 8383**。有些电脑的宿主 8383 在系统保留端口范围内，换 9000 是为避开冲突。

根路径返回 Flask 404 只证明 HTTP 服务有响应，不证明视频生成模型准备好。等日志出现模型加载完成，再通过原桥真正提交一段短音频验证。冷启动可能数分钟。

### C5. 连接旧桥

旧 `bridge-config.json` 合并：

```json
{
  "digital_human": {
    "enabled": true,
    "duix_base": "http://127.0.0.1:9000",
    "data_dir": "D:/duix_avatar_data/face2face",
    "temp_dir": "temp",
    "avatar_video": "bg3_15fps.mp4",
    "container_name": "duix-avatar-gen-video"
  }
}
```

重启旧桥后，在 DSH 插件打开数字人开关，先发一句短话。确认音频、生成视频和前端播放都完成，再测试长回复。

口型假、段与段衔接不顺和延迟，可能来自驱动素材、逐段生成方式、帧数和显存竞争；不是换一个浏览器标签样式就能解决。当前直播主线用 Vidu 后，不必让它和 OmniVoice/DUIX 同时抢显存。

## D. 两条路线结束后怎么选

| 目标 | 日常启动 |
|---|---|
| 本地 DSH 语音聊天 | OmniVoice + 8765 + DSH |
| 本地 DUIX 口播 | 上述再加 Docker/DUIX |
| 本教程直播工作台 | OmniVoice + 8795 + Vidu；不必启动以上旧组件 |

Qwen3-TTS 是原项目的备选引擎，本教程的当前选择是 OmniVoice，所以不要求再下 Qwen。H3 视频生成也不是此处已经接好的实时驱动服务。
