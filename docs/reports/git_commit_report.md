# Git 提交报告

提交时间：2026-05-27 Asia/Hong_Kong

## 提交信息

```text
Initial CET-4 project baseline
```

## 提交 Hash

```text
c27822b7f2890a11fc11c3fac17f6101bea7c3a9
```

## 纳入的主要目录和文件

- `.gitignore`
- `git_baseline_plan.md`
- `cet4-reader-assistant/`
  - 应用源码：`cet4_reader/`
  - 文档：`README.md`、`QUICK_START.md`、`FAQ.md`、`docs/`
  - 启动和安装脚本：`run.bat`、`run_app.bat`、`run_tests.ps1`、`install.ps1`
  - 测试：`tests/`
  - 项目脚本：`scripts/`
  - 小型内置词典：`data/dictionaries/cet_common.csv`
  - 静态资源：`assets/`
- `cet4-abloop-player/`
  - 页面入口：`ABLoopPlayer.html`、`cet4.html`
  - 前端源码：`css/`、`js/`
  - 文档：`README.md`、`README_CET4.md`、`docs/`
  - 项目脚本：`scripts/`
  - 静态素材：`png/`、`svg/`、`tex/`
  - 第三方前端依赖源码：`jquery-ui/`
  - CI 配置：`.github/`、`.gitlab-ci.yml`
  - 许可证：`LICENSE`

## 排除的主要目录和文件

- `.deepseek/`
- `.venv/`
- `__pycache__/`
- `node_modules/`
- `logs/`、`*.log`
- `.cache/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`
- `runtime/cache/`
- `runtime/models/`
- `runtime/libreoffice-profiles/`
- `runtime/session.json`
- `vocab/`
- 大型词典和词形数据：`ecdict.csv`、`ecdict.mini.csv`、`ecdict.sqlite3`、`lemma.en.txt`
- 模型缓存：`data/paddlex_cache/`
- 本机系统缓存：`data/home/`、`*.dxcache`、`iconcache_*.db`、`thumbcache_*.db`
- 临时导出和临时文件：`exports/tmp/`、`data/exports/tmp/`、`*.tmp`、`*.temp`
- 打包和渲染产物：`archive/*.zip`、`*.zip`、`qa/manual-render/`、`qa/docx-render/`

## 提交后工作区状态

提交后立即执行：

```powershell
git -c safe.directory='D:/Codex Project/CET-4' status --short --branch
```

结果：

```text
## master
```

结论：提交后工作区干净。

说明：本报告文件是在提交完成并获取 hash 后生成的记录文件，未包含在上述提交中。
