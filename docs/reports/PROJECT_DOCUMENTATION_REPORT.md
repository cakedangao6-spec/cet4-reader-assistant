# Project Documentation Report

生成日期：2026-06-01  
项目主体：`cet4-reader-assistant`

## 本次工作范围

本次执行的是工程化整理与项目历史梳理，只新增文档，不删除、不移动、不重命名文件，不修改功能代码或项目逻辑。

新增文档：

- `PROJECT_TIMELINE.md`
- `CHANGELOG.md`
- `README_IMPROVEMENT_PLAN.md`
- `PROJECT_SHOWCASE_REVIEW.md`
- `PROJECT_DOCUMENTATION_REPORT.md`

## 依据来源

本次梳理使用以下证据：

- Git 提交记录：
  - `c27822b Initial CET-4 project baseline`
  - `46a6b2f fix: 优化在线词典查词流程和词形还原逻辑`
- 当前主体项目代码：
  - `cet4_reader/main.py`
  - `cet4_reader/ui.py`
  - `cet4_reader/core.py`
  - `cet4_reader/dictionary.py`
  - `cet4_reader/ocr_service.py`
  - `cet4_reader/listening.py`
- 当前脚本：
  - `install.ps1`
  - `run.bat`
  - `run_app.bat`
  - `run_app_hidden.vbs`
  - `run_app_launcher.pyw`
  - `run_app_logged.cmd`
  - `scripts/download_dictionary.py`
  - `scripts/build_usage_guide.py`
  - `scripts/whisper_gpu_diagnostics.py`
- 当前测试：
  - `tests/test_core.py`
  - `tests/test_dictionary.py`
  - `tests/test_ocr_service.py`
  - `tests/test_ui_paste_article.py`
- 现有文档：
  - `README.md`
  - `QUICK_START.md`
  - `FAQ.md`
  - `docs/project_sync_report.md`
  - `docs/listening_mode_report.md`
  - `docs/mode_switch_fix_report.md`
  - `docs/mode_switch_audio_restore_report.md`
  - `docs/listening_article_auto_detect_report.md`
  - `docs/whisper_gpu_support_report.md`
  - `git_baseline_plan.md`
  - `git_commit_report.md`
  - `CLEANUP_PLAN.md`

## `cet4-abloop-player` 依赖检查

已按要求检查 `cet4-abloop-player` 是否仍与主体项目存在代码依赖。

检查结论：

- 未发现 `cet4-reader-assistant` 源码、脚本或测试导入 `cet4-abloop-player`。
- 未发现 `cet4-reader-assistant` 运行入口依赖 `cet4-abloop-player`。
- 未发现 README/FAQ/QUICK_START 将 `cet4-abloop-player` 作为当前主体功能。
- 仅在历史报告中出现过使用 `cet4-abloop-player/materials/listening/25-6-1/*.mp3` 作为真实音频验证样本的记录。

风险评估：

- 从代码运行角度看，删除 `cet4-abloop-player` 风险较低。
- 从历史追溯角度看，删除后部分报告中的旧验证路径会失效，但不影响应用。
- 如果后续测试仍需要真实音频样本，应先把样本迁移到主体项目外部资料目录或测试 fixture。

后续建议：

- 第二阶段确认无测试样本依赖后，将 `cet4-abloop-player` 作为废弃实验项目归档或删除。
- README、CHANGELOG、项目介绍不重点体现该目录。
- 若保留历史记录，只在内部报告中注明它是早期听力播放实验，不作为主线。

## 项目发展路线梳理结果

本次已将项目发展整理为以下阶段：

1. 阅读助手基线：文章粘贴、题目拆分、查词、生词本、导出、会话恢复。
2. 词典能力增强：离线词典、SQLite、在线查词、词形还原和兜底。
3. TXT/文本导入与清洗：编码兼容、题目识别、OCR 噪声清理、区块重识别。
4. OCR 功能接入：PaddleOCR、PP-OCRv5、图像缩放、主列选择。
5. 听力模式进入主体项目：模式切换、音频播放、进度标记。
6. 模式切换与音频恢复修复：QActionGroup、遮挡修复、session 音频恢复。
7. Whisper 自动识别：后台转录、文章切分、缓存、原始转写、导出。
8. GPU 支持与诊断：CUDA 检测、float16、CPU 回退、诊断脚本。
9. 启动器、图标与打包体验：隐藏启动、日志启动、图标资源。

