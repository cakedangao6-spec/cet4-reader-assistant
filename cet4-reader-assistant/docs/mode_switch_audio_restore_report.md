# CET-4 阅读助手：模式切换与音频恢复修复报告

## 问题定位

- 桌面快捷方式已确认指向当前项目：
  - `TargetPath`: `C:\Windows\System32\wscript.exe`
  - `Arguments`: `D:\Codex Project\CET-4\cet4-reader-assistant\run_app_hidden.vbs`
  - `WorkingDirectory`: `D:\Codex Project\CET-4\cet4-reader-assistant`
- 听力模式下点击“阅读模式”无反应的根因不是旧目录，也不是 `QActionGroup` 逻辑。
- 通过 `childAt` 检查发现，“阅读模式”按钮位置实际命中一个空的 `QLabel`。
- 该空控件来自搜索状态 label，未放入布局也未隐藏，默认位于窗口左上角，覆盖了工具栏左侧按钮区域。

## 修复内容

- 隐藏搜索状态 label，并设置 `WA_TransparentForMouseEvents`，确保鼠标事件到达顶部模式按钮。
- 保持阅读模式 / 听力模式双向切换逻辑：
  - 切换当前页面
  - 同步按钮选中状态
  - 同步当前模式值
  - 同步焦点、搜索和统计状态
- 新增音频路径持久化：
  - 导入音频后保存完整绝对路径到 `runtime/session.json`
  - 启动时自动恢复上次音频
  - 不复制音频文件
  - 原文件不存在时提示并清除失效路径
  - 顶部“一键清空 / 重新开始”会清除已保存音频路径和标记状态

## 验证

- 已确认听力模式下“阅读模式”按钮位置命中 `QToolButton 阅读模式`，不再被空 label 覆盖。
- 已用真实 MP3 验证：
  - `C:\Users\shaolang\Desktop\四级单词\真题\25-6-1\cet4_2025_06_1.mp3`
  - 导入后保存路径
  - 关闭后重新打开可自动恢复
  - 播放器读取到总时长 `1416045 ms`
  - 一键清空后再次启动不再自动加载音频

## 测试

已新增/补充最小测试：

- 阅读模式 / 听力模式来回切换
- 听力模式下阅读按钮可被鼠标点击
- 音频路径保存
- 启动恢复音频
- 一键清空清除音频路径

已运行：

```powershell
python -m unittest discover -s tests -v
```

结果：

```text
Ran 49 tests ... OK
```

## 快速状态块

- 项目：CET-4 阅读助手
- 当前状态：已修复模式按钮遮挡问题，已支持音频路径保存与启动恢复，测试通过
- 入口文件：`cet4_reader/main.py`
- 运行方式：桌面快捷方式，或在 `D:\Codex Project\CET-4\cet4-reader-assistant` 目录运行 `python -m cet4_reader.main`
- 最后修改：2026-05-30
