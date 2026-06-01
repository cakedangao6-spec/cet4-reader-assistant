# Changelog

说明：本文件按功能阶段整理，不伪造语义化版本号。依据来自 Git 提交、当前代码、README/FAQ/QUICK_START 和历史报告。

## 当前工作区阶段：听力识别、GPU 与启动器增强

### Added

- 新增听力模式，支持“阅读模式 / 听力模式”切换。
- 新增本地音频导入和播放能力，支持 MP3 等常见格式。
- 新增音频进度条、播放/暂停、点击跳转、拖动跳转。
- 新增听力进度标记，可添加、跳转和删除。
- 新增自动识别文章功能，使用 faster-whisper 转录听力音频。
- 新增 CET-4 听力材料切分规则，生成“文章1 / 文章2 / ...”目录。
- 新增识别缓存，避免同一音频重复转录。
- 新增重新识别功能，可跳过缓存并覆盖旧识别结果。
- 新增文章模式和原始转写模式。
- 新增听力文本导出功能。
- 新增 GPU 可选模式，支持 `cuda + float16`。
- 新增 GPU 不可用或初始化失败时的 CPU 自动回退。
- 新增识别摘要，显示实际设备、模型、耗时、文章数量和 segment 数。
- 新增 `scripts/whisper_gpu_diagnostics.py`，用于检查 faster-whisper 和 ctranslate2 GPU 环境。
- 新增隐藏窗口启动脚本和日志启动器：`run_app_hidden.vbs`、`run_app_launcher.pyw`、`run_app_logged.cmd`。
- 新增图标相关资源：`assets/app.ico`、`assets/app_icon_preview.png`、`assets/app_icon_crop_preview.png`。

### Changed

- `requirements.txt` 增加 `faster-whisper>=1.1,<2`。
- 听力模式粘贴文本时不再触发阅读文章/题目拆分，完整保留到听力题目区。
- 音频路径保存到 `runtime/session.json`，启动时尝试恢复。
- Whisper 默认运行策略保持 CPU + int8，以兼顾稳定性。
- GPU 模式只作为可选加速路径，实际失败时不让应用崩溃。

### Fixed

- 修复阅读模式和听力模式按钮状态与页面状态不同步的问题。
- 修复听力模式下“阅读模式”按钮被空 `QLabel` 遮挡导致点击无反应的问题。
- 修复音频路径未持久化、重启后不能恢复的问题。
- 修复自动切分失败时误认为转写失败的问题，改为保留原始转写。
- 修复 25-6-2 听力材料切分异常，支持标题漏转、标题和正文同段、长间隔材料入口等场景。
- 修复 GPU 缺少 `cublas64_12.dll` 等运行库时的崩溃风险，改为提示并回退 CPU。

### Improved

- 听力识别放入后台线程，避免阻塞 UI。
- 识别进度按 Whisper segment 结束时间更新。
- 缓存命中时显示“缓存：已读取”状态。
- GPU 成功路径和回退路径均有测试覆盖。
- 历史报告记录 RTX 4060 环境下 `small + cuda/float16` 较 CPU 约 6.48x 加速。

## 2026-05-30 阶段：听力模式初版

### Added

- 新增阅读模式和听力模式的页面切换。
- 新增听力题目区。
- 新增本地 MP3 播放控件。
- 新增播放位置标记功能。
- 新增听力模式粘贴测试。
- 新增听力标记点添加、跳转、删除测试。

### Changed

- 通用编辑能力根据当前模式作用于阅读区或听力题目区。
- 听力模式复用高亮、字体颜色、清除格式、翻译、生词管理和导出能力。

### Fixed

- 修复模式切换逻辑和 QAction 状态同步问题。
- 修复工具栏按钮被不可见控件覆盖的问题。

### Improved

- 补充模式切换、按钮可点击、音频路径保存和恢复测试。

## 2026-05-27 阶段：词典与查词流程修复

来源提交：`46a6b2f fix: 优化在线词典查词流程和词形还原逻辑`

### Added

- 新增在线查词 provider 复用流程 `_try_providers`。
- 新增在线兜底候选 `_simple_online_fallbacks`。
- 生词保存前增加词形还原，统一保存原型词。

### Changed

- 查词流程调整为在线优先尝试，失败或无结果后回退本地词典。
- 在线查词原词失败后尝试词形还原形式。

### Fixed

- 修复 `redesigned -> redesigne` 这类 silent e 误加问题。
- 修复网络失败时查词流程可能体验不稳定的问题。

### Improved

- `redesigned`、`redesign`、`redesigning` 等形式可统一归入 `redesign`。
- 本地词典与在线词典之间的兜底关系更清晰。

## 2026-05-27 阶段：项目基线进入 Git

来源提交：`c27822b Initial CET-4 project baseline`

### Added

- 新增 PyQt6 桌面应用主体 `cet4_reader/`。
- 新增阅读文章区、题目区和右侧生词区。
- 新增粘贴文章后自动拆分文章/题目功能。
- 新增点击查词、双击加入生词、手动添加生词。
- 新增生词导出到 `vocab/vocab.txt`。
- 新增生词历史合并和 `AAA_vocab.txt` 汇总逻辑。
- 新增 `Ctrl+F` 搜索和高亮。
- 新增右键高亮/取消高亮。
- 新增会话保存与恢复。
- 新增 OCR 服务 `ocr_service.py`。
- 新增离线词典下载和构建脚本。
- 新增 Word 使用教程生成脚本。
- 新增 `README.md`、`QUICK_START.md`、`FAQ.md`、`docs/usage/`。
- 新增安装和运行脚本：`install.ps1`、`run.bat`、`run_app.bat`、`run_tests.ps1`。
- 新增测试：核心逻辑、词典、OCR、UI 粘贴流程。

### Changed

- 将 `cet4-reader-assistant` 从 `D:\reasonix_sandbox` 同步到当前正式项目目录。
- 上层 Git 仓库作为项目管理入口。

### Improved

- 根级 `.gitignore` 排除虚拟环境、缓存、日志、模型、词典大文件、运行状态和渲染产物。
- 安装脚本支持 Python 3.9-3.13。
- 安装流程自动准备依赖并尝试下载词典。

## 早期同步前阶段：阅读助手原型

### Added

- 面向 CET-4 阅读训练的桌面辅助工具原型。
- 文章阅读、查词、生词本、导出和会话恢复等核心功能。

### Improved

- 逐步形成 README、FAQ、QUICK_START 和使用教程文档。

## 后续规划

### Added

- 补充正式截图、演示 GIF 或短视频。
- 增加 GitHub Actions，运行单元测试。
- 增加 release 包或打包说明。

### Changed

- 将 README 升级为 GitHub 展示首页。
- 将历史报告移动或归档到 `docs/history/` 和 `docs/reports/`。

### Improved

- 模块拆分听力、OCR、词典和 UI。
- 完善模型缓存、离线词典和 GPU 环境的重建说明。
- 为简历项目描述沉淀技术亮点和问题修复案例。

