# CET-4 Reader Assistant Project Timeline

生成日期：2026-06-01  
项目主体：`cet4-reader-assistant`  
说明：本时间线只以当前代码、Git 提交、README/FAQ/QUICK_START、`docs/*_report.md`、根目录 Git 记录为依据。`cet4-abloop-player` 已按废弃实验项目处理，不作为主线。

## 项目起源

`cet4-reader-assistant` 最初形成于一个明确的桌面学习工具目标：为英语四级阅读训练提供“粘贴文章、查词、记录生词、导出复习词表”的本地辅助环境。

从 `README.md`、`QUICK_START.md`、`FAQ.md` 和 2026-05-27 的 `project_sync_report.md` 看，项目在进入当前仓库前已经有一个可运行版本，来源目录为 `D:\reasonix_sandbox\cet4-reader-assistant`。2026-05-27 同步到正式目录 `D:\Codex Project\CET-4\cet4-reader-assistant` 后，纳入上层 Git 仓库管理。

当前 Git 主线能确认的提交：

- `c27822b`，2026-05-27 22:02，`Initial CET-4 project baseline`
- `46a6b2f`，2026-05-27 22:14，`fix: 优化在线词典查词流程和词形还原逻辑`

听力、Whisper、GPU、启动器和图标相关内容主要来自 2026-05-30 至 2026-05-31 的当前工作区代码与历史报告，尚不能从 Git 提交历史中确认已提交。

## 发展阶段

### 阶段1：阅读助手基线

证据来源：`README.md`、`QUICK_START.md`、`project_sync_report.md`、`c27822b`。

主要功能：

- PyQt6 桌面应用入口：`cet4_reader/main.py`
- 主界面：`cet4_reader/ui.py`
- 阅读文章区和题目区分离
- 支持粘贴英文文章
- 粘贴后根据 `36.`、`46.`、`Questions 36-40`、`Question 1`、`对应题目` 等标志自动拆分文章和题目
- 点击文章或题目中的单词查词
- 双击单词加入生词
- 右侧手动添加生词
- 生词自动去重、排序
- 导出当前生词到 `vocab/vocab.txt`
- 导出历史到 `vocab/history/`
- `Ctrl+F` 搜索文章并高亮
- 选中文本后右键高亮或取消高亮
- 自动保存和恢复会话到 `runtime/session.json`
- “一键清空 / 重新开始”清理当前会话

工程化内容：

- `install.ps1` 自动创建虚拟环境、安装依赖、准备词典
- `run.bat` 和 `run_app.bat` 作为 Windows 启动入口
- `tests/` 初步覆盖核心逻辑、词典、OCR、UI 粘贴流程
- `scripts/build_usage_guide.py` 用于生成使用教程文档
- `scripts/download_dictionary.py` 用于下载和构建离线词典数据

### 阶段2：生词本和词典能力增强

证据来源：`README.md`、`FAQ.md`、`dictionary.py`、`core.py`、`46a6b2f`。

主要功能：

- 离线词典优先支持 `data/dictionaries/cet_common.csv`
- 支持完整 ECDICT 数据：`ecdict.csv`、`ecdict.sqlite3`
- 支持词形还原数据：`lemma.en.txt`
- 本地查词时生成候选词形，例如复数、过去式、进行式
- 在线查词支持 Youdao、MyMemory、Free Dictionary API
- 选中文本可调用在线翻译
- 生词导出前可进一步归一化为原型词

重要修复：

- 2026-05-27 的 `46a6b2f` 修复了 `-ed`、`-ing` 后缀处理盲加 silent e 的问题
- 在线查词流程增加原词、词形还原、简单后缀兜底三层策略
- 网络失败或在线接口无结果时回退本地词典，避免界面卡死或查词失败后无兜底

### 阶段3：TXT 导入、文本清洗与题目拆分体验

证据来源：`core.py`、`ui.py`、`tests/test_ui_paste_article.py`、`project_sync_report.md`。

主要功能：

- 支持读取 UTF-8、UTF-8 BOM、GBK 和系统默认编码文本
- 标准化换行符
- 自动清洗 OCR/导入文本中的页码、题号、选项、Section/Passage 噪声行
- 支持重新识别文章/题目边界
- 支持在文章区和题目区之间移动选中文本
- 支持连续题号、`Questions ...`、`Question 1`、中文“对应题目”等拆分场景

历史说明：

- `project_sync_report.md` 记录同步时曾清理目标端额外文件 `tests/test_ui_txt_import.py`，但当前 `test_ui_paste_article.py` 中仍保留多项文本导入/拆分相关测试。

### 阶段4：OCR 功能接入

