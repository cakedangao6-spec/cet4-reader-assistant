# CET-4 阅读助手

[English](./README.md) | 简体中文

`CET-4 阅读助手` 是一个面向大学英语四级备考的 Windows 桌面工具，覆盖阅读训练、听力训练、生词管理、OCR 文本整理和 Whisper 听力转写。

它解决的是刷题时反复切换工具的问题：阅读材料需要查词、标记、生词导出；纸质或截图材料需要 OCR 整理；听力音频需要播放、定位、转写和分段。项目把这些流程集中在一个本地优先的 PyQt6 应用里，适合 CET-4 学生、自主备考者，以及需要整理四级练习材料的使用者。

当前展示和维护的主体项目是 `cet4-reader-assistant`。`cet4-abloop-player` 是已废弃的早期实验目录，不作为本项目主页、功能亮点或维护主线。

## 功能概览

### 阅读模式

- 自动拆分文章和题目：粘贴阅读材料后，根据题号、`Questions ...`、`Question 1`、中文提示等标志尝试拆分阅读区和题目区。
- 试卷 PDF 导入：导入文本型四级真题 PDF 后，可从篇章列表中选择选词填空、长篇阅读、第一篇短篇阅读或第二篇短篇阅读。
- 单词查词：点击文章或题目中的英文单词即可查询释义。
- 本地 AI 讲题：侧边栏可调用 Ollama 的 `qwen3:8b`，围绕当前文章、选中文本和题目选项讲解做题思路。
- 生词本：双击单词加入生词，也可以在右侧手动输入；导出到 `vocab/vocab.txt`，并保留历史快照。
- 搜索与高亮：支持 `Ctrl+F` 搜索；选中文本后右键添加或取消高亮。
- TXT 导入与文本整理：支持常见编码文本读取，清洗页码、题号、选项、Section/Passage 等噪声行。
- 会话恢复：自动保存上次文章、题目、答案、生词、高亮和部分运行状态到 `runtime/session.json`。

### OCR

- OCR 识别：使用 PaddleOCR 识别图片中的英文阅读材料。
- 文本清洗：对 OCR 结果做换行、噪声行、题目边界等整理。
- 阅读区整理：识别后交给阅读模式继续处理，可用于查词、生词、高亮和导出。
- 版面处理：对大图自动缩放，并在检测到 Passage 标志时优先选择主要阅读文本列。

### 听力模式

- 音频播放：支持导入本地音频，进行播放、暂停、进度拖动和点击跳转。
- 进度标记：可在当前播放位置添加标记，并支持跳转或删除。
- Whisper 自动识别：使用 faster-whisper 对听力音频进行离线转写。
- 自动文章切分：根据 CET-4 听力材料结构识别“文章1 / 文章2 / ...”入口，点击目录可跳转到对应音频位置。
- 原始转写：自动切分失败时仍保留 Whisper 原始转写，不丢弃识别结果。
- 听力文本导出：可导出文章切分文本；没有切分结果时导出完整原始转写。
- 缓存识别结果：同一音频的识别结果缓存到 `cache/listening/`，避免重复转写。

### GPU 支持

- GPU 可选加速：默认使用 CPU + int8，用户可在听力模式中选择 GPU。
- 自动回退 CPU：GPU 不可用、CUDA 检测失败、`float16` 不支持或转录失败时，自动回退到 CPU + int8。
- 运行状态显示：识别完成后显示实际设备、模型、耗时、文章数量和 Whisper segment 数。
- GPU 诊断工具：`scripts/whisper_gpu_diagnostics.py` 可检查 `nvidia-smi`、faster-whisper、ctranslate2 和本地音频推理路径。

## 技术栈

| 类别 | 技术 |
| --- | --- |
| 应用语言 | Python |
| 桌面界面 | PyQt6 |
| OCR | PaddleOCR |
| PDF 解析 | pypdf |
| 本地 AI 讲题 | Ollama |
| 听力转写 | faster-whisper |
| 本地数据 | CSV, SQLite |
| 测试 | unittest |

## 项目结构

```text
cet4-reader-assistant/
├─ cet4_reader/
│  ├─ main.py              # 应用入口
│  ├─ ai_tutor.py          # 本地 Ollama 讲题提示词与 API 调用
│  ├─ ui.py                # PyQt6 主界面、阅读/听力交互
│  ├─ core.py              # 文本处理、生词导出、历史合并
│  ├─ dictionary.py        # 本地/在线词典、词形还原
│  ├─ exam_paper.py        # 四级试卷 PDF 解析与阅读篇章切分
│  ├─ ocr_service.py       # PaddleOCR 服务与 OCR 结果整理
│  └─ listening.py         # Whisper 转写、听力文章切分、GPU 回退
├─ scripts/
│  ├─ download_dictionary.py
│  ├─ build_usage_guide.py
│  └─ whisper_gpu_diagnostics.py
├─ tests/                  # unittest 测试
├─ docs/                   # 使用教程和历史功能报告
├─ data/dictionaries/      # 词典数据目录
├─ assets/                 # 图标和截图素材
├─ install.ps1             # Windows 环境安装脚本
├─ run.bat                 # 推荐启动入口
├─ run_app.bat             # 已安装环境下的启动入口
├─ run_tests.ps1           # 测试入口
├─ requirements.txt
├─ README.md               # 英文主页
└─ README.zh-CN.md         # 中文说明
```

