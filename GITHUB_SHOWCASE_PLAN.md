# GitHub Showcase Plan

生成日期：2026-06-01  
项目主体：`cet4-reader-assistant`

## 当前仓库优点

- 项目场景明确：面向 CET-4 阅读和听力训练，不是泛化学习工具。
- 功能链路完整：阅读材料导入、题目拆分、查词、生词本、OCR、听力播放、Whisper 转写和导出形成闭环。
- 本地优先：桌面应用、离线词典、SQLite 词典、OCR/Whisper 缓存都围绕本地使用设计。
- 工程处理有价值：GPU 可选加速、CPU 自动回退、音频缓存、会话恢复、Windows 启动脚本都体现了实际使用中的稳定性考虑。
- 有测试基础：`tests/` 覆盖核心逻辑、词典、OCR、阅读/听力 UI 流程、Whisper 切分和 GPU 回退。
- 有维护记录：`PROJECT_TIMELINE.md`、`CHANGELOG.md` 和 `docs/*_report.md` 能说明项目不是一次性 demo。

## 当前仓库不足

- GitHub 首页原 README 停留在阅读助手阶段，未覆盖听力、Whisper、GPU 和 OCR 展示。
- 当前仓库根目录同时存在废弃的 `cet4-abloop-player`，容易稀释主体项目。
- 缺少应用界面截图，现有 `assets/screenshots` 主要是纸质试卷照片。
- 缺少 CI，用户无法直接从 GitHub 状态看到测试是否持续通过。
- 缺少正式 release 或打包说明，目前仍以源码运行和 Windows 脚本为主。
- 历史报告分布在根目录和 `docs/`，后续需要归档成更清晰的文档层级。
- `ui.py` 体积较大，长期维护时可读性和模块边界仍有优化空间。

## 建议补充内容

短期优先：

- 使用新版 `cet4-reader-assistant/README.md` 作为项目主页说明。
- 补充 3-5 张应用截图：阅读模式、查词生词、OCR、听力模式、Whisper 识别结果。
- 在仓库根目录增加简短总览 README，明确当前主项目是 `cet4-reader-assistant`，并说明 `cet4-abloop-player` 已废弃。
- 修正 `QUICK_START.md` 中旧路径，避免出现 `D:\reasonix_sandbox`。
- 确认听力、GPU、启动器、图标和报告相关文件是否纳入正式 Git 提交。

中期建议：

- 增加 GitHub Actions，至少运行 `python -m unittest discover -s tests -v`。
- 增加 `docs/reports/` 与 `docs/history/`，归档功能报告和历史整理文档。
- 增加 GPU 诊断说明页，集中解释 CUDA/cuBLAS、ctranslate2 和自动回退机制。
- 增加 release 或打包说明，说明源码运行与可执行包之间的差异。
- 拆分 `ui.py`，将阅读页面、听力播放器、生词侧栏、后台 worker 分离。

长期建议：

- 建立版本号和 release notes。
- 标准化 OCR、Whisper、词典大文件的缓存和重建流程。
- 提供更小的测试 fixture，方便 CI 覆盖 OCR/听力逻辑的核心路径。
- 将项目定位稳定为“CET-4 本地阅读与听力训练桌面助手”。

## 简历展示建议

可使用的项目标题：

`CET-4 阅读与听力训练桌面助手`

可使用的简历描述：

- 开发基于 Python/PyQt6 的 CET-4 桌面训练工具，支持阅读材料拆分、点击查词、生词管理、搜索高亮和会话恢复。
- 集成 PaddleOCR 对纸质/截图试卷进行英文文本识别，并通过清洗规则整理阅读区和题目区。
- 集成 faster-whisper 实现听力音频离线转写、文章入口自动切分、原始转写保留和听力文本导出。
- 为 Whisper 推理增加 GPU 可选加速、CUDA 能力检测和 CPU 自动回退，提升可用性和环境兼容性。
- 编写 unittest 覆盖文本处理、词典、OCR、UI 粘贴流程、听力切分、缓存和 GPU 回退等核心路径。

可突出能力：

- 桌面应用开发
- 文本处理与状态管理
- OCR/语音识别工具集成
- 本地数据和缓存设计
- Windows 环境工程化
- 单元测试和回归修复

## 面试介绍建议

推荐 1 分钟介绍：

这个项目是我为 CET-4 备考场景做的本地桌面工具，核心目标是减少阅读和听力刷题时在多个工具之间切换。阅读模式支持粘贴文章后自动拆分题目、点击查词、生词本导出、搜索高亮和会话恢复；OCR 模块用 PaddleOCR 处理纸质或截图材料；听力模式集成音频播放、进度标记和 faster-whisper 自动转写，可以把听力音频切分成文章目录并导出文本。工程上我重点处理了本地优先、缓存复用、GPU 可选加速和 CPU 自动回退，并用 unittest 覆盖了文本处理、词典、OCR、UI 流程和听力切分等核心逻辑。

面试可展开的问题：

- 为什么选择 PyQt6 做桌面端，而不是 Web？
- 阅读文章和题目如何自动拆分？
- 词典查询如何处理离线、在线和词形还原？
- OCR 结果有哪些噪声，如何清洗？
- faster-whisper 的 segment 如何转成听力文章目录？
- GPU 不可用时如何避免应用崩溃？
- UI 模式切换 bug 是如何定位和修复的？
- 后续如何拆分 `ui.py` 并加入 CI？

## 展示主线

GitHub 首页和简历展示应聚焦 `cet4-reader-assistant`：

1. CET-4 阅读训练
2. 生词管理和离线查词
3. OCR 文本整理
4. CET-4 听力训练
5. Whisper 自动转写和 GPU 自动回退
6. 测试、文档和长期维护

不要把 `cet4-abloop-player` 作为展示内容、项目亮点或 README 主线。
