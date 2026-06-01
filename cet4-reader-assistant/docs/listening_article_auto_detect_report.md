# CET-4 阅读助手：听力文章自动识别报告

## 快速状态

- 项目：CET-4 阅读助手
- 当前状态：已修复 25-6-2 听力切分异常，并新增重新识别、原始转写模式、GPU 真实状态、识别摘要和听力文本导出
- 入口文件：`cet4_reader/main.py`
- 运行方式：在 `cet4-reader-assistant` 目录运行 `.venv\Scripts\python.exe -m cet4_reader.main`，或双击 `run_app.bat`
- 最后修改：2026-05-31

## 本次新增

- 听力模式新增按钮：`自动识别文章`
- 导入本地音频后，可用 faster-whisper 离线转录并提取带时间戳的 segment
- 按四六级听力结构识别材料入口，只生成“文章1 / 文章2 / ...”目录
- 点击文章目录项后，播放器跳转到对应材料开头并开始播放
- 识别任务运行在后台线程，不阻塞 UI
- 识别失败时在界面显示明确错误信息
- 缓存同一音频的识别结果，避免重复转录
- 自动发现同目录同名 PDF 和答案 PDF，已在缓存结构中预留
- 默认使用稳定的 CPU + int8 识别
- 可在听力模式中切换到 GPU（可选）；GPU 初始化或转录失败时自动回退 CPU + int8
- 识别完成后在界面状态中显示实际使用设备：GPU / CPU / 缓存
- 新增真实识别进度条：按 Whisper segment 结束时间 / 音频总时长更新
- 自动切分失败时不再丢弃转写结果，会保留 Whisper 原始识别文本
- 缓存中保存原始转写、segment 数、音频时长、实际运行设备和回退原因
- 新增 `重新识别`：忽略缓存并覆盖同一路径缓存
- 新增 `文章模式 / 原始转写模式`：文章模式保留目录跳转，原始转写模式只读显示 Whisper 全文
- 新增 `导出听力文本`：导出文章切分文本；无文章切分时导出完整原始转写
- 识别摘要统一显示：实际设备、模型、耗时、文章数量、Whisper segment 数

## 识别规则

当前支持两类四六级常见结构：

- 标题型入口：`News Report 1`、`Conversation 1`、`Passage 1`
- 标题+正文同段入口：`News report 2 British astronaut...`、`Passage 1. We assume...`
- 提示句入口：`Questions 1 to 2 are based on the following news report/conversation/passage`
- Section Directions 后首段材料入口：用于没有清晰播报 `News Report 1` / `Conversation 1` 的音频
- 题目块后的长间隔材料入口：用于 `Conversation 2` 标题被 Whisper 漏转的情况

对于提示句，程序会继续向后寻找真正材料内容，不把提示句本身作为文章开头。

## 问题原因

25-6-2 的 Whisper 原始转写并不是只有两个片段。实际 CPU 转写能覆盖整段音频，问题主要在切分规则：

- 第一篇新闻、第一段对话有时没有稳定独立的 `News Report 1` / `Conversation 1` segment
- `News report 2`、`Passage 1` 这类标题常和正文出现在同一个 segment
- `Conversation 2` 在一次转写中标题被漏掉，只剩题目块后的正文
- 旧逻辑只认“整段完全等于标题”的形式，导致漏切
- 旧逻辑在没有文章起点时直接抛错，误把“切分失败”当成“转写失败”

本次把“转写”和“文章切分”拆开处理：只要 Whisper 有文本输出，就返回结果并缓存；文章目录为空时显示“未能自动切分文章，但已保留原始识别结果”。

## 模型与缓存

- Whisper 模型：`small`
- 默认推理配置：CPU + int8
- 可选 GPU 配置：CUDA + float16
- CPU/GPU 共用参数：`language=en`、`beam_size=5`、`vad_filter=True`、`word_timestamps=True`、`temperature=0.0`、`condition_on_previous_text=True`
- VAD 参数：`min_silence_duration_ms=500`
- CET-4 initial prompt：`College English Test Band 4 listening comprehension...`
- 模型下载位置：`%USERPROFILE%\.cache\huggingface\hub`
- 识别缓存目录：`cache/listening/`
- 缓存示例：`cache/listening/cet4_2025_12_1-a0a932f333cfde81.json`

## GPU 加速说明

GPU 是可选能力，不是必需项。

- 默认不使用 GPU，不要求安装 CUDA
- 用户切换到 `GPU（可选）` 后，程序会先尝试 `cuda + float16`
- 如果缺少 CUDA/cuBLAS，例如 `cublas64_12.dll`，程序不会崩溃，会自动回退到 `cpu + int8`
- 不建议程序自动修改系统环境变量
- 如需启用 GPU，需要自行安装与 faster-whisper / ctranslate2 兼容的 NVIDIA CUDA 与 cuBLAS 运行库，并确保 DLL 在系统可加载路径中

缓存优先级高于设备选择：同一个音频已经有缓存时，不会为了 CPU/GPU 切换而重新转录。

## 新增交互