证据来源：`ocr_service.py`、`tests/test_ocr_service.py`、`requirements.txt`、`install.ps1`。

主要功能：

- 使用 PaddleOCR 作为 OCR 引擎
- 设置 `PADDLE_PDX_CACHE_HOME` 到项目内 `data/paddlex_cache`
- 默认使用 `PP-OCRv5_mobile_det` 和 `en_PP-OCRv5_mobile_rec`
- 对大图进行缩放，降低识别压力
- 从 PaddleOCR 返回结构中提取文本
- 根据版面列坐标优先选择主要阅读文本列
- 清洗 OCR 噪声后交给阅读流程使用

工程化内容：

- `install.ps1` 单独安装 `paddlepaddle==3.3.1`，并在官方源失败后回退 PyPI
- 测试覆盖大图缩放和主列选择逻辑

### 阶段5：听力模式进入主体项目

证据来源：`docs/listening_mode_report.md`、当前 `ui.py`、当前 `tests/test_ui_paste_article.py`。

主要功能：

- 顶部工具栏新增“阅读模式 / 听力模式”
- 阅读模式保留原文章区和题目区
- 听力模式使用独立的大题目区
- 听力模式粘贴文本时不执行阅读文章/题目自动拆分
- 听力模式复用高亮、字体颜色、清除格式、翻译选中、生词添加/删除、导出词表、一键清空
- 集成本地音频播放
- 支持导入 MP3 等音频文件
- 支持播放、暂停、进度条拖动、点击跳转
- 支持播放位置标记、跳转标记和删除标记

测试记录：

- `listening_mode_report.md` 记录当时运行 `python -m unittest discover -s tests -v`，结果为 `Ran 41 tests ... OK`

### 阶段6：模式切换与音频恢复修复

证据来源：`docs/mode_switch_fix_report.md`、`docs/mode_switch_audio_restore_report.md`、当前 `ui.py`、当前测试。

重要问题：

- 阅读模式和听力模式按钮状态与页面切换状态曾不同步
- 听力模式下“阅读模式”按钮曾被一个未布局但可接收鼠标事件的空 `QLabel` 覆盖

修复内容：

- 使用 `QActionGroup` 统一管理两个模式按钮
- 切换时同步当前模式值、当前页面、按钮选中状态、焦点、搜索和统计状态
- 隐藏搜索状态 label，并设置鼠标事件穿透
- 导入音频后保存绝对路径到 `runtime/session.json`
- 启动时恢复上次音频
- 原文件不存在时提示并清理失效路径
- 一键清空时清除音频路径和标记状态

测试记录：

- `mode_switch_fix_report.md` 记录 `Ran 45 tests ... OK`
- `mode_switch_audio_restore_report.md` 记录 `Ran 49 tests ... OK`

### 阶段7：Whisper 听力文章自动识别

证据来源：`docs/listening_article_auto_detect_report.md`、当前 `listening.py`、当前 `ui.py`、当前测试。

主要功能：

- 听力模式新增“自动识别文章”
- 使用 faster-whisper 离线转录音频
- 后台线程执行识别，不阻塞 UI
- 识别结果按 CET-4 听力材料结构生成“文章1 / 文章2 / ...”
- 点击文章目录项跳转到对应音频位置并播放
- 缓存同一音频识别结果到 `cache/listening/`
- 自动发现同目录同名试卷 PDF 和答案 PDF，并在缓存结构中保留
- 支持“重新识别”，忽略缓存并覆盖结果
- 支持“文章模式 / 原始转写模式”
- 自动切分失败时仍保留 Whisper 原始转写
- 支持导出听力文本到 `{audio_stem}_listening_articles.txt`
- 显示识别摘要：实际设备、模型、耗时、文章数量、Whisper segment 数

识别规则演进：

- 支持 `News Report 1`、`Conversation 1`、`Passage 1`
- 支持标题和正文同段的情况
- 支持 `Questions ... are based on the following ...` 提示句
- 支持 Section Directions 后首段材料入口
- 支持题目块后长间隔作为材料入口

真实验证记录：

- `25-12-1` 音频识别出 7 篇文章，首次识别 226.45 秒，缓存读取 0.03 秒
- `25-6-2` 修复后识别到 161 个 segment、8 个文章起点
- 报告记录测试结果为 `Ran 65 tests ... OK`

### 阶段8：GPU 支持与诊断

证据来源：`docs/whisper_gpu_support_report.md`、当前 `listening.py`、当前 `scripts/whisper_gpu_diagnostics.py`、当前 `requirements.txt`。

主要功能：

