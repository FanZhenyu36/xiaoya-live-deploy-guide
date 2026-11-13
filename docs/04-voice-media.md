# 04 · 音色、人物图片、bg3 视频分别在哪里

回到 [主教程](../README.md)。

## 1. 本地音色

每个文件夹一种声音：

```text
xiaoya-runtime/voices/my_voice/
  ref_audio.wav   清晰参考音频
  ref_text.txt    和录音逐字对应的文字
  omnivoice.txt   克隆预设标记，可为空白或说明文字
  label.txt      可选，界面显示名称
```

上游扫描克隆音色时要求参考音频和 `omnivoice.txt`。只放一个音频文件可能被当成其他引擎的音色而跳过。`design.json` 是另一种“参数设计音色”，不能在不读字段契约的情况下随便编 JSON。

用 `Import-Voice.ps1` 导入可以避免假 WAV 和路径错误。若想添加第二个音色，换 `-Name voice_two`；脚本不覆盖已有音色目录。

舞台切换本地音色通常对后续 TTS 请求生效，不需要重启整台电脑。已排队或已合成音频仍是旧声音；先打断或等它播完再测试。若改的是 Vidu 云端全托管语音，此组件版主线并不使用它。

## 2. Vidu 人物

配置位于私有 `stage/config.json`：

```json
{
  "avatar": {
    "avatar_id": "你的已就绪形象ID",
    "image_uri": ""
  }
}
```

本地文件路径不是可供云端直接访问的 URI。使用平台创建/上传入口，等处理完成后再连接。切换形象要结束当前会话，用新配置重新创建一场。

人物素材应正面、嘴部清晰、遮挡少、画面稳定。大侧脸、趴伏、手遮嘴、嘴在画面中太小都可能影响口型效果；后期 UI 放大不等于提高模型输入质量。

## 3. 从视频抽一张图

Windows PowerShell，换成你自己的文件：

```powershell
ffmpeg -ss 00:00:01 -i C:\AI\bg3.mp4 -frames:v 1 -q:v 2 C:\AI\avatar-frame.jpg
```

这只抽帧，不会让静态图自动具有原视频的待机动作。图片渲染与循环播放本地视频是两种不同机制。

## 4. 旧 DUIX 的视频

旧路线使用共享目录里的 MP4，例如：

```text
D:\duix_avatar_data\face2face\temp\bg3_avatar_15fps.mp4
```

转换时保留原文件：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\Convert-Avatar.ps1 -InputVideo C:\AI\bg3.mp4 -OutputVideo C:\AI\bg3_15fps.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate,width,height -of default=nw=1 C:\AI\bg3_15fps.mp4
```

`avg_frame_rate=15/1` 才说明新文件是 15fps。转换降低本地生成的帧数负担，但不保证自然衔接，不会改变 Vidu 的云端渲染规格。

## 5. 为什么人物会突然变回另一个

先区分：断线时的占位图、DSH 待机背景、DUIX 驱动视频、Vidu 会话形象。它们配置位置不同。

- DSH 待机：旧项目 `assets/bg-images/` 及 `persona.default_idle`。
- DUIX 说话：旧桥 `digital_human.avatar_video`。
- Vidu：当前 `avatar.avatar_id/image_uri`。
- 如果 `image_uri` 有旧值，它可能优先于新 `avatar_id`。

不要为了换当前 Vidu 人物去删除旧 Docker 视频；那不会改当前会话。
