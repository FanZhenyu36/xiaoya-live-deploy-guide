# 03 · 模型与加速：按层验证

回到 [主教程](../README.md)。本章只针对本地 OmniVoice，不涉及 Vidu 云端渲染加速。

## 1. 三样东西不要混淆

| 你看到的文件 | 是什么 |
|---|---|
| `flashinfer-source/omnivoice/` | Python 源码 |
| `.venv/lib/python3.12/site-packages/` | 已安装的 Python 包 |
| `snapshots/.../model.safetensors` | 真正的模型权重 |

只找到 `omnivoice.txt` 说明找到了音色标记，不代表找到了模型。文件夹名字不叫 OmniVoice 也可能存了权重；Hugging Face blobs 常无后缀。

## 2. 检查已下载模型

Ubuntu：

```bash
cd ~/omnivoice-wsl
source .venv/bin/activate
python guide-tools/check_model.py
find -L "$HOME/.cache/huggingface/hub/models--k2-fsa--OmniVoice/snapshots" -maxdepth 3 -type f -printf '%s %p\n' 2>/dev/null | head -n 20
```

`du -sh` 和文件逻辑大小不一样，尤其在符号链接、稀疏文件及共享 blob 情况下。先用 `readlink -f` 和本教程检查器确认链接可读，再决定要不要重下。

## 3. 先检查环境，不加载大模型

```bash
cd ~/omnivoice-wsl
source .venv/bin/activate
export PYTHONPATH="$PWD/flashinfer-source"
NVCC_PATH=$(find "$VIRTUAL_ENV" -path '*/bin/nvcc' -type f -print -quit)
export CUDA_HOME="$(dirname "$(dirname "$NVCC_PATH")")"
export PATH="$CUDA_HOME/bin:$PATH"
python guide-tools/diagnose.py
```

应看到：

- `torch.cuda.is_available()` 对应 Available=True。
- GPU 为你的 NVIDIA 显卡。
- PyTorch CUDA 为这个安装档的 13.0。
- OmniVoice 来源于 `flashinfer-source`，能导入 `omnivoice.models.omnivoice_flashinfer`。
- nvcc 来源于当前虚拟环境的 `nvidia/cu13/bin/nvcc`，不是系统残留的 12.8。

`ModuleNotFoundError: omnivoice.models.omnivoice_flashinfer` 可能是 PyPI 同版本源码中没有该文件，或 Python 优先导入了另一份安装。检查 `omnivoice.__file__`，不要只反复重装 FlashInfer 包。

## 4. CUDA、nvcc、缓存怎么搭配

这台已知工作的环境是 PyTorch `2.14.1+cu130`、FlashInfer `0.7.2.post1`、cache `0.7.2.post1+cu130`、nvcc `13.0.88`。这是已记录的组合，不是“所有 RTX 50 都只能用某一个 CUDA”的普遍结论。

- `nvidia-smi` 的 CUDA 字样代表驱动支持能力上限，不等于当前 Python 实际 CUDA runtime。
- `torch.version.cuda` 才反映当前 PyTorch 构建的 runtime。
- `nvcc --version` 反映编译器版本；FlashInfer JIT 可能使用它。
- JIT cache 必须和 FlashInfer/CUDA 档位对应。[官方安装说明](https://docs.flashinfer.ai/installation.html)会随版本更新。

本教程不改系统 `/usr/local/cuda`。启动器只给本进程设置虚拟环境中的 `CUDA_HOME` 和 PATH。

## 5. 先不加速 → FlashInfer → Graph

从教程根目录，在 Ubuntu 逐项测试。每次换模式前先 Ctrl+C 结束上一份服务：

```bash
# A. 标准 GPU 推理
OMNI_FLASHINFER=0 bash scripts/wsl/start-omnivoice.sh

# B. FlashInfer，但不启用 CUDA Graph
OMNI_CUDA_GRAPH=0 bash scripts/wsl/start-omnivoice.sh

# C. FlashInfer + CUDA Graph
bash scripts/wsl/start-omnivoice.sh
```

不要一次性粘贴三行，前一行是常驻服务，会一直占住终端。先完成 A 的试听，再结束并运行 B，再做 C。

Graph 默认只捕获 `5,10` 桶。更长桶可能加大显存和初始化成本，不保证对短回复有帮助。OOM 时先回 B，而不是继续叠加环境变量。

## 6. 怎么比较是否真的提速

1. 用同一个模型、同一份参考音频、相同文本和相同采样参数。
2. 先合成一次预热，不把首次编译/权重加载算成稳定速度。
3. 再合成同一段 3 次，记录各自秒数以及生成音频时长。
4. 比较端到端合成时间；不要拿 2 秒语音和 20 秒语音直接比。
5. 同时看显存峰值、CPU 和 GPU 是否被别的程序占用。

FlashInfer 主要优化本地语音计算，不能消除云端 LLM、网络、Vidu 渲染和 RTC 的等待。口型是否自然还受形象角度、遮挡、嘴部尺寸、参考素材等影响。

## 7. 本地模型入口明确列在仓库里

本教程的服务入口为 `scripts/wsl/launch_omnivoice.py`，安装后位于 `~/omnivoice-wsl/guide-tools`，可以直接阅读。它使用官方 `OmniVoice.from_pretrained` 和 `build_demo`，不下载额外 ASR 模型，不开启 Gradio 公网 share。

启用 `load_asr=False` 是为了减少依赖和显存，不表示你录入的参考文字可空着不填。
