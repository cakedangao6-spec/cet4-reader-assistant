# CET-4 Cleanup Plan

生成日期：2026-06-01  
阶段：第一阶段，只分析、不清理  
范围：`D:\Codex Project\CET-4`

本报告仅给出整理建议。未删除、移动、重命名任何文件，也未修改项目代码。

## 1. 总览

当前工作区规模：

| 项目 | 数量 / 体积 |
| --- | ---: |
| 全部文件（含 `.git`） | 45,985 个 |
| 总体积（含 `.git`） | 4,278.48 MB |
| 工作区文件（不含 `.git`） | 38,508 个 |
| 工作区体积（不含 `.git`） | 3,907.13 MB |
| Git loose objects | 7,447 个 / 275.56 MB |
| Git LFS objects | 3 个 / 95.75 MB |
| Git 已跟踪文件 | 81 个 |
| Git 未跟踪但未忽略文件 | 16 个 / 3.49 MB |
| Git 已忽略未跟踪文件 | 38,411 个 / 3,897.53 MB |

主要体积来源：

| 路径 | 文件数 | 体积 | 判断 |
| --- | ---: | ---: | --- |
| `cet4-reader-assistant/.venv/` | 31,343 | 3,147.95 MB | 可重建虚拟环境 |
| `cet4-abloop-player/.venv/` | 6,920 | 347.05 MB | 可重建虚拟环境 |
| `.git/objects/` | 7,447 | 275.56 MB | Git 历史对象，需谨慎 |
| `cet4-reader-assistant/data/` | 84 | 252.96 MB | 词典、OCR 模型缓存、本地系统缓存 |
| `cet4-abloop-player/runtime/` | 6 | 140.92 MB | faster-whisper 模型缓存 |
| `.git/lfs/` | 3 | 95.75 MB | LFS 本地对象，需确认是否仍引用 |

## 2. 建议删除

这些项目属于可重建缓存、临时运行产物或明显不应长期保留在项目工作区的内容。建议在第二阶段清理前先关闭应用和测试进程。

| 路径 / 类型 | 文件数 | 体积 | 理由 |
| --- | ---: | ---: | --- |
| `cet4-reader-assistant/.venv/` | 31,343 | 3,147.95 MB | Python 虚拟环境，可通过 `requirements.txt` 重建；不应进仓库 |
| `cet4-abloop-player/.venv/` | 6,920 | 347.05 MB | Python 虚拟环境，可重建；不应进仓库 |
| `cet4-reader-assistant/cet4_reader/__pycache__/` | 13 | 0.26 MB | Python 字节码缓存 |
| `cet4-reader-assistant/tests/__pycache__/` | 9 | 0.17 MB | 测试字节码缓存，含 Python 3.12/3.14 混合缓存 |
| `cet4-reader-assistant/scripts/__pycache__/` | 1 | 0.02 MB | 脚本字节码缓存 |
| `cet4-abloop-player/scripts/__pycache__/` | 3 | 0.03 MB | 脚本字节码缓存 |
| `cet4-reader-assistant/data/home/` | 35 | 6.09 MB | Windows/D3D/Explorer 本地缓存，不属于项目数据 |
| `cet4-reader-assistant/qa/manual-render/` | 6 | 1.09 MB | 文档渲染验收输出，可按需重新生成 |
| `cet4-abloop-player/archive/ABLoopPlayer.zip` | 1 | 0.20 MB | 历史压缩包，已被 `.gitignore` 规则覆盖 |
| `cet4-abloop-player/archive/server.log`、`cet4-abloop-player/server.log` | 2 | <0.01 MB | 本地服务日志 |
| `cet4-reader-assistant/data/logs/app.log`、`cet4-reader-assistant/runtime/launcher.log` | 2 | 0.24 MB | 本地运行日志 |

预计可减少：约 38,335 个文件，约 3,502.0 MB。

## 3. 建议归档

这些文件可能对复现、离线运行或历史说明有价值，但不适合长期散落在主工作区。建议移动到统一归档目录或外部备份位置，第二阶段执行前需确认归档策略。

| 路径 / 类型 | 文件数 | 体积 | 理由 |
| --- | ---: | ---: | --- |
| `cet4-reader-assistant/data/paddlex_cache/` | 42 | 96.62 MB | OCR 模型缓存，可重建；若需要离线 OCR 可归档保留 |
| `cet4-abloop-player/runtime/models/` | 6 | 140.92 MB | faster-whisper `base.en` 模型缓存；时间轴已生成，但重新生成需要它 |
| `cet4-reader-assistant/data/dictionaries/ecdict.csv` | 1 | 62.88 MB | ECDICT 源 CSV；当前代码优先使用 `ecdict.sqlite3`，CSV 可作为源数据归档 |
| `cet4-reader-assistant/data/dictionaries/lemma.en.txt` | 1 | 2.21 MB | 词形还原源数据；可随 ECDICT 源数据归档 |
| `cet4-reader-assistant/data/dictionaries/ecdict.sqlite3` | 1 | 83.08 MB | 完整离线索引库，运行时有价值；若发布轻量版可外置 |
| `cet4-abloop-player/materials/listening/25-6-1/` | 3 | 8.58 MB | 听力原始材料，适合作为资料包而非代码核心 |
| `cet4-reader-assistant/docs/*_report.md` | 5 | 0.02 MB | 多个阶段性修复/功能报告，可合并后归档 |
| `git_baseline_plan.md`、`git_commit_report.md` | 2 | 0.01 MB | 历史 Git 操作说明，建议归档到 docs/history 或外部记录 |

