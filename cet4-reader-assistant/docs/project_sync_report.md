# 项目同步报告

同步时间：2026-05-27 21:51 Asia/Hong_Kong

## 同步来源与目标

- 来源最新版项目：`D:\reasonix_sandbox\cet4-reader-assistant`
- 正式项目：`D:\Codex Project\CET-4\cet4-reader-assistant`
- 同步前备份：`D:\Codex Project\backup\cet4-reader-assistant_before_sync_2026-05-27`

## 同步方式

使用 Robocopy 镜像同步最新版内容到正式项目，跳过相同文件以避免无意义覆盖。

执行结果：Robocopy 返回码 `3`，表示已复制文件并处理目标端额外文件，未报告失败。

## 已同步文件

更新文件：

- `FAQ.md`
- `QUICK_START.md`
- `README.md`
- `requirements.txt`
- `run.bat`
- `cet4_reader/core.py`
- `cet4_reader/dictionary.py`
- `cet4_reader/main.py`
- `cet4_reader/ocr_service.py`
- `cet4_reader/ui.py`
- `data/logs/app.log`
- `scripts/build_usage_guide.py`
- `tests/test_core.py`
- `vocab/history/2026-05-17_vocab.txt`
- `vocab/history/2026-05-18_vocab.txt`

新增文件：

- `run_app.bat`
- `runtime/session.json`
- `tests/test_ui_paste_article.py`
- `vocab/vocab.txt`
- `vocab/history/2026-05-22_vocab.txt`
- `vocab/history/2026-05-25_vocab.txt`
- `vocab/history/2026-05-27_21-34-31_vocab.txt`
- `vocab/history/2026-05-27_vocab.txt`

镜像清理的目标端额外文件：

- `新建 文本文档.txt`
- `cet4_reader/hotkey.py`
- `tests/test_ui_txt_import.py`

## 跳过目录与文件

同步时排除：

- `.git`
- `.venv`
- `node_modules`
- `__pycache__`
- `*pycache*`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `.cache`
- `cache`
- `tmp`
- `temp`
- `*.pyc`
- `*.pyo`

## Git 保留情况

- 未删除或覆盖 `.git`
- 未重新初始化 Git
- 正式项目子目录 `D:\Codex Project\CET-4\cet4-reader-assistant\.git` 不存在
- 当前 Git 仓库位于上层目录：`D:\Codex Project\CET-4\.git`，同步过程已保留

## Git 状态

同步后使用一次性 safe.directory 参数执行：

```powershell
git -c safe.directory='D:/Codex Project/CET-4' status --short --branch
```

Git 仓库可正常识别。当前仓库状态为未提交初始提交的 `master` 分支，并显示项目目录为未跟踪内容。

## 当前项目入口文件

- Python 模块入口：`cet4_reader/main.py`
- 启动命令入口：`run.bat`
- 直接应用启动脚本：`run_app.bat`

## 当前运行方式

推荐运行方式：

```powershell
cd "D:\Codex Project\CET-4\cet4-reader-assistant"
.\run.bat
```

`run.bat` 会在缺少 `.venv` 或 PyQt6 时调用 `install.ps1` 准备环境，然后执行：

```powershell
.\.venv\Scripts\pythonw.exe -m cet4_reader.main
```

也可以在环境已准备好后运行：

```powershell
.\run_app.bat
```
