# 在线查词多源兜底优化报告

## 改动内容

- 保留 Youdao 中国在线词典接口，并给其结果标记来源为 `Youdao`。
- 保留 Free Dictionary API 作为 VPN 或海外网络下更容易访问的英文词典源，并给其结果标记来源为 `Free Dictionary`。
- 保留 MyMemory 作为在线翻译型补充源，并给其结果标记来源为 `MyMemory`。
- 本地词典结果继续标记为 `本地词典`。
- 在线源失败、超时、返回空结果、解析失败时继续兜底；所有在线源都无结果后，沿用 UI 现有本地词典兜底逻辑。
- 将 Youdao 请求超时时间缩短为 1.2 秒，其他在线 JSON 请求维持 2.5 秒，降低 VPN 下被 Youdao 慢响应拖住的体感。
- Free Dictionary 命中时不再直接显示大段英文 definition；程序会按词性取简短释义，并优先用 MyMemory 将 definition 翻译成中文。
- Free Dictionary 的词性会简化显示，例如 `noun` -> `n`、`verb` -> `v`、`adjective` -> `adj`、`adverb` -> `adv`。
- Free Dictionary definition 翻译成功时，来源显示为 `Free Dictionary + MyMemory`；翻译失败时保留短英文释义，来源显示为 `Free Dictionary`。
- 未新增 UI 设置，双击加入生词、词形还原、翻译选择等调用面保持不变。

## 当前查词顺序/并发策略

1. 原词在线查词：Youdao 与 Free Dictionary 并发请求，谁先返回有效结果就使用谁。
2. Free Dictionary 若先返回，会先尝试用 MyMemory 把英文 definition 转成简短中文释义。
3. 如果 Youdao 与 Free Dictionary 都失败或无结果，再尝试 MyMemory 直接翻译单词。
4. 如果原词无在线结果，再对词形还原后的 headword 重复同样策略。
5. 如果仍无结果，再尝试简单后缀兜底候选词。
6. 所有在线尝试都无结果后，UI 沿用现有流程查询本地词典。

## 来源显示位置

- 查词显示区底部已有 `来源` 字段，现在会显示具体命中源：`Youdao`、`Free Dictionary`、`Free Dictionary + MyMemory`、`MyMemory` 或 `本地词典`。
- 查询中状态仍显示在线查询提示，最终结果回来后会替换为具体来源。

## 验证方式

- 新增字典单元测试，覆盖 Youdao 与 Free Dictionary 主源并发尝试，且有效的 Free Dictionary 结果可直接返回。
- 新增字典单元测试，覆盖主源返回空结果和解析失败后再调用 MyMemory。
- 新增字典单元测试，覆盖 Free Dictionary definition 经 MyMemory 翻译成短中文释义，并简化词性。
- 新增字典单元测试，覆盖 Free Dictionary definition 翻译失败时保留短英文释义。
- 运行现有测试：

```powershell
cd cet4-reader-assistant
powershell -ExecutionPolicy Bypass -File .\run_tests.ps1
```

结果：72 个测试全部通过。

## 手工验证建议

- 中国网络：启动应用，点击常见单词，例如 `important`、`society`、`classical`，观察查词区底部来源是否优先出现 `Youdao`；如果在线无结果，应看到 `本地词典`。
- VPN 网络：开启 VPN 后重复点击同一组单词，观察是否能较快显示 `Free Dictionary + MyMemory`、`Free Dictionary`、`MyMemory` 或 `本地词典`，并确认不会长时间停留在“查询中...”。Free Dictionary 命中时应优先看到 `n. 疾病`、`v. 传染` 这类短中文行，而不是整段英文长释义。
- 断网或接口不可用：临时断网后查词，确认最终仍能命中本地词典中的常见词。

## 快速状态报告

- 项目：CET-4 阅读助手
- 当前状态：已完成在线查词并发兜底、具体来源显示、Free Dictionary 中文化优化，并通过现有测试
- 入口文件：`cet4_reader/main.py`
- 运行方式：`cd cet4-reader-assistant` 后执行 `.\run.bat`
- 最后修改：`cet4_reader/dictionary.py`、`tests/test_dictionary.py`、`docs/online_dictionary_fallback_report.md`