预计可从主工作区减少：约 61 个文件，约 394.3 MB。  
注意：其中 `ecdict.sqlite3` 和 faster-whisper 模型会影响离线能力，归档不等于删除。

## 4. 建议保留

这些内容是当前功能、说明或测试的核心组成部分。

| 路径 / 类型 | 理由 |
| --- | --- |
| `cet4-reader-assistant/cet4_reader/*.py` | 阅读助手核心代码；其中 `listening.py` 目前未跟踪，但看起来是新增听力功能代码 |
| `cet4-reader-assistant/tests/*.py` | 当前测试集合，建议保留源码测试文件 |
| `cet4-reader-assistant/scripts/*.py` | 文档生成、词典下载、GPU 诊断脚本；源码应保留 |
| `cet4-reader-assistant/data/dictionaries/cet_common.csv` | 已跟踪、小型常用词典，代码和测试依赖路径明确 |
| `cet4-reader-assistant/docs/usage/*.docx` | 用户使用教程源文档 |
| `cet4-abloop-player/data/*.js`、`*.json` | 播放器题目和时间轴数据 |
| `cet4-abloop-player/jquery-ui/` | 前端页面直接依赖的静态库 |
| `cet4-abloop-player/svg/`、`png/favicon.ico` | 前端图标资源 |
| `.gitignore` 和子项目 `.gitignore` | 已覆盖多数缓存、模型和运行产物，应继续保留并维护 |

## 5. 不确定，需人工确认

这些项目可能是近期开发成果、个人素材或仓库策略问题，第一阶段不建议处理。

| 路径 / 类型 | 体积 | 需要确认的问题 |
| --- | ---: | --- |
| `honglu.png` | 1.70 MB | 根目录未跟踪图片，未发现代码引用；需确认是否为应用素材 |
| `Screenshot_2026-01-29-00-49-59-050_com.xingin.xhs.jpg` | 0.40 MB | 根目录未跟踪截图，未发现代码引用；需确认是否为参考图 |
| `cet4-reader-assistant/assets/app.ico` | 0.17 MB | 未跟踪图标，可能是新启动器资源；需确认是否应加入版本控制 |
| `cet4-reader-assistant/assets/app_icon_preview.png` | 0.19 MB | 图标预览图，通常可删除或归档 |
| `cet4-reader-assistant/assets/app_icon_crop_preview.png` | 0.98 MB | 图标裁剪预览图，通常可删除或归档 |
| `cet4-reader-assistant/assets/screenshots/*.jpg` | 3.10 MB | 已跟踪截图；需确认 README/文档是否仍需要，否则可改为外部文档资产 |
| `cet4-reader-assistant/run_app_hidden.vbs`、`run_app_launcher.pyw`、`run_app_logged.cmd` | <0.01 MB | 未跟踪启动器脚本，可能是近期功能；需确认是否纳入仓库 |
| `cet4-reader-assistant/runtime/session.json` | 0.04 MB | 运行状态文件，已被忽略；删除会清空本地会话 |
| `cet4-reader-assistant/cache/listening/` | 0.08 MB | 听力识别缓存，体积小；删除会导致重新转录 |
| `cet4-reader-assistant/vocab/history/` | <0.01 MB | 用户词表历史，体积小但可能是个人数据 |
| `.git/lfs/objects/` | 95.75 MB | 当前 `git lfs ls-files -s` 未列出文件；可能是历史/孤立 LFS 对象，需确认后再 prune |
| `.git/objects/` | 275.56 MB | Git loose objects 较大；需确认历史中是否提交过大模型/缓存，再决定是否 GC 或重写历史 |

## 6. scripts / tests / docs / reports 检查

### scripts

`scripts` 源码本身体积很小，应保留：

- `cet4-reader-assistant/scripts/build_usage_guide.py`
- `cet4-reader-assistant/scripts/download_dictionary.py`
- `cet4-reader-assistant/scripts/whisper_gpu_diagnostics.py`
- `cet4-abloop-player/scripts/build_usage_doc.py`
- `cet4-abloop-player/scripts/generate_timeline.py`
- `cet4-abloop-player/scripts/local_server.py`

可整理内容：

- 删除两个项目下的 `scripts/__pycache__/`。
- `whisper_gpu_diagnostics.py` 目前未跟踪，需确认是否作为正式诊断工具纳入仓库。

### tests

测试源码建议保留。可整理内容：