- `自动识别文章`：优先读取缓存，缓存未命中才转写
- `重新识别`：强制跳过缓存重新转写，完成后覆盖缓存
- `文章模式`：显示文章目录，点击后播放器跳转
- `原始转写模式`：显示 `transcript_text`，不写入题目区，避免覆盖用户笔记
- `导出听力文本`：默认文件名为 `{audio_stem}_listening_articles.txt`

导出格式：

- 标题区包含音频、模型、实际设备、耗时、segment 数
- 有文章切分时按 `文章1 00:43` 分块导出
- 无文章切分时导出 `原始转写`

## 真实音频验证

验证文件：

`C:\Users\shaolang\Desktop\四级单词\真题\25-12-1\cet4_2025_12_1.mp3`

自动发现：

- `cet4_2025_12_1.pdf`
- `cet4_2025_12_1_ans.pdf`

识别结果：

- 文章1   00:41
- 文章2   02:25
- 文章3   04:13
- 文章4   07:07
- 文章5   10:03
- 文章6   13:38
- 文章7   19:30

耗时：

- 首次识别耗时：226.45 秒
- 再次打开缓存耗时：0.03 秒

## GPU / 回退验证

本机检测：

- `nvidia-smi` 可见 NVIDIA GeForce RTX 4060 Laptop GPU
- faster-whisper GPU 初始化失败：`Library cublas64_12.dll is not found or cannot be loaded`

真实音频请求 GPU 的验证结果：

- GPU 可用时首次识别耗时：本机 CUDA/cuBLAS 环境不完整，未测得 GPU 成功耗时
- GPU 不可用时自动回退 CPU：通过
- 回退后实际设备：CPU + int8
- 回退后真实音频首次识别耗时：313.34 秒
- 回退后识别文章数：7
- 回退缓存再次读取耗时：0.03 秒

## 25-6-2 验证

验证文件：

`C:\Users\shaolang\Desktop\四级单词\真题\25-6-2\cet4_2025_06_2.mp3`

请求设备：

- 用户选择：GPU（可选）
- 当前会话实际结果：GPU 初始化失败，自动回退 CPU + int8
- 回退原因：`Library cublas64_12.dll is not found or cannot be loaded`

转写与切分：

- Whisper segment 数：161
- 音频识别到的最后时间：1424.76 秒
- 进度回调次数：161
- 自动文章目录数：8
- 缓存读取耗时：0.03 秒

识别结果：

- 文章1   00:43
- 文章2   02:49
- 文章3   04:45
- 文章4   07:44
- 文章5   10:47
- 文章6   14:33
- 文章7   17:23
- 文章8   20:23

原始转写前 500 字：

```text
[00:00] College English Test Band 4 Part 2 listening comprehension.
[00:07] Section A Directions In this section, you will hear three news
[00:13] reports. At the end of each news report, you will hear two or three questions. Both the
[00:20] news report and the questions will be spoken only once. After you hear a question, you
[00:27] must choose the best answer from the four choices marked A, B, C and D. Then mark the corresponding
[00:35] letter on answer sheet 1 with a single line through th
```

## 多套目录扫描

已确认以下目录均能发现音频、试卷 PDF、答案 PDF：

- `24-6-1`
- `24-6-2`
- `25-6-1`
- `25-6-2`
- `25-12-1`
- `25-12-2`

## 测试

已运行：

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

结果：

`Ran 65 tests ... OK`

检查项：

- 识别出多个文章起点：通过
- 点击目录跳转：通过单元测试验证
- 缓存生效：通过，第二次命中缓存
- 阅读模式不受影响：通过原有阅读模式测试
- UI 不被转录卡住：识别任务已放入 `QThreadPool` 后台线程
- GPU 成功路径：通过 mock 单元测试验证
- GPU 失败回退 CPU：通过 mock 单元测试和真实音频验证
- 缓存命中：通过，命中缓存时不初始化 Whisper 模型
- 25-6-2 不再只识别两个片段：通过，实际 161 个 segment、8 个文章起点
- 自动切分失败不丢转写：通过单元测试
- 进度条真实更新：通过真实音频进度回调验证
- 自动识别缓存命中不转写：通过单元测试
- 重新识别忽略缓存并覆盖缓存：通过单元测试
- GPU 状态文案：通过 CPU、GPU、cublas 缺失、缓存四类单元测试
- 导出听力文本：通过文章模式和原始转写模式单元测试

## 后续准确率优化点

- 增加模型下拉选项：`small` / `medium` / `large-v3`，默认仍保持 `small`
- 为单个音频提供“重新识别并覆盖缓存”按钮，方便调整模型或参数后重跑
- 在缓存中保存 segment 明细，便于不用重新转写也能调试切分规则
- 针对不同年份真题继续扩充标题漏转、题目漏转、长间隔切分样本
- 对 GPU 环境提供只读诊断页：显示 `ctranslate2`、CUDA device count、supported compute types，不修改系统环境变量

## 修改文件

- `cet4_reader/listening.py`
- `cet4_reader/ui.py`
- `requirements.txt`
- `tests/test_ui_paste_article.py`
- `docs/listening_article_auto_detect_report.md`
