# 版本与来源

记录日期：2026-11-13。下表是这次部署电脑的读取得到的信息，不表示这些软件永远是最新版本。

| 组件 | 版本 / 提交 | 用途 |
|---|---|---|
| 工作台上游 | `c0effaf50d2bbf9dcfde8847a853c5c871d9dee4` | 安装器固定的后端和界面基线 |
| OmniVoice 源码 | `08be0b4ccbac3e13e374e86fbfead4b4cac343e2` | 包版本仍显示 0.2.1，但包含 FlashInfer 入口 |
| OmniVoice 模型快照 | `c5fdb5ccb189668d56333f77ba2629f4cd7535f4` | 官方 HF 预训练模型 |
| Ubuntu | 22.04 / WSL2 | 语音环境 |
| GPU | RTX 5060 Ti，compute capability 12.0 | 已知工作目标 |
| Python | 3.12 | 两个独立虚拟环境 |
| torch | 2.14.1+cu130 | WSL 实际运行版本 |
| torchaudio | 2.11.1 | WSL 实际安装；元数据要求 torch>=2.11 |
| flashinfer-python | 0.7.2.post1 | 语音加速 |
| flashinfer-jit-cache | 0.7.2.post1+cu130 | 匹配 CUDA 13.0 的缓存 |
| nvidia-cuda-nvcc | 13.0.88 | 虚拟环境中的编译器 |
| nvidia-cuda-crt / nvidia-nvvm | 13.5.37 | 实际运行环境的配套安装版本 |
| transformers / gradio | 5.22.1 / 6.31.0 | OmniVoice 依赖 |
| gradio-client | 2.5.0 | Windows 舞台访问 TTS |
| douyinLive | v2.3.2 | 可选采集器 |
| 旧 DSH 源码包标识 | 0.2.1-rc.2 | 历史路线，不作为当前主线依赖 |
| 旧 DSH 语音插件安装结果 | 0.4.0 | 历史成功记录，未来兼容性需另验 |

`requirements/*tested*` 记录关键依赖。Windows 安装器另使用 `stage-win-py312.lock.txt` 固定独立安装时解析成功的 29 个包；它不是操作系统和驱动镜像，WSL 也未提供全量传递依赖锁文件。安装器会检查解析冲突；不应看到冲突就用 `--no-deps` 强行跳过。

## 官方参考

- [工作台源码与说明](https://github.com/cyber-xiaoya/cyber-xiaoya-live)
- [旧语音项目](https://github.com/beiyege-01/dsh-voice-ai-girlfriend)
- [OmniVoice 源码](https://github.com/k2-fsa/OmniVoice)
- [OmniVoice 权重](https://huggingface.co/k2-fsa/OmniVoice)
- [FlashInfer 安装](https://docs.flashinfer.ai/installation.html)
- [PyTorch 安装](https://pytorch.org/get-started/locally/)
- [NVIDIA CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [WSL 安装](https://learn.microsoft.com/en-us/windows/wsl/install)
- [WSL 网络](https://learn.microsoft.com/en-us/windows/wsl/networking)
- [uv 安装](https://docs.astral.sh/uv/getting-started/installation/)
- [DeepSeek 模型列表与计费说明](https://api-docs.deepseek.com/quick_start/pricing/)
- [douyinLive v2.3.2](https://github.com/jwwsjlm/douyinLive/releases/tag/v2.3.2)

API 的价格、权限、模型名和 RTC 条件以服务商当前文档及账号控制台为准。教程没有把某次截图的积分费率写成永久承诺。
