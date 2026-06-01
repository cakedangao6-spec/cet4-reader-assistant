# Release Precheck Report

生成日期：2026-06-01  
目标主体项目：`cet4-reader-assistant`

## 检查范围

本次发布前检查覆盖：

- Git 工作区状态
- 本轮新增和修改文档
- `.gitignore` 覆盖情况
- 缓存、日志、模型缓存、运行状态文件
- README 国际化状态
- 文档引用和旧路径
- 截图引用
- 隐私和绝对路径风险

本次只修改文档与发布说明，不修改功能代码。

## 当前 Git 状态摘要

当前工作区不是干净状态，但发布范围已进一步收敛。

已修改文件：

```text
.gitignore
cet4-reader-assistant/QUICK_START.md
cet4-reader-assistant/README.md
cet4-reader-assistant/cet4_reader/ui.py
cet4-reader-assistant/requirements.txt
cet4-reader-assistant/tests/test_ui_paste_article.py
```

本轮新增文件：

```text
cet4-reader-assistant/README.zh-CN.md
RELEASE_PRECHECK_REPORT.md
```

前序阶段新增但尚未提交的文档：

```text
CHANGELOG.md
CLEANUP_PLAN.md
GITHUB_SHOWCASE_PLAN.md
PROJECT_DOCUMENTATION_REPORT.md
PROJECT_SHOWCASE_REVIEW.md
PROJECT_TIMELINE.md
README_IMPROVEMENT_PLAN.md
README_REFACTOR_REPORT.md
SCREENSHOT_PLAN.md
git_commit_report.md
```

前序阶段新增但尚未提交的主体项目文件：

```text
cet4-reader-assistant/cet4_reader/listening.py
cet4-reader-assistant/scripts/whisper_gpu_diagnostics.py
cet4-reader-assistant/docs/listening_article_auto_detect_report.md
cet4-reader-assistant/docs/listening_mode_report.md
cet4-reader-assistant/docs/mode_switch_audio_restore_report.md
cet4-reader-assistant/docs/mode_switch_fix_report.md
cet4-reader-assistant/docs/whisper_gpu_support_report.md
cet4-reader-assistant/run_app_hidden.vbs
cet4-reader-assistant/run_app_launcher.pyw
cet4-reader-assistant/run_app_logged.cmd
cet4-reader-assistant/assets/app.ico
cet4-reader-assistant/assets/app_icon_preview.png
cet4-reader-assistant/assets/app_icon_crop_preview.png
```

未跟踪且不建议提交的根目录图片：

```text
honglu.png
Screenshot_2026-01-29-00-49-59-050_com.xingin.xhs.jpg
```

最终处理：

- 已确认两张根目录图片没有被代码或 README 引用。
- 已加入根目录 `.gitignore`。
- 不会暂存或提交。

## 建议提交文件

如果本次发布目标是展示当前 README 中描述的完整能力，建议提交以下范围。

文档和发布准备：

```text
.gitignore
CHANGELOG.md
GITHUB_SHOWCASE_PLAN.md
PROJECT_DOCUMENTATION_REPORT.md
PROJECT_SHOWCASE_REVIEW.md
PROJECT_TIMELINE.md
README_IMPROVEMENT_PLAN.md
README_REFACTOR_REPORT.md
SCREENSHOT_PLAN.md
RELEASE_PRECHECK_REPORT.md
README.md
cet4-reader-assistant/README.md
cet4-reader-assistant/README.zh-CN.md
cet4-reader-assistant/QUICK_START.md
```

当前 README 所依赖的主体项目能力：

```text
cet4-reader-assistant/requirements.txt
cet4-reader-assistant/cet4_reader/ui.py
cet4-reader-assistant/cet4_reader/listening.py
cet4-reader-assistant/tests/test_ui_paste_article.py
cet4-reader-assistant/scripts/whisper_gpu_diagnostics.py
cet4-reader-assistant/docs/listening_article_auto_detect_report.md
cet4-reader-assistant/docs/listening_mode_report.md
cet4-reader-assistant/docs/mode_switch_audio_restore_report.md
cet4-reader-assistant/docs/mode_switch_fix_report.md
cet4-reader-assistant/docs/whisper_gpu_support_report.md
```

可提交但建议确认用途的资源：

```text
cet4-reader-assistant/assets/app.ico
cet4-reader-assistant/run_app_hidden.vbs
cet4-reader-assistant/run_app_launcher.pyw
cet4-reader-assistant/run_app_logged.cmd
```