运行时会产生 `.venv/`、`runtime/`、`cache/`、`vocab/`、OCR/Whisper 模型缓存等本地文件。这些内容不应作为源代码提交。

## 安装与启动

当前项目的安装脚本和启动脚本以 Windows 为主要目标。

环境要求：

- Windows
- Python 3.9-3.13
- PowerShell

推荐方式：

```powershell
cd cet4-reader-assistant
.\run.bat
```

首次运行时，`run.bat` 会在缺少虚拟环境或 PyQt6 时调用 `install.ps1`：

- 创建 `.venv/`
- 升级 pip
- 安装 `paddlepaddle==3.3.1`
- 安装 `requirements.txt`
- 尝试下载并构建扩展离线词典
- 运行单元测试

如果需要手动安装：

```powershell
cd cet4-reader-assistant
powershell -ExecutionPolicy Bypass -File .\install.ps1
.\run_app.bat
```

词典下载失败不会阻止应用使用。项目自带 `data/dictionaries/cet_common.csv`，可作为基础离线词表继续运行。

## 使用说明

### 阅读模式

1. 启动应用后进入阅读模式。
2. 将英文阅读材料粘贴到文章区，程序会尝试自动拆分文章和题目；也可以点击 `导入试卷 PDF` 后从篇章列表选择要练习的阅读篇章。
3. 点击单词查看释义，双击单词加入生词。
4. 使用 `Ctrl+F` 搜索，或选中文本后右键高亮。
5. 点击 `导出 vocab.txt` 导出生词；历史词表会写入 `vocab/history/`。
6. 下次启动时会自动恢复上次会话。

### OCR

1. 使用 OCR 功能识别试卷截图或照片。
2. 程序会调用 PaddleOCR 生成文本，并做基础清洗。
3. 将整理后的文本放入阅读流程，继续进行拆分、查词、生词和高亮。
4. OCR 结果仍可手动编辑，适合处理识别错误或版面复杂的材料。

### 听力模式

1. 点击顶部工具栏的 `听力模式`。
2. 点击 `导入音频`，选择本地音频文件。
3. 使用播放、暂停、进度条和标记功能进行精听。
4. 点击 `自动识别文章`，使用 faster-whisper 进行转写和文章入口识别。
5. 在 `文章模式` 中点击文章目录跳转音频位置，或切换到 `原始转写模式` 查看完整转写。
6. 点击 `导出听力文本` 保存识别结果。

GPU 是可选项。默认 CPU 模式更稳；选择 GPU 后，如果运行环境不满足 CUDA / ctranslate2 要求，程序会自动回退 CPU。

## 测试

已有测试覆盖核心文本处理、词典、OCR、阅读/听力 UI 流程、Whisper 切分、缓存和 GPU 回退等场景。

```powershell
cd cet4-reader-assistant
.\run_tests.ps1
```

也可以直接运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 开发历程

本项目没有伪造语义化版本号，历史按功能阶段整理：

- 阅读助手基线：完成文章粘贴、题目拆分、查词、生词本、导出、搜索高亮和会话恢复。
- 词典能力增强：加入离线词典、SQLite 词典、在线查词、词形还原和查询兜底。
- 文本整理扩展：支持 TXT 导入、编码兼容、OCR 噪声清理和题目边界识别。
- OCR 接入：使用 PaddleOCR 识别图片材料，并对大图和主要文本列做处理。
- 听力模式：加入阅读/听力双模式、本地音频播放和进度标记。
- Whisper 自动识别：加入 faster-whisper 后台转写、缓存、文章切分、原始转写和文本导出。
- GPU 支持：加入 CUDA 检测、`float16` 支持判断、GPU 失败后 CPU 自动回退和诊断脚本。
- 启动体验：加入 Windows 启动脚本、隐藏启动器、日志启动器和图标资源。

更完整的历史可参考 [PROJECT_TIMELINE.md](../PROJECT_TIMELINE.md) 和 [CHANGELOG.md](../CHANGELOG.md)。

## 项目亮点

- 本地优先：核心阅读、查词、生词和听力流程围绕本地桌面应用设计。
- 离线能力：内置基础离线词表，扩展词典和模型缓存可在本地复用。
- OCR 辅助：能处理纸质试卷、截图和复制格式混乱的材料。
- Whisper 集成：把听力音频播放、转写、文章定位和导出连成完整流程。
- GPU 自动回退：GPU 只是加速选项，失败时不影响继续使用。
- 长期维护痕迹：保留了功能报告、修复记录、测试和安装脚本，适合交接和持续迭代。

## 当前限制与后续方向

- 当前安装和启动流程主要面向 Windows。
- 首次安装 PaddleOCR、PaddlePaddle、faster-whisper 或模型缓存时可能耗时较长。
- GPU 加速依赖本机 NVIDIA CUDA / cuBLAS / ctranslate2 环境，项目只做检测与回退，不自动修改系统级 GPU 运行库。
- README 展示截图仍需补充应用界面截图；当前截图目录主要是 OCR 输入素材。
- 后续建议补充 GitHub Actions、正式截图、release 打包说明，并继续拆分较大的 UI 模块。

## 相关文档

- [QUICK_START.md](./QUICK_START.md)
- [FAQ.md](./FAQ.md)
- [docs/listening_article_auto_detect_report.md](./docs/listening_article_auto_detect_report.md)
- [docs/whisper_gpu_support_report.md](./docs/whisper_gpu_support_report.md)
