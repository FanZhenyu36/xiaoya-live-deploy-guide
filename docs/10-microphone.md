# 10 · 麦克风聊天：最高优先级

回到 [主教程](../README.md)。先确认文字对话和语音合成已正常。

## 使用

1. 刷新舞台，点「开始连线」。
2. 在右侧输入框下方点「麦克风」，浏览器询问时允许麦克风权限。
3. 看见「正在录音」后说话，再点「结束并发送」。单次最长约 30 秒，也可点「取消录音」。
4. 本地模型识别后，文字自动作为你的聊天发出。识别中会显示状态；没识别到声音会提示重录。

麦克风录音、识别和回答期间优先级最高，弹幕、欢迎、闲聊等等待。正在说话时先结束当前整句；歌曲会停止让位。录音取消、权限失败、空音频、识别失败会释放优先级。页面意外关闭后，未完成录音的占用会在最长 120 秒保护期后释放。建议戴耳机，减少扬声器声音被麦克风收进去。

## 本地识别服务

语音上传到本机 8798 识别服务，不发送到 Vidu 做语音识别。模型沿用 FunASR Paraformer 中文模型，以 CPU 运行，减少与 OmniVoice 抢显存。首条会加载模型，随后常驻复用。

在舞台私有 `config.json` 中配置已有的识别环境及完整模型目录：

```json
{
  "stt": {
    "base_url": "http://127.0.0.1:8798",
    "python_exe": "C:/AI/asr-env/Scripts/python.exe",
    "model_dir": "C:/AI/models/paraformer-zh"
  }
}
```

Python 环境需要安装 FunASR、PyTorch、NumPy、FastAPI 和 Uvicorn；模型目录中应有 `model.pt`、配置与词表。验证电脑复用了已有 `funasr 1.4.22 / modelscope 1.40.2 / torch 2.11.0+cu130 / numpy 2.5.4` 环境；虽然 Torch 支持 CUDA，这个识别服务明确使用 CPU。本次没有重装一个全新的识别环境，不应把“复用已部署模型”写成任意新电脑免配置即可使用。

FFmpeg 需要已安装并在 PATH 中，也可以额外配置 `stt.ffmpeg` 为本机 FFmpeg 的绝对路径。配置后正常运行 `Start-Stage.ps1` 即会启动或复用识别服务；没配置时该步骤跳过，文字聊天仍可用。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\Start-ASR.ps1
Invoke-RestMethod http://127.0.0.1:8798/health
```

`loaded=false` 仅表示模型尚未首次加载。首次识别可能较慢；健康检查成功不等于物理麦克风权限或输入设备正常。

参考：[FunASR 官方 Python API](https://github.com/modelscope/FunASR/blob/main/docs/python_api.md)。