图标预览图更像制作过程产物，公开发布前不建议提交，已加入 `.gitignore`：

```text
cet4-reader-assistant/assets/app_icon_preview.png
cet4-reader-assistant/assets/app_icon_crop_preview.png
```

## 不建议提交文件

明确不建议提交：

```text
.deepseek/
honglu.png
Screenshot_2026-01-29-00-49-59-050_com.xingin.xhs.jpg
cet4-reader-assistant/.venv/
cet4-reader-assistant/cache/
cet4-reader-assistant/runtime/
cet4-reader-assistant/vocab/
cet4-reader-assistant/data/home/
cet4-reader-assistant/data/logs/
cet4-reader-assistant/data/paddlex_cache/
cet4-reader-assistant/qa/
cet4-reader-assistant/**/__pycache__/
cet4-reader-assistant/data/dictionaries/ecdict.csv
cet4-reader-assistant/data/dictionaries/ecdict.mini.csv
cet4-reader-assistant/data/dictionaries/ecdict.sqlite3
cet4-reader-assistant/data/dictionaries/lemma.en.txt
```

这些文件属于本地环境、运行状态、缓存、日志、词典大文件、OCR/模型缓存或个人图片，不适合进入公开仓库。

## `.gitignore` 检查结果

当前忽略规则覆盖合理：

- `.venv/`：由 `cet4-reader-assistant/.gitignore` 覆盖。
- 大词典文件：由 `cet4-reader-assistant/.gitignore` 覆盖。
- `vocab/`：由 `cet4-reader-assistant/.gitignore` 覆盖。
- `runtime/session.json`：由根目录 `.gitignore` 覆盖。
- `cache/listening/`：本轮根目录 `.gitignore` 已补充覆盖。
- `data/paddlex_cache/`：由根目录 `.gitignore` 覆盖。
- `__pycache__/`、日志、临时文件、测试缓存：已有覆盖。

仍需注意：

- 根目录个人图片 `honglu.png` 和 `Screenshot_2026-01-29-00-49-59-050_com.xingin.xhs.jpg` 当前未被忽略，只是未跟踪；发布前不要 `git add .`。
- 如果以后经常放个人临时图片，可考虑新增更具体的忽略目录，而不是全局忽略所有图片，以免影响正式截图资产。

## GitHub 展示风险

方案评估与处理：

- 方案 A：将 `cet4-reader-assistant` 作为独立 GitHub 仓库发布。优点是展示最干净、历史和目录最聚焦；代价是需要新建或迁移仓库。
- 方案 B：在当前仓库中移除 `cet4-abloop-player` 的 Git 跟踪，保留本地目录并加入 `.gitignore`。优点是当前仓库改造成本低；代价是历史提交中仍可追溯到旧实验目录。

本次执行方案 B：

- 已用 `git rm -r --cached -- cet4-abloop-player` 移除 Git 跟踪。
- 本地文件仍保留。
- 已在 `.gitignore` 中忽略 `cet4-abloop-player/`。

如果后续要做最干净的长期公开展示，方案 A 仍是更优选择。

剩余风险：

1. 当前工作区包含尚未提交的功能改动。
   - `ui.py`、`requirements.txt`、`tests/test_ui_paste_article.py` 和新增 `listening.py` 与 README 中的听力/Whisper/GPU 功能有关。
   - 已运行单元测试，65 个测试全部通过。

2. 缺少应用界面截图。
   - `cet4-reader-assistant/assets/screenshots/` 中两张图片是纸质试卷照片，不适合作为 GitHub README 主展示图。
   - README 当前没有引用它们，风险已规避。

3. 应用界面截图仍需后续补充。
   - 当前已新增根目录 `README.md` 作为 GitHub 入口，并指向 `cet4-reader-assistant`。
   - 主体功能说明仍以 `cet4-reader-assistant/README.md` 为准。

## 隐私检查结果

已扫描 Markdown、Python、PowerShell、bat/cmd/vbs 等文本文件，排除虚拟环境、缓存、runtime 和 OCR 缓存目录。

结果：

- 未发现 `reasonix_sandbox` 残留。
- 未发现明显 Windows 绝对路径残留。
- 未发现 `token`、`password`、`api_key`、`secret` 等明显凭据字段。
- `QUICK_START.md` 中旧的 `D:\reasonix_sandbox\...` 路径已改为相对路径。

