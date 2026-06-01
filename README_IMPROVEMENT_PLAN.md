# README Improvement Plan

生成日期：2026-06-01  
项目主体：`cet4-reader-assistant`

## 当前 README 质量评估

当前 `README.md` 能说明阅读助手的基础用途，覆盖了阅读粘贴、查词、生词本、离线词典、目录约定、会话恢复和继续阅读链接。它适合早期内部使用，但作为 GitHub 首页和简历项目展示还不够完整。

主要不足：

- 没有体现当前已经扩展到听力模式。
- 没有介绍 Whisper 自动识别、GPU 可选加速、CPU 回退、缓存等技术亮点。
- 没有截图或界面展示。
- 技术栈不完整，只能从依赖文件间接看出 PyQt6、PaddleOCR、faster-whisper。
- 安装方式偏简略，没有说明 Python 版本、Windows 环境、首次运行会安装依赖和下载词典。
- 使用方式偏阅读模式，缺少听力模式流程。
- 没有项目结构说明。
- 没有测试和工程化说明。
- 没有开发历程简介，难以体现持续维护过程。
- `QUICK_START.md` 中仍出现 `D:\reasonix_sandbox\...` 旧路径，需要后续修正。

## 建议 README 结构

### 1. 项目简介

建议首页开头直接说明：

`CET-4 阅读助手` 是一个面向大学英语四级训练的 Windows 桌面工具，覆盖阅读文章查词、生词本、OCR 文本整理，以及听力音频转写和文章定位。

建议突出：

- 本地优先
- 面向真实四级刷题流程
- 阅读和听力一体化
- 可离线运行核心功能
- 支持 Whisper 自动转录和 GPU 加速

### 2. 功能展示

建议分成“阅读模式”和“听力模式”两组。

阅读模式：

- 粘贴文章，自动拆分文章和题目
- 点击查词
- 在线查词和本地词典兜底
- 双击加入生词
- 生词导出和历史合并
- 搜索和高亮
- OCR 文本清洗
- 会话恢复

听力模式：

- 导入本地音频
- 播放、暂停、拖动进度
- 添加听力进度标记
- Whisper 自动识别文章开头
- 文章目录点击跳转
- 原始转写查看
- 听力文本导出
- CPU 稳定模式和 GPU 可选模式
- 缓存识别结果

### 3. 技术栈

建议列出：

| 类别 | 技术 |
| --- | --- |
| 桌面 UI | Python, PyQt6 |
| 文本处理 | 正则、编码检测、OCR 清洗规则 |
| 词典 | CSV, SQLite, ECDICT, 在线 API |
| OCR | PaddleOCR, PP-OCRv5 |
| 听力识别 | faster-whisper, CTranslate2 |
| GPU | CUDA / cuBLAS / cuDNN via ctranslate2 |
| 测试 | unittest, PyQt6 QtTest, mock |
| 文档 | Markdown, python-docx |

### 4. 软件截图建议

建议补充 3-5 张图片，放在 `docs/assets/` 或 `assets/screenshots/`：

- 阅读模式主界面：文章区、题目区、生词栏
- 点击单词查词效果
- 高亮和搜索效果
- 听力模式：音频播放、文章识别目录、识别进度
- GPU/CPU 识别状态或导出听力文本效果

当前仓库已有：

- `cet4-reader-assistant/assets/screenshots/1778995092752.jpg`
- `cet4-reader-assistant/assets/screenshots/1778995092772.jpg`

需要确认这两张图是否适合作为 GitHub 首页展示图。如果不适合，建议重新截取当前版本界面。

### 5. 安装方式

建议写清楚：

- 系统：Windows
- Python：3.9-3.13
- 推荐从项目目录运行
- 首次运行：

```powershell
cd cet4-reader-assistant
.\run.bat
```

- 手动安装：

```powershell
cd cet4-reader-assistant
powershell -ExecutionPolicy Bypass -File .\install.ps1
.\run_app.bat
```

需要说明：

- `.venv/` 会自动创建，不提交到 Git
- ECDICT 大词典会尝试下载，失败时仍可使用内置 `cet_common.csv`
- PaddleOCR 模型和 Whisper 模型可能产生缓存，不建议提交
- GPU 是可选，不是必需

### 6. 使用方式

建议按任务写：

阅读训练：

1. 打开应用
2. 粘贴英文文章和题目
3. 点击单词查看释义
4. 双击加入生词
5. 使用高亮和搜索
6. 导出词表

OCR：

1. 导入或粘贴 OCR 文本
2. 使用清洗后的文章区继续阅读
3. 手动调整拆分结果

听力训练：

1. 切换听力模式
2. 导入音频
3. 播放并添加标记
4. 点击自动识别文章
5. 使用文章目录跳转
6. 查看原始转写或导出文本

### 7. 项目结构

建议加入：

```text
cet4-reader-assistant/
├─ cet4_reader/
│  ├─ main.py          # 应用入口
│  ├─ ui.py            # PyQt6 主界面
│  ├─ core.py          # 文本处理、生词导出、历史合并
│  ├─ dictionary.py    # 本地/在线词典与词形还原
│  ├─ ocr_service.py   # OCR 服务
│  └─ listening.py     # Whisper 听力识别与文章切分
├─ scripts/
│  ├─ download_dictionary.py
│  ├─ build_usage_guide.py
│  └─ whisper_gpu_diagnostics.py
├─ tests/
├─ docs/
├─ data/dictionaries/
├─ vocab/
└─ run.bat
```

### 8. 开发历程简介

建议用简短小节说明：

- 起步：阅读文章查词和生词本
- 增强：离线词典、在线查词、词形还原
- 扩展：TXT/OCR 文本整理
- 扩展：听力模式和本地音频播放
- 深化：Whisper 自动识别、缓存和文章切分
- 优化：GPU 可选加速、CPU 自动回退、启动器和图标

注意只写已由代码和报告支持的事实，不写未发生的版本号。

### 9. 测试与质量

建议补充：

```powershell
cd cet4-reader-assistant
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

可说明当前测试覆盖：

- 文本清洗和编码读取
- 生词导出和历史合并
- 本地词典、SQLite 词典、词形还原
- OCR 图片预处理
- 阅读/听力 UI 流程
- Whisper 切分规则、缓存、GPU 回退

### 10. 后续规划

建议写成短列表：

- 完善 README 截图和演示
- 提供正式 release 打包说明
- 增加 GitHub Actions
- 模块化 UI 和听力识别逻辑
- 完善 GPU 诊断说明
- 整理历史报告和缓存目录

## README 改写注意事项

- 不要把 `cet4-abloop-player` 写成项目亮点。
- 不要使用旧路径 `D:\reasonix_sandbox`。
- 不要声称已经打包发布，除非后续确实完成。
- 不要声称支持 macOS/Linux，当前启动脚本和依赖准备明显偏 Windows。
- GPU 支持要写成“可选加速”，不要写成必要条件。
- 词典、OCR、Whisper 模型相关大文件要写明可重建或外部缓存。