- 删除 `cet4-reader-assistant/tests/__pycache__/`。
- 当前存在 Python 3.12 和 3.14 的缓存混合，说明本地曾用多个解释器运行测试；这类缓存不应长期保留。
- `test_ui_txt_import.cpython-312.pyc` 没有对应源码文件，属于历史遗留缓存，建议删除。

### docs

文档源文件建议保留，但报告类文档可归档：

- `docs/usage/*.docx`：保留。
- `docs/project_sync_report.md`：可保留或归档到历史记录。
- `docs/listening_*_report.md`、`docs/mode_switch_*_report.md`、`docs/whisper_gpu_support_report.md`：建议合并为阶段性 changelog 或归档。

### reports

未发现独立 `reports/` 目录。当前报告散落在：

- 仓库根目录：`git_baseline_plan.md`、`git_commit_report.md`
- `cet4-reader-assistant/docs/`：多个 `*_report.md`

建议后续统一到 `docs/history/`、`docs/reports/` 或外部项目记录。

## 7. 未引用资源、旧模型、旧缓存、旧导出

初步未发现明确的重复文件组（基于 100 KB 以上文件的大小+SHA256 粗查）。疑似未引用或可重建资源如下：

| 类型 | 路径 | 建议 |
| --- | --- | --- |
| 根目录图片 | `honglu.png`、`Screenshot_2026-01-29-00-49-59-050_com.xingin.xhs.jpg` | 未发现引用，人工确认后删除或归档 |
| 图标预览 | `assets/app_icon_preview.png`、`assets/app_icon_crop_preview.png` | 若只是制作过程预览，建议删除或归档 |
| OCR 模型缓存 | `data/paddlex_cache/` | 可重建，离线需求确认后删除或归档 |
| Whisper 模型缓存 | `cet4-abloop-player/runtime/models/` | 已生成时间轴后通常不需随项目常驻，但重新生成时间轴需要 |
| LibreOffice profile | `runtime/libreoffice-profiles/` | 文档生成临时配置，可删除 |
| 手动渲染产物 | `qa/manual-render/` | 可重新生成，建议删除 |
| 听力调试缓存 | `cache/listening/25-6-2-debug*` | 体积很小，但属于调试缓存；可删除 |
| Windows 图标/缩略图缓存 | `data/home/AppData/Local/Microsoft/Windows/Explorer/` | 明显本机缓存，建议删除 |

## 8. Git 大文件与仓库健康

当前 `HEAD` 中最大的已跟踪文件：

| 文件 | 体积 | 判断 |
| --- | ---: | --- |
| `cet4-reader-assistant/data/dictionaries/cet_common.csv` | 1.94 MB | 可接受，核心词典 |
| `cet4-reader-assistant/assets/screenshots/1778995092772.jpg` | 1.67 MB | 需确认是否仍有文档引用 |
| `cet4-reader-assistant/assets/screenshots/1778995092752.jpg` | 1.43 MB | 需确认是否仍有文档引用 |
| `cet4-abloop-player/jquery-ui/jquery-ui.min.js` | 0.24 MB | 前端依赖，可接受 |

当前已跟踪文件中没有特别大的单文件（例如 10 MB 以上）。  
但 `.git/objects/` 达到 275.56 MB，且 `.git/lfs/objects/` 有 95.75 MB 本地对象，说明历史中可能曾出现过大文件或 LFS 对象。建议第二阶段只做只读调查：

- 使用 `git rev-list --objects --all` 排查历史大对象。
- 确认 `.git/lfs/objects/` 是否仍被任何引用使用。
- 如果确认是孤立本地对象，可考虑 `git lfs prune`。
- 如果历史中曾提交模型/虚拟环境，需谨慎评估是否重写历史。

## 9. 预估收益

保守清理（删除虚拟环境、字节码、本地系统缓存、日志、QA 渲染产物）：

- 预计减少文件：约 38,335 个
- 预计减少空间：约 3,502 MB
- 功能影响：需要重新创建虚拟环境；运行日志和本机会话/渲染产物消失

中等清理（保守清理 + 归档可重建模型/词典源/听力材料）：

- 预计减少文件：约 38,396 个
- 预计减少空间：约 3,896 MB
- 功能影响：离线 OCR、重新生成听力时间轴、完整离线词典重建可能需要重新下载或从归档恢复

Git 本地维护（在确认安全后清理 LFS 孤立对象和 Git loose objects）：

- 潜在额外释放：最高约 371 MB
- 功能影响：通常不影响工作树，但涉及 Git 历史和本地对象，需单独确认

## 10. 建议第二阶段顺序

1. 先确认未跟踪开发文件：`listening.py`、启动器脚本、图标文件、GPU 诊断脚本、近期报告。
2. 删除两个 `.venv/` 并按需重建，确认应用和测试可运行。
3. 删除 `__pycache__/`、日志、`data/home/`、`qa/manual-render/`。
4. 决定 OCR/Whisper 模型缓存是否改为外部下载或外部归档。
5. 统一整理报告文件到一个历史目录。
6. 最后单独检查 Git 历史大对象和 LFS 对象。

