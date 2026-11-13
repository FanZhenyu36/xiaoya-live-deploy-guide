# 09 · 排错：先确定哪一层出了问题

回到 [主教程](../README.md)。先读第一条真正的错误，不要只看最后一行的 exit code。

## 1. 快速定位

| 现象 | 先检查 |
|---|---|
| 命令不存在 / pnpm.ps1 被禁止 | 软件安装、重开终端、使用 `.cmd` 入口 |
| curl 立即 Connection refused，DNS 为 0.0.0.0 | hosts / 默认 DNS / 代理软件过滤 |
| 下载很久不动 | 目标网络、代理是否覆盖该进程、下载实际字节数 |
| 找不到 demo_flashinfer.py | 入口来自哪个仓库；本教程用 launch_omnivoice.py |
| Python 执行后退出码 0、什么都没输出 | 文件是否成了一行注释，是否有 main 入口 |
| 找不到 omnivoice_flashinfer | Python 导入来源、源码版本、PYTHONPATH |
| CUDA / sm_120 / unsupported architecture | 显卡、PyTorch CUDA、nvcc 与 cache 的组合 |
| 9877 打不开 | OmniVoice 是否真的启动且完成加载 |
| 8795 拒绝连接 | 舞台进程退出或没启动，读 stage.err.log |
| 8765 根地址 Not Found | 查 `/api/health`，它不是前台网页 |
| HTTP 503 TTS | 查看服务端错误，检查 9877、音色、模型是否就绪 |
| 10048 / Address already in use | 已有实例占端口，不要再起第二份 |
| Vidu 400 avatar is still processing | 等平台形象处理完成 |
| Vidu 401 / 403 | Key、环境、账号、组件权限、形象和动作库归属 |
| conn_init 成功但没画面 | RTC SDK、频道、远端订阅、播放策略、网络 |
| 说话两遍 | 两个标签、两个 relay、双音频采集、旧插件朗读 |
| 改了声音没变化 | 分清云端音色与本地 OmniVoice 音色，清旧队列后新合成 |
| 统计字幕丢了 | 右侧统计开关，双击/按 Home 复位拖动位置 |

## 2. 9877 启动卡住

Ubuntu 新开一个终端：

```bash
nvidia-smi
ps -ef | grep -E 'launch_omnivoice|start_flashinfer|omnivoice.cli.demo' | grep -v grep
curl --noproxy '*' --connect-timeout 3 --max-time 5 -I http://127.0.0.1:9877/
```

在首次编译/Graph 捕获期间，网页还没起来是可能的。看前台日志究竟停在下载、权重加载、内核编译还是报错。如果已经打印 traceback，就不是继续等 150 秒能解决的事。

OOM 时先关其他模型，再禁用 Graph 验证；若仍不行，不要删除现有缓存作为第一步。

## 3. Windows 打不开 WSL 服务

1. Ubuntu 内部能否打开 `http://127.0.0.1:9877/`？
2. Windows 能否访问 `127.0.0.1:9877`？
3. 不行时，PowerShell 查 `wsl -d Ubuntu-22.04 hostname -I`，取实际可达的 WSL 地址测试。
4. NAT IP 会变化，不能沿用旧截图中的 `172.x.x.x`。
5. 若只能通过新 WSL IP 访问，在私有配置更新 `tts.omnivoice_base`，然后 reload。

WSL 镜像网络和自动代理支持情况见网络章节，不要用关闭全部防火墙来解决一个本地端口问题。

## 4. TTS 服务返回 WAV 但没听到

HTTP 200、文件字节数、音频时长只证明返回了音频；仍要实际播放。检查文件格式、音量、浏览器输出设备和静音状态。上游旧 smoke 脚本提示 `Play ...` 只是提示你去播放，不一定自动播放。

## 5. 数字人画面慢

把耗时拆开看：

```text
LLM 首字 → 句子积累 → 本地 TTS → 音频转码/上传 → 云端渲染 → RTC 播放
```

本地 Graph 不能提速云端渲染。短句、关闭不必要的思考模式、稳定网络和清晰素材往往更影响体感。不要在没测量前把所有延迟归给显卡。

## 6. 字幕有回复但没有人物声音

先做 `/api/tts/preview`。试听失败则修本地 TTS；试听成功再看喂流、RTC 远端音频订阅、浏览器自动播放和输出设备。不要一开始就重新下载全部模型。

## 7. public 仓库里发现 Key

先到服务方撤销并换新。删当前文件不能撤回 Git 历史和已经被读取的凭据。不要再把新 Key 发到 Issue 或聊天截图里。本仓库的扫描器只是辅助检查，不能保证识别世界上所有密钥格式。

## 8. 反馈问题的最小信息

- Windows / WSL / Python / 显卡版本。
- 主教程第几步，执行的是 PowerShell 还是 Bash。
- 复制的命令（Key 置空）、第一条错误、最后 30–60 行日志。
- 对应端口是否响应，以及是否已有重复实例。

不要把完整 `config.json`、登录凭据、Cookie、私人参考音频或带签名的录播 URL 公开。
