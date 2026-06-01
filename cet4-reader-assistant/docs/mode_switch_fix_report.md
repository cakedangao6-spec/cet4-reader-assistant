# CET-4 阅读助手：模式切换修复报告

## 修改内容

- 修复顶部“阅读模式 / 听力模式”切换逻辑。
- 将两个模式按钮的 lambda 连接改为 `QActionGroup` 统一分发，避免按钮状态和页面切换状态不同步。
- 切换时使用实际页面对象设置 `QStackedWidget` 当前页，确保区域显示与模式一致。
- 切换后同步：
  - 当前模式值
  - 当前显示页面
  - “阅读模式 / 听力模式”按钮选中状态
  - 当前文本编辑区焦点
  - 搜索状态和统计状态

## 未修改范围

- 未修改 `dictionary.py`
- 未修改在线查词逻辑
- 未修改翻译逻辑
- 未修改生词本导出逻辑
- 未重构阅读模式 UI

## 测试

已新增最小测试：

- `test_mode_actions_switch_between_reading_and_listening`

覆盖内容：

- 点击“听力模式”后显示听力页，听力按钮选中。
- 再点击“阅读模式”后显示阅读页，阅读按钮选中。
- 两个按钮状态互斥且与页面一致。

已运行：

```powershell
python -m unittest discover -s tests -v
```

结果：

```text
Ran 45 tests ... OK
```

## 快速状态块

- 项目：CET-4 阅读助手
- 当前状态：已修复阅读模式与听力模式双向切换，测试通过
- 入口文件：`cet4_reader/main.py`
- 运行方式：桌面快捷方式，或在 `cet4-reader-assistant` 目录运行 `python -m cet4_reader.main`
- 最后修改：2026-05-30
