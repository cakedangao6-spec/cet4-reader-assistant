# CET-4 听力精听播放器

这是基于 ABLoopPlayer 思路改造的四级听力练习工具。上游原页面仍保留在 `ABLoopPlayer.html`，四级专用入口是 `cet4.html`。

## 安装

不需要安装前端依赖。推荐用 Python 启动一个本地静态服务，浏览器访问会比直接双击 HTML 更稳定。

```powershell
cd "D:\Codex Project\CET-4\cet4-abloop-player"
.\.venv\Scripts\python.exe scripts\local_server.py
```

也可以使用系统 Python：

```powershell
cd "D:\Codex Project\CET-4\cet4-abloop-player"
python scripts\local_server.py
```

## 运行

打开：

```text
http://localhost:8000/cet4.html
```

页面默认读取：

```text
materials/listening/25-6-1/cet4_2025_06_1.mp3
```

也可以点“导入 MP3”手动选择音频。

## 功能

- 本地 MP3 播放
- 0.5x 到 2.0x 倍速
- A-B 循环
- 左侧 1-25 题号跳转
- 当前时间写入本题时间点
- 手动编辑开始/结束时间
- 右侧原文、答案、解析
- 右侧 AI 时间轴，点击片段跳转，点击“循环”反复听该片段
- 搜索题干、选项、原文、解析
- 导入/保存 JSON

## 文件作用

- `cet4.html`：四级专用页面入口。
- `css/cet4.css`：Windows 浏览器界面样式。
- `js/cet4.js`：播放控制、题号跳转、A-B 循环、搜索、JSON 导入导出。
- `data/cet4_2025_06_1.js`：本套题的题目、答案、解析、原文、初始时间点。
- `data/cet4_2025_06_1_timeline.js`：faster-whisper 生成的 AI 时间轴。
- `data/cet4_2025_06_1_timeline.json`：同一份时间轴的 JSON 版。
- `scripts/local_server.py`：本地静态服务脚本。
- `scripts/generate_timeline.py`：重新生成 AI 时间轴的脚本。
- `ABLoopPlayer.html`：保留的上游 ABLoopPlayer 原页面。
- `js/main.js`：上游 ABLoopPlayer 原播放器逻辑。
- `css/main.css`：上游 ABLoopPlayer 原样式。
- `jquery-ui/`、`svg/`、`png/`：上游项目资源。

## 说明

当前 1-25 题时间点是初始估算值。练习时跳到某题，微调到准确位置后点“当前时间设为本题”，再点“保存 JSON”即可导出自己的时间点文件。

AI 时间轴由本地 `faster-whisper base.en` 自动生成，适合快速定位句子或短片段。个别识别词可能与标准原文不同，以右侧“原文”为准。
