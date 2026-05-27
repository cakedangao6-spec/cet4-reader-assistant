# Git 基线检查计划

检查时间：2026-05-27 Asia/Hong_Kong

## 当前仓库状态

项目根目录：`D:\Codex Project\CET-4`

执行命令：

```powershell
git -c safe.directory='D:/Codex Project/CET-4' status --short --branch
```

检查结果：

```text
## No commits yet on master
?? .deepseek/
?? cet4-abloop-player/
?? cet4-reader-assistant/
```

补充根级 `.gitignore` 和本计划文件后，当前状态为：

```text
## No commits yet on master
?? .gitignore
?? cet4-abloop-player/
?? cet4-reader-assistant/
?? git_baseline_plan.md
```

忽略规则验证结果：

```text
!! .deepseek/
!! cet4-reader-assistant/.venv/
!! cet4-reader-assistant/cet4_reader/__pycache__/
!! cet4-reader-assistant/data/logs/
!! cet4-reader-assistant/vocab/
```

抽查 `git check-ignore -v` 已确认 `.deepseek/`、两个子项目的 `.venv/`、`data/logs/app.log`、`server.log` 都命中预期忽略规则。

说明：

- 根仓库存在于 `D:\Codex Project\CET-4\.git`。
- 根仓库还没有初始提交。
- 根目录原本没有 `.gitignore`，已补充根级 `.gitignore` 作为基线忽略规则。
- `cet4-abloop-player` 内部存在独立 `.git`，属于嵌套 Git 仓库，需要在正式纳入根仓库前决定管理方式。
- 未执行 commit。
- 未删除任何项目文件。

## .gitignore 基线

根级 `.gitignore` 已覆盖以下类别：

- `.venv/` 和任意层级的 `.venv/`
- `__pycache__/` 和任意层级的 `__pycache__/`
- `*.pyc`、`*.pyo`、`*.pyd`
- `node_modules/`
- `.deepseek/`
- `runtime/cache/`
- `logs/` 和 `*.log`
- 临时导出目录与临时文件：`exports/tmp/`、`tmp/`、`temp/`、`*.tmp`、`*.temp`、`*.bak`、`*.backup`
- 数据导出临时文件：`data/exports/tmp/`、`data/exports/*.tmp`、`data/exports/*.temp`
- 运行状态和模型缓存：`runtime/session.json`、`runtime/libreoffice-profiles/`、`runtime/models/`、`data/paddlex_cache/`
- 本机系统缓存：`data/home/`、`*.dxcache`、`iconcache_*.db`、`thumbcache_*.db`
- 打包/渲染产物：`archive/*.zip`、`*.zip`、`qa/manual-render/`、`qa/docx-render/`
- 工具缓存：`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.cache/`
- 系统和编辑器缓存文件：`.DS_Store`、`Thumbs.db`、`Desktop.ini`、`ehthumbs.db`、`*.swp`、`*.swo`、`*~`

子项目已有 `.gitignore`：

- `cet4-reader-assistant/.gitignore`
- `cet4-abloop-player/.gitignore`

这些子项目规则可以继续保留，用于表达项目内更具体的忽略策略。

## 建议纳入 Git 的文件

根仓库建议纳入：

- `.gitignore`
- `git_baseline_plan.md`

`cet4-reader-assistant` 建议纳入：

- 项目说明：`README.md`、`QUICK_START.md`、`FAQ.md`
- 启动和安装脚本：`run.bat`、`run_app.bat`、`run_tests.ps1`、`install.ps1`
- 依赖清单：`requirements.txt`
- 应用源码：`cet4_reader/`
- 测试：`tests/`
- 项目脚本：`scripts/`
- 文档：`docs/`
- 静态资源：`assets/`
- 小型、必要、可复现的数据样本或内置词典：例如 `data/dictionaries/cet_common.csv`

`cet4-abloop-player` 建议纳入。已决定不再作为独立仓库或子模块维护，而是作为 CET-4 根仓库下的普通项目目录管理：

- 页面入口：`ABLoopPlayer.html`、`cet4.html`
- 前端源码：`css/`、`js/`
- 静态素材：`png/`、`svg/`
- 项目文档：`README.md`、`README_CET4.md`、`docs/`
- 自动化或辅助脚本：`scripts/`
- CI 配置：`.gitlab-ci.yml`、`.github/`
- 许可证：`LICENSE`