## README 评估结果

当前 README 优点：

- 项目定位清晰，能说明阅读助手基础功能。
- 覆盖查词顺序、离线词典、目录约定、粘贴文本和会话恢复。
- 链接了 QUICK_START 和 FAQ。

当前 README 不足：

- 未体现听力模式、Whisper、GPU、OCR 工程细节和启动器优化。
- 缺少截图和技术栈。
- 缺少安装环境说明和测试命令。
- 缺少项目结构和开发历程简介。
- 不适合作为完整 GitHub 展示首页。

已生成 `README_IMPROVEMENT_PLAN.md`，给出建议结构和注意事项。

## 历史文档整理方案

建议后续整理为：

```text
docs/
├─ usage/
│  ├─ CET4_阅读助手使用教程.docx
│  └─ usage_guide_ascii.docx
├─ reports/
│  ├─ listening_mode_report.md
│  ├─ mode_switch_fix_report.md
│  ├─ mode_switch_audio_restore_report.md
│  ├─ listening_article_auto_detect_report.md
│  └─ whisper_gpu_support_report.md
├─ history/
│  ├─ project_sync_report.md
│  ├─ git_baseline_plan.md
│  ├─ git_commit_report.md
│  └─ cleanup_plan.md
└─ assets/
   └─ screenshots/
```

第一阶段不移动文件。建议第二阶段再执行归档。

整理原则：

- 使用教程留在 `docs/usage/`。
- 功能开发报告进入 `docs/reports/`。
- Git、同步、清理等过程记录进入 `docs/history/`。
- README 只保留对外展示需要的高密度信息，不堆过程报告。

## GitHub 展示评估结果

项目适合展示的亮点：

- 真实学习场景明确。
- 阅读、词典、生词、OCR、听力识别形成完整工具链。
- 有 GPU 加速和 CPU 回退这样的工程处理。
- 有测试覆盖和历史问题修复记录。
- 能体现软件开发、测试、桌面应用、AI 工具集成和 Windows 环境处理能力。

当前影响展示的问题：

- README 不完整。
- 废弃目录干扰主线。
- 新功能未提交，Git 历史不完整。
- 缺少截图、CI、release 和架构说明。

已生成 `PROJECT_SHOWCASE_REVIEW.md`，面向 GitHub 展示和实习简历场景给出分析。

## 后续建议

优先级最高：

- 确认当前未跟踪文件是否纳入正式项目，尤其是 `listening.py`、启动器脚本、图标、GPU 诊断脚本和报告。
- 改写 README。
- 将 `cet4-abloop-player` 从展示主线中移除或归档。
- 清理虚拟环境、缓存、日志、模型和本地系统缓存。

中期：

- 建立 `docs/reports/` 和 `docs/history/`。
- 加入 GitHub Actions。
- 拆分过大的 `ui.py`。
- 补充截图和演示素材。

长期：

- 建立版本号和 release 说明。
- 规范 OCR、Whisper、词典等大文件下载/缓存策略。
- 形成可交接的开发文档和维护手册。

## 快速状态

项目：`cet4-reader-assistant`

当前状态：主体项目已具备阅读训练、生词管理、OCR 文本整理、听力音频播放、Whisper 自动识别和 GPU 可选加速能力；部分最新功能仍处于当前工作区状态，需后续确认提交。

主要功能：阅读文章粘贴与题目拆分、点击查词、在线/离线词典、词形还原、生词本导出、历史词表、搜索高亮、OCR 清洗、听力模式、音频播放、进度标记、Whisper 转写、文章目录跳转、听力文本导出、GPU 检测与 CPU 回退。

项目入口：`cet4-reader-assistant/cet4_reader/main.py`

运行方式：在 `cet4-reader-assistant` 目录运行 `.\run.bat`；环境已准备好时可运行 `.\run_app.bat` 或 `.\.venv\Scripts\python.exe -m cet4_reader.main`。

最近重要改动：听力模式、faster-whisper 自动识别、25-6-2 听力切分修复、GPU 推理检测与 CPU 回退、音频路径恢复、隐藏启动器和图标资源。

下一步建议：确认并提交当前主体项目最新文件，重写 README，归档历史报告，移除或归档废弃的 `cet4-abloop-player`，补充截图和 CI，清理大缓存和本地运行产物。