注意：

- 历史报告中包含真实测试环境描述，例如 RTX 4060、耗时数据和 CUDA/cuBLAS 问题。这些属于技术验证信息，不是凭据，但公开前应确认可以展示。
- 根目录个人图片不建议提交，因为图片内容可能包含与项目无关的个人信息或版权风险。

## README 状态

英文 README 已完成：

```text
cet4-reader-assistant/README.md
```

当前状态：

- 已作为 GitHub 展示主版。
- 顶部包含中文切换链接。
- 面向国际 GitHub 用户说明项目定位、功能、安装、使用、测试、开发历程和限制。
- 未引用纸质试卷截图作为主展示图。
- 未虚构 release、打包发布、跨平台支持或不存在的功能。

## 中文 README 状态

中文 README 已新增：

```text
cet4-reader-assistant/README.zh-CN.md
```

当前状态：

- 顶部包含英文切换链接。
- 保留前一阶段中文 README 的主体内容。
- 面向国内用户说明 CET-4 阅读、听力、OCR、Whisper、GPU 回退和 Windows 使用方式。
- 已更新项目结构，包含英文 README 与中文 README。

## 文档引用检查

已修正：

- `cet4-reader-assistant/README.md` 中 `PROJECT_TIMELINE.md` 和 `CHANGELOG.md` 引用改为可点击相对链接。
- `cet4-reader-assistant/README.zh-CN.md` 同步修正。
- `cet4-reader-assistant/QUICK_START.md` 旧绝对路径改为相对路径。

仍需注意：

- 根目录历史报告较多，适合后续归档到 `docs/history/` 或 `docs/reports/`。
- `CLEANUP_PLAN.md` 可以作为内部整理材料，是否公开提交需要按展示目标判断。

## 截图状态

当前截图目录：

```text
cet4-reader-assistant/assets/screenshots/
├─ 1778995092752.jpg
└─ 1778995092772.jpg
```

判断：

- 两张图片是纸质 CET-4 阅读材料照片。
- 可作为 OCR 输入素材。
- 不应作为 README 主展示图。
- 英文 README 和中文 README 均未直接引用这两张图片。

建议后续补充应用界面截图：

```text
cet4-reader-assistant/assets/screenshots/reading-mode-overview.png
cet4-reader-assistant/assets/screenshots/vocabulary-lookup.png
cet4-reader-assistant/assets/screenshots/listening-mode-overview.png
cet4-reader-assistant/assets/screenshots/whisper-analysis-result.png
```

## 发布准备度评估

当前不建议直接 `git add . && git commit && git push`，但可以进行选择性暂存、提交，并在配置远程仓库后准备推送。

原因：

- 根目录个人图片已忽略，但仍保留在本地。
- `cet4-abloop-player` 已从 Git 跟踪中移除并忽略，但本地仍保留。
- 前序功能改动已通过本轮单元测试确认。
- 应用界面截图仍需后续补充。

条件通过后可以发布：

1. 只选择性暂存建议提交文件。
2. 不提交根目录个人图片。
3. 已明确处理 `cet4-abloop-player`：当前仓库移除 Git 跟踪，本地保留并忽略。
4. 已运行测试：

```powershell
cd cet4-reader-assistant
.\run_tests.ps1
```

实际执行命令：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

结果：

```text
Ran 65 tests in 3.488s
OK
```

5. 确认启动器和图标资源是否作为正式发布内容。

## 建议 Commit Message

```text
docs: prepare CET-4 Reader Assistant for GitHub showcase
```

如果同时提交听力、Whisper 和 GPU 功能代码，建议使用更准确的提交信息：

```text
feat: add listening transcription and GitHub-ready documentation
```

## 建议 GitHub Description

```text
Local-first CET-4 reading and listening assistant with PyQt6, PaddleOCR, faster-whisper, vocabulary export, and optional GPU fallback.
```

## 建议 Topics

```text
python
pyqt6
cet4
english-learning
ocr
paddleocr
whisper
faster-whisper
sqlite
desktop-app
listening-practice
vocabulary
windows
```

## 最终结论

README 国际化、截图引用规避、旧路径清理、个人图片忽略、废弃目录 Git 跟踪移除和测试验证已完成。

当前适合进行选择性暂存和提交；不适合使用 `git add .`，也不能直接推送，因为当前仓库尚未配置 GitHub remote。
