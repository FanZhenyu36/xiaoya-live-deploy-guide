# 上游来源与素材边界

这是个人整理的部署教程与界面补丁，不是上游官方发行版。

另附 `overlays/speech-completion.patch`：基于同一上游提交，修正完整句子收集和过短 TTS 尾块；该源码补丁同样采用 AGPL-3.0，修改日期 2026-11-13。

- `overlays/silver-studio.patch` 修改自 [cyber-xiaoya/cyber-xiaoya-live](https://github.com/cyber-xiaoya/cyber-xiaoya-live)，基线 `c0effaf50d2bbf9dcfde8847a853c5c871d9dee4`。源代码采用 AGPL-3.0；许可证全文见本仓库 LICENSE。
- 变更日期：2026-11-13。界面补丁包括三分区工作台、银白配色、底部控制、统计字幕、事件折叠；另附上文所述的语音完整性后端修复。
- 上游作者：天工开帧 / AI少女宇宙计划组，Copyright (C) 2026。上游 NOTICE 原文见下方。
- OmniVoice 是 k2-fsa 的独立项目（Apache-2.0）；本仓库只提供安装与启动工具，不打包其模型和源码。
- FlashInfer、PyTorch、douyinLive、DSH、DUIX 及各模型遵循各自许可证。安装器直接从各自官方来源获取；使用前阅读对应许可。
- 本仓库不分发人物图片/视频、克隆参考音频、作者歌单/动作库/人设、登录 Cookie 或 API Key。
- README 中的“小雅”仅用于识别本次部署的上游项目，不表示官方合作或官方发布。

## 上游 NOTICE 原文

```text
赛博小雅直播版（组件版数字人）
Copyright (C) 2026 天工开帧 / AI少女宇宙计划组

本仓库的**源代码**以 GNU Affero General Public License v3.0（见 LICENSE）授权。

以下内容**不在** AGPL-3.0 的授权范围内，版权归作者所有，未经书面许可不得用于商业用途、
不得二次分发：

  1. 人物形象素材（图片、视频、形象模型及其衍生素材）
  2. 克隆音色的参考音频、参考文本、音色模型
  3. 人设提示词、文案、歌单、动作库内容
  4. 项目名称「赛博小雅」、Logo 及相关标识

关于名称与标识：本项目名称与标识用于指代本项目的官方发布。任何第三方不得以本项目
名义发布、售卖或推广其修改版本，也不得暗示与本项目存在官方关联。

第三方组件（FastAPI、httpx、uvicorn、websockets 等）遵循其各自的许可证，详见
requirements.txt 与各依赖仓库。

官方唯一发布渠道：https://github.com/cyber-xiaoya/cyber-xiaoya-live

```

2026-11-14：更新银白界面中的入场提示、排队计数及设置说明；新增 `audience-queue.patch`，修改弹幕转发、队列调度和完整句边界，增加 `src/audience.py`。该源码补丁与对应回归测试同样采用 AGPL-3.0。