- 默认仍使用 CPU + int8，保证兼容
- 用户可选择 GPU 模式
- GPU 模式先检查 ctranslate2 CUDA 设备和 `float16` 支持
- GPU 初始化或转录失败时自动回退 CPU + int8
- UI 中显示实际设备、模型和精度
- `scripts/whisper_gpu_diagnostics.py` 检查 nvidia-smi、torch、faster-whisper、ctranslate2，并可用本地音频测试 CPU/GPU

真实验证记录：

- 报告记录设备为 NVIDIA GeForce RTX 4060 Laptop GPU
- faster-whisper `small + cuda/float16` 完成真实 GPU 推理
- CPU small/int8：235.56 秒
- GPU small/float16：36.36 秒
- 加速倍率约 6.48x
- 报告记录测试结果为 `Ran 58 tests ... OK`

### 阶段9：启动器、图标与打包体验

证据来源：当前工作区文件、`mode_switch_audio_restore_report.md`、[`docs/reports/CLEANUP_PLAN.md`](./docs/reports/CLEANUP_PLAN.md)。

主要内容：

- 新增 `run_app_hidden.vbs`，通过 `wscript.exe` 隐藏控制台启动
- 新增 `run_app_launcher.pyw`，记录启动日志并在缺少虚拟环境时调用安装脚本
- 新增 `run_app_logged.cmd`，把启动和安装输出写入 `runtime/launcher.log`
- 新增 `assets/app.ico`、`assets/app_icon_preview.png`、`assets/app_icon_crop_preview.png`

状态说明：

- 这些启动器和图标文件当前在 Git 状态中显示为未跟踪，需要后续确认是否纳入正式版本
- 图标预览图更像制作过程产物，适合归档或删除，`app.ico` 若被正式启动器/快捷方式使用则建议保留

## 当前状态

当前主体项目已经从单一阅读辅助工具扩展为“阅读 + 听力”的 CET-4 桌面训练助手。

已确认能力：

- 阅读文章粘贴和题目拆分
- 离线优先查词、在线查词兜底、句子翻译
- 生词本管理、导出和历史合并
- 会话保存与恢复
- OCR 文本识别与清洗
- 听力模式、音频播放、进度标记
- Whisper 自动转录与文章切分
- CPU/GPU 识别路径和自动回退
- 听力识别缓存和文本导出
- 单元测试覆盖 65 个测试函数

仍需工程化确认：

- 当前听力、GPU、启动器、图标相关文件部分未提交
- README 尚未覆盖听力、Whisper、GPU、启动器和项目结构的完整展示
- 历史报告散落在 `docs/` 和根目录
- 大型词典、OCR 缓存、运行缓存和本地系统缓存需要二阶段清理

## `cet4-abloop-player` 风险评估与删除建议

检查结果：

- 代码引用搜索未发现 `cet4-reader-assistant` 引用 `cet4-abloop-player`
- `cet4-reader-assistant` 的 Python 模块、脚本、测试没有导入该目录
- 当前唯一明显关联来自历史报告中使用 `cet4-abloop-player/materials/listening/25-6-1/*.mp3` 作为真实音频验证样本
- 该关联是验证材料路径，不是运行依赖或代码依赖

风险评估：

- 删除 `cet4-abloop-player` 不应影响 `cet4-reader-assistant` 的代码运行
- 风险主要在历史验证材料丢失、Git 历史中早期基线曾包含该目录、以及部分报告中的旧路径会失效
- 若保留报告原文，删除目录后报告里的旧验证路径仍只是历史记录，不影响应用

后续删除建议：

1. 第二阶段先确认听力测试所需样本是否已迁移到 `cet4-reader-assistant` 外部资料目录或测试 fixture。
2. 若没有运行依赖，可从 Git 展示范围中移除 `cet4-abloop-player`。
3. 删除前建议保留一个压缩归档到仓库外部备份位置。
4. README、CHANGELOG、项目介绍中不再强调该实验项目，只在内部历史整理中注明“已废弃，不作为主线”。

## 后续规划

短期：

- 确认并提交当前听力、Whisper、GPU、启动器相关文件
- 更新 README，使 GitHub 首页能准确展示当前主体项目
- 清理或归档历史报告和运行缓存
- 明确 `app.ico` 是否作为正式图标资源

中期：

- 增加听力模型选择：`small` / `medium` / `large-v3`
- 将 GPU 诊断能力做成只读页面或命令行工具说明
- 为 OCR、Whisper 缓存和离线词典建立下载/重建说明
- 增加截图、动图或演示流程图

长期：

- 把阅读、听力、词典、OCR、会话、导出进一步模块化
- 增加 CI 测试
- 建立版本号和 release notes
- 准备适合 GitHub 和简历展示的项目主页