## 建议忽略的文件和目录

根仓库建议忽略：

- `.deepseek/`
- 任意 `.venv/`
- 任意 `__pycache__/`
- 任意 `node_modules/`
- 任意工具缓存目录，例如 `.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.cache/`
- 任意运行缓存：`runtime/cache/`
- 日志目录和日志文件：`logs/`、`*.log`
- 临时导出和临时文件：`exports/tmp/`、`tmp/`、`temp/`、`*.tmp`、`*.temp`
- 系统缓存文件：`.DS_Store`、`Thumbs.db`、`Desktop.ini`、`ehthumbs.db`

`cet4-reader-assistant` 建议继续忽略：

- `.venv/`
- `data/dictionaries/ecdict.csv`
- `data/dictionaries/ecdict.mini.csv`
- `data/dictionaries/ecdict.sqlite3`
- `data/dictionaries/lemma.en.txt`
- `data/exports/`
- `data/history/`
- `runtime/cache/`
- `data/logs/`
- 运行中生成的会话、缓存、日志和导出文件

`cet4-abloop-player` 建议继续忽略：

- `.venv/`
- `server.log`
- `server.err`
- `runtime/models/`
- `qa/docx-render/`
- `archive/*.zip`
- 运行缓存、模型缓存、临时渲染输出

## 需要决策的事项

1. `cet4-abloop-player` 内部 Git 仓库已处理。
   - 决策：不作为独立仓库或子模块维护。
   - 处理：已备份内部 `.git` 到 `D:\Codex Project\backup\cet4-abloop-player_inner_git_2026-05-27`。
   - 处理：已从 `D:\Codex Project\CET-4\cet4-abloop-player\.git` 移除内部 `.git`。
   - 验证：在 `cet4-abloop-player` 内执行 `git -c safe.directory='D:/Codex Project/CET-4' rev-parse --show-toplevel`，结果为 `D:/Codex Project/CET-4`。
   - 验证：`git status --short --untracked-files=all cet4-abloop-player` 已将 HTML、CSS、JS、文档、素材和脚本显示为根仓库下的普通未跟踪文件。

2. `cet4-reader-assistant/runtime/session.json` 是运行状态文件。
   - 如果希望项目启动时带有固定默认会话，可以纳入 Git。
   - 如果它只是本机运行状态，建议加入子项目 `.gitignore`。

3. `cet4-reader-assistant/vocab/` 当前被子项目 `.gitignore` 忽略。
   - 如果词表是用户数据，应继续忽略。
   - 如果需要提供示例词表，应移动到示例数据目录并纳入 Git。

4. 大型词典和模型文件建议不纳入 Git。
   - 推荐保留下载脚本或安装脚本来生成这些文件。

## 后续建议操作

建议在正式提交前执行：

```powershell
git -c safe.directory='D:/Codex Project/CET-4' status --short --ignored
```

确认忽略规则生效后，再手动选择要纳入的文件执行 `git add`。本次检查不执行提交。

## 本次处理记录

处理时间：2026-05-27 Asia/Hong_Kong

已执行：

- 检查 `D:\Codex Project\CET-4\cet4-abloop-player\.git` 存在。
- 备份内部 `.git` 到 `D:\Codex Project\backup\cet4-abloop-player_inner_git_2026-05-27`。
- 仅移除内部 Git 元数据目录 `D:\Codex Project\CET-4\cet4-abloop-player\.git`。
- 未删除源码、文档、素材或脚本。
- 未修改业务逻辑。
- 未执行 commit。
- 首次提交前补充忽略规则，排除本机系统缓存、OCR 模型缓存、LibreOffice profile、运行会话、QA 渲染产物和 ZIP 打包产物，避免进入基线提交。

处理后根仓库状态：

```text
## No commits yet on master
?? .gitignore
?? cet4-abloop-player/
?? cet4-reader-assistant/
?? git_baseline_plan.md
```

确认结果：

- `cet4-abloop-player\.git` 已不存在。
- 备份目录中存在 `HEAD`、`objects/`、`refs/` 等 Git 元数据。
- `cet4-abloop-player` 现在由根仓库 `D:\Codex Project\CET-4` 识别为普通项目目录。
