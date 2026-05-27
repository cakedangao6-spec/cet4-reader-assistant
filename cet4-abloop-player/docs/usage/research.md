# 开源方案调研

调研时间：2026-05-14

## 结论

选择 ABLoopPlayer 作为改造基础。它已经具备本地音频、倍速、A-B 循环、书签、导入导出等核心能力，源码是轻量 HTML/JavaScript，改成“题号导航 + 四级原文解析 + JSON 时间点”成本最低。

## 对比

| 方案 | 功能 | 是否开源 | 二次开发难度 | 是否适合英语四级 | 是否适合本需求 |
| --- | --- | --- | --- | --- | --- |
| WorkAudioBook | 语言学习音频播放器，短语切分、字幕、自动暂停、重复、书签、词汇等 | 未找到可用源码；公开资料标为 Free Personal / Proprietary | 高，闭源不可直接改 | 很适合听力精听 | 不适合作为本次代码基础 |
| LLPlayer | Windows 语言学习播放器，双字幕、AI 字幕、实时翻译、Whisper/faster-whisper | 开源，C#/WPF | 中高，需要理解 WPF、多媒体和 ASR 结构 | 适合泛语言学习 | 功能很强，但对“题号 + 解析面板”改造偏重 |
| SuVi Player | Windows 视频播放器，交互字幕、词汇列表、A-B loop、Repeat After Me、字幕提取 | 开源，C#/.NET/LibVLCSharp/FFmpeg | 中高 | 适合带字幕视频/跟读 | 音频题目导航不是主场，改造成本高于 ABLoopPlayer |
| AB Loop Player | HTML5 本地音视频、A-B repeat、slow/fast motion、bookmark、export/import | 开源，GPL；HTML/JS/jQuery UI | 低 | 很适合单套听力练习 | 最适合，已采用 |
| mpv + 脚本 | mpv 原生支持 A-B loop，可配脚本做字幕跳转、书签、Anki 卡片 | 开源生态 | 中，需要安装 mpv 和脚本配置 | 适合高阶用户 | 不适合做给普通 Windows 用户的题号界面 |
| faster-whisper | 本地语音识别，可生成字幕/时间戳 | 开源 | 中，需要模型、依赖和校对 | 适合自动生成初稿字幕 | 适合作为辅助，不适合作为播放器底座 |

## 关键依据

- ABLoopPlayer README：支持本地音视频文件、A-B repeat、slow/fast motion、bookmark、export/import。  
  https://github.com/agrahn/ABLoopPlayer
- LLPlayer README：面向语言学习，支持双字幕、AI 生成字幕、实时翻译，C#/WPF，Windows。  
  https://github.com/umlx5h/LLPlayer
- WorkAudioBook 公开资料：语言学习音频播放器，支持短语重复、字幕、书签；许可证信息显示为 Free Personal / Proprietary。  
  https://alternativeto.net/software/workaudiobook/about/
- SuVi Player 公开资料：Windows 开源语言学习播放器，支持交互字幕、词汇列表、A-B looping、Repeat After Me。  
  https://github.com/ahmedismailc/SuViPlayer
- mpvacious：mpv 语言学习脚本生态，支持字幕定位、选段、Anki 卡片等。  
  https://github.com/Ajatt-Tools/mpvacious
- faster-whisper：基于 CTranslate2 的 Whisper 转写实现，适合生成字幕和时间戳。  
  https://github.com/SYSTRAN/faster-whisper

## 采用方式

本项目保留 ABLoopPlayer 上游文件，并新增：

- `cet4.html`
- `css/cet4.css`
- `js/cet4.js`
- `data/cet4_2025_06_1.js`

核心播放器能力沿用 ABLoopPlayer 的技术路线：浏览器原生媒体播放、倍速、A-B 区间、时间点/书签数据可导出。四级定制层把“书签”改成“题号时间点”，把通用注释改成“原文、答案、解析”面板。
