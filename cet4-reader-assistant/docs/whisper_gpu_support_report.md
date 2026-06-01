# 快速状态

- 项目：CET-4 阅读助手（听力模式）
- 当前状态：已完善 GPU 推理检测、CPU 自动回退、运行信息显示和本地诊断脚本；已修复 CUDA/cuBLAS/cuDNN 运行库链路，faster-whisper `small + cuda/float16` 已完成真实 GPU 推理
- 入口文件：`cet4_reader/main.py`
- 运行方式：在 `cet4-reader-assistant` 目录运行 `.venv\Scripts\python.exe -m cet4_reader.main`，或双击 `run_app.bat`
- 最后修改：2026-05-31

# GPU环境检查

- 显卡：`nvidia-smi` 可见 `NVIDIA GeForce RTX 4060 Laptop GPU`
- 驱动：`591.59`
- nvidia-smi 显示 CUDA Version：`13.1`
- 显存：`8188 MiB`
- torch：当前虚拟环境未安装，无法用 torch 检测 GPU
- faster-whisper：`1.2.1`
- ctranslate2：`4.7.2`
- ctranslate2 CUDA 设备数：`1`
- ctranslate2 CUDA 支持精度：包含 `float16`
- CUDA/cuBLAS/cuDNN 运行库来源：项目虚拟环境内 NVIDIA 官方 wheel
  - `nvidia-cublas-cu12`：`12.9.2.10`
  - `nvidia-cudnn-cu12`：`9.23.0.39`
  - `nvidia-cuda-runtime-cu12`：`12.9.79`
  - `nvidia-cuda-nvrtc-cu12`：`12.9.86`
- 已加入当前用户 PATH：
  - `D:\Codex Project\CET-4\cet4-reader-assistant\.venv\Lib\site-packages\nvidia\cublas\bin`
  - `D:\Codex Project\CET-4\cet4-reader-assistant\.venv\Lib\site-packages\nvidia\cudnn\bin`
  - `D:\Codex Project\CET-4\cet4-reader-assistant\.venv\Lib\site-packages\nvidia\cuda_runtime\bin`
  - `D:\Codex Project\CET-4\cet4-reader-assistant\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin`
- DLL 加载检查：
  - `cublas64_12.dll`：可被 `where.exe` 找到
  - `cublasLt64_12.dll`：可被 `where.exe` 找到
  - `cudnn64_9.dll`：可被 `where.exe` 找到
  - `cudnn_ops64_9.dll`：可被 `where.exe` 找到
- 实际 faster-whisper GPU 模型加载：`GPU model load OK`
- 实际 faster-whisper GPU 转录：`small + cuda/float16` 正常完成

结论：界面选择 GPU 后不会只是显示 GPU。程序会真实尝试并运行 `cuda + float16`；当前 RTX 4060 环境已经能完成 faster-whisper GPU 推理。

# 修改内容

- 在 `cet4_reader/listening.py` 增加 CUDA 运行时选择：
  - 默认 CPU + int8 保持不变
  - 请求 GPU 时先检测 ctranslate2 CUDA 设备和 `float16` 支持
  - CUDA 不可用时直接回退 CPU
  - GPU 初始化或转录失败时捕获异常并回退 CPU
- 在 `cet4_reader/ui.py` 增强识别状态：
  - 开始识别时显示设备、模型、精度
  - 完成识别时显示实际运行设备、模型、精度
  - GPU 失败时显示已回退 CPU
- 增加 `scripts/whisper_gpu_diagnostics.py`：
  - 检查 nvidia-smi、torch、faster-whisper、ctranslate2
  - 用现有音频测试 CPU/GPU
  - 默认只使用本地缓存模型，不自动下载 medium/large-v3
- 增加单元测试：
  - CUDA 不可用时预检查回退
  - GPU 初始化失败时回退
  - GPU 成功路径仍使用 `cuda + float16`

# 测试结果

测试命令：

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

结果：`Ran 58 tests ... OK`

真实音频：

`D:\Codex Project\CET-4\cet4-abloop-player\materials\listening\25-6-1\cet4_2025_06_1.mp3`

诊断命令：

```powershell
.venv\Scripts\python.exe scripts\whisper_gpu_diagnostics.py "D:\Codex Project\CET-4\cet4-abloop-player\materials\listening\25-6-1\cet4_2025_06_1.mp3" --models small medium
```

| 模型 | 设备 | 精度 | 结果 | 耗时 | 显存占用 |
|---|---|---|---|---:|---:|
| small | CPU | int8 | 正常完成 | 235.56s | 约 403 MiB 基线占用 |
| small | GPU | float16 | 正常完成，确认真正使用 GPU | 36.36s | 峰值约 1265 MiB |
| medium | CPU | int8 | 未测试，模型本地未缓存 | 0.00s | - |
| medium | GPU | float16 | 未测试，模型本地未缓存 | 0.00s | - |

CPU / GPU 加速倍率：

- CPU small/int8：235.56s
- GPU small/float16：36.36s
- 加速倍率：约 `6.48x`
- 当前应用内 GPU 模式会自动回退 CPU，不会崩溃

# 模型建议

- 当前默认继续保持 `small + CPU/int8`，这是兼容性最稳路径。
- GPU 模式现在可用于推理加速；`small + GPU/float16` 已在 RTX 4060 上跑通。
- 如需排查识别准确率，下一步可单独下载并测试 `medium + GPU/float16`。
- `large-v3` 对显存和加载时间要求更高；RTX 4060 8GB 有机会运行，但建议只作为专项测试，不建议设为默认。
- `medium` 当前未本地缓存，本次未下载模型，避免引入大文件和额外变量。

# 后续建议

- 新开终端后再次运行 `where.exe cublas64_12.dll` 和 `where.exe cudnn64_9.dll`，确认用户 PATH 已继承。
- 若后续移动项目目录或重建 `.venv`，需要重新安装 NVIDIA wheel 并更新 PATH。
- 下载 `medium` 模型后重新运行诊断脚本，记录 `medium` 的 CPU/GPU 耗时和显存峰值。
- 如需 torch 检测项，可单独安装匹配 CUDA 的 PyTorch；但 faster-whisper 推理本身不依赖 torch，不建议为了诊断强制加入项目依赖。
- 本次没有训练模型，没有下载四级数据集，也没有构建新的 AI 训练流程。
