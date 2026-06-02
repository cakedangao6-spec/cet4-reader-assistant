# CET-4 阅读助手运行时图标修复报告

## 检查范围

- PyQt 主入口：`cet4_reader/main.py`
- PyQt 主窗口：`cet4_reader/ui.py`
- 启动脚本：`run.bat`、`run_app.bat`、`run_app_hidden.vbs`、`run_app_launcher.pyw`、`run_app_logged.cmd`
- 图标资源：`assets/app.ico`
- PyInstaller spec：未发现现有 `.spec` 文件

## 修复内容

- 新增 `cet4_reader/app_icon.py`，统一解析并加载 `assets/app.ico`。
- 在应用启动时设置：
  - `QApplication` 的应用名和应用级 `windowIcon`
  - Windows `AppUserModelID`
- 在 `MainWindow` 初始化时设置窗口图标，确保窗口左上角和任务栏使用同一个 CET-4 图标。
- 图标路径兼容源码运行、临时 `base_dir` 测试场景，以及 PyInstaller `_MEIPASS`/冻结程序目录。

## 验证结果

- 已运行：`.\run_tests.ps1`
- 结果：68 个测试全部通过

## 备注

- 本次未修改阅读、听力、查词、翻译等功能逻辑。
- 当前仓库未包含 PyInstaller spec；如后续新增 spec，应继续使用 `assets/app.ico` 作为 `icon` 参数，并将该资源打包进 `assets/app.ico` 路径。
