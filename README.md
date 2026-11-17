<div align="center">

# PyQtScrcpy · 2.0.0-dev

**基于 PyQt6 的 Android 投屏与设备管理桌面工具**

USB / 无线投屏 · APK 安装 · 音视频录制 · 摄像头捕获 · 虚拟显示 · 中英文界面

[![CI](https://github.com/xiatian410/PyQtScrcpy/actions/workflows/main.yml/badge.svg?branch=2.0.0-dev)](https://github.com/xiatian410/PyQtScrcpy/actions/workflows/main.yml?query=branch%3A2.0.0-dev)
[![Version](https://img.shields.io/badge/version-2.0.0--dev-orange)](https://github.com/xiatian410/PyQtScrcpy/tree/2.0.0-dev)
[![Python](https://img.shields.io/badge/Python-3.13%20%7C%203.14-blue)](#快速开始)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

[快速开始](#快速开始) · [功能说明](#功能说明) · [构建与测试](#构建与测试) · [更新计划](docs/ROADMAP.md) · [问题反馈](https://github.com/xiatian410/PyQtScrcpy/issues)

</div>

## 项目状态

本项目基于 [Stardawn0v0/PyQtScrcpy](https://github.com/Stardawn0v0/PyQtScrcpy) 持续维护，整合上游功能请求，并升级 Qt、scrcpy 和 Android Platform-Tools。

**当前开发版本及默认分支为 `2.0.0-dev`，尚未发布 2.0 稳定版。** 默认分支用于展示当前开发成果，`main` 保留原项目基线；仓库历史 Release 不代表本分支的新版构建。

本地 Linux 已通过 **43 项自动化测试**、依赖检查、界面启动及目录式打包验证。Windows/macOS 和 Android 真机功能仍需按[验收计划](docs/ROADMAP.md)验证；远端 CI 结果以顶部徽章及 [Actions](https://github.com/xiatian410/PyQtScrcpy/actions) 页面为准。详细证据见[验证记录](docs/VALIDATION.md)。

## 功能概览

| 功能 | 支持内容 |
| --- | --- |
| 设备管理 | USB 设备发现、明确选择目标设备、未授权/离线提示、ADB 重启 |
| 无线调试 | Android 11+ 配对码配对、IP/端口连接、有线切换无线 |
| APK 安装 | 安装至所选设备、覆盖安装、错误输出和超时处理 |
| 屏幕与摄像头 | 分辨率、帧率、码率、旋转、摄像头选择、高速捕获 |
| 音视频录制 | 唯一时间戳 MKV 文件、时长限制、仅录制不播放 |
| 虚拟显示 | 尺寸/DPI、启动指定应用、关闭后保留应用、系统装饰 |
| 桌面交互 | 中英文切换、窗口置顶、屏幕电源控制、运行日志 |
| 组件维护 | 固定版本、官方包 SHA-256 校验、上一版目录备份 |

## 快速开始

推荐 **Python 3.13 或 3.14**，最低 Python 3.12。首次运行前在手机开启开发者选项和 USB 调试，并接受电脑的调试授权。

### Windows PowerShell

```powershell
git clone --branch 2.0.0-dev https://github.com/xiatian410/PyQtScrcpy.git
cd PyQtScrcpy
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/update_components.py
.\.venv\Scripts\python.exe main.py
```

Windows x64 的便携组件已包含在 `bin/`。更新脚本将对应平台的校验包安装到优先使用的 `tools/` 目录。以上命令直接调用虚拟环境中的 Python，无需修改 PowerShell 执行策略。

### Linux / macOS

```bash
git clone --branch 2.0.0-dev https://github.com/xiatian410/PyQtScrcpy.git
cd PyQtScrcpy
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/update_components.py
.venv/bin/python main.py
```

Debian/Ubuntu 缺少虚拟环境或 Qt 系统库时，可先安装：

```bash
sudo apt-get update
sudo apt-get install python3-venv libegl1 libopengl0 libxkbcommon0 libxcb-cursor0
```

Linux USB 访问还需要发行版提供的 Android udev 规则和正确的用户组权限。

| 平台 | 组件获取 | 当前验证范围 |
| --- | --- | --- |
| Windows x64 | 自带 `bin/` 或更新脚本 | 官方组件校验完成；桌面及设备操作待实机验收 |
| Windows ARM64 | 更新脚本 | 未实机验证；需系统支持所选工具及 Python/Qt 架构 |
| Linux x86_64 | 更新脚本或系统安装 | 本地测试、offscreen 界面及打包启动通过 |
| macOS Intel / Apple Silicon | 更新脚本 | 已配置 CI；桌面及设备操作待实机验收 |
| Linux ARM | 自行安装 adb/scrcpy | 更新脚本无官方对应包，未验证 |

### 获取构建产物

在 [Actions → Test and build](https://github.com/xiatian410/PyQtScrcpy/actions/workflows/main.yml) 手动运行工作流，选择 `2.0.0-dev`。测试通过后会构建并上传对应平台 artifact。下载后需完整解压并保留工具目录；当前流程不自动发布 Release。

## 功能说明

### USB 投屏与 APK 安装

1. 连接手机，开启 USB 调试并接受授权。
2. 点击“刷新设备列表”，选择目标设备。
3. 点击“启动 Scrcpy 投屏”，或点击“安装 APK”选择安装包。

安装使用 `adb -s <serial> install -r`，覆盖安装时保留应用数据。版本降级、签名冲突、存储不足等情况显示 ADB 原始错误。

### 无线调试

Android 11+ 在开发者选项中开启“无线调试”。首次连接时填写两组地址：

| 字段 | 从手机哪里获取 |
| --- | --- |
| 连接地址 `IP:端口` | 无线调试主页 |
| 配对地址 `IP:端口` 与六位配对码 | “使用配对码配对设备”页面 |

**配对端口和连接端口通常不同。** 已配对设备只需填写连接地址；电脑和手机需处于可互通的网络。配对码不保存到设置，也不放入进程命令行。旧设备可使用“有线连接转无线”。

### 虚拟显示

打开高级面板，在“设备屏幕”页启用“创建虚拟显示”：

- 尺寸可填 `1920x1080/420`、`/240`，或留空使用主屏幕参数。
- 应用填写包名，例如 `org.mozilla.firefox`；不指定时可留空。
- 可选择关闭后保留应用，以及是否显示系统装饰。

虚拟显示与物理屏幕 ID 互斥，需要 scrcpy 3.0+ 和兼容的 Android 设备；本分支配套 scrcpy 5.0.1。

### 录屏、语言与日志

选择录屏目录后，程序自动创建唯一时间戳 `.mkv` 文件，支持时长限制和仅录制不播放。高级面板底部可切换简体中文 / English，语言设置会保留。第三方工具的诊断输出保留原文。

“运行日志”最多保留 3000 行，scrcpy 异常退出时自动打开。关闭界面会提示结束活跃投屏；APK 安装、配对等任务执行期间需等待操作结束。

## 常见问题

**有画面但无法控制小米/红米设备**：检查开发者选项中的“USB 调试（安全设置）”。输入权限由设备系统控制；更新电脑组件不能绕过该限制。

**找不到 adb 或 scrcpy**：运行 `python scripts/check_components.py` 查看实际使用的文件和版本；必要时重新运行更新脚本。命令中的 `python` 请替换为虚拟环境中的 Python。

**连接失败或设备未授权**：检查数据线、手机授权和设备状态；无线连接检查网络与端口。ADB 重置会影响同一电脑上的其他 ADB 客户端，仅在需要时使用。

**提交问题**：请提供操作系统、Python/Qt/组件版本、手机型号与 Android 版本、复现步骤，以及脱敏后的日志。日志可能包含设备序列号和网络地址，请勿提交配对码。

## 组件版本与更新

以下版本于 **2026-11-18** 核对，完整清单见[验证记录](docs/VALIDATION.md)。

| 组件 | 锁定版本 |
| --- | --- |
| PyQt6 / Qt | 6.12.1 / 6.12.0 |
| PyQt6-sip | 13.13.1 |
| PyQt6-Fluent-Widgets | 1.11.3 |
| PyQt6-Frameless-Window | 0.8.2 |
| scrcpy / server | 5.0.1 |
| Android Platform-Tools | 37.0.1（稳定通道） |
| PyInstaller / pytest | 6.22.3 / 9.2.0 |

Platform-Tools 37.0.3 在官方仓库属于预览通道，本分支采用稳定版。scrcpy 的 SDL、FFmpeg、libusb 随官方包整套更新，避免可执行文件、server 和 DLL 版本混用。

工具查找优先级：环境变量 `PYQTSCRCPY_ADB` / `PYQTSCRCPY_SCRCPY` → `tools/` 对应组件目录 → `bin/` 对应平台文件 → 系统 PATH。

[components.lock.json](components.lock.json) 固定官方下载地址与 SHA-256。更新脚本验证完整包后安装，保留 `tools/<组件>.previous`；关闭应用后可以将当前目录改名，再将 `.previous` 改回原目录名进行回退。它安装的是仓库锁定版本，不会自动选择未经测试的新版本。

## 构建与测试

在虚拟环境中执行：

```bash
python -m pip install -r requirements-dev.txt
pyuic6 mainWindow.ui -o mainWindow.py
python scripts/update_components.py
python -m pytest -q
python -m pip check
python -m PyInstaller --noconfirm PyQtScrcpy.spec
```

产物位于 `dist/PyQtScrcpy/`，需在对应操作系统构建。Linux 构建受构建主机 glibc 版本限制。静态界面由 `mainWindow.ui` 生成；运行时控件在 `main.py`；资源使用 PyQt6，不应混用其他 Qt 绑定。

push/PR 自动触发测试；手动工作流在测试通过后生成构建产物。CI 配置不等于所有平台已经验证通过，请查看具体运行记录。

## 开发与维护

### 提交身份

使用已登录的 GitHub CLI 账号创建提交，无需在脚本或仓库中填写个人姓名、邮箱：

```bash
gh auth status --hostname github.com
git add <要提交的文件>
python scripts/git_commit.py -m "说明本次改动"
git push
```

每次执行都会从 GitHub 查询当前账号，以账号用户名和 `ID+用户名@users.noreply.github.com` 设置本次提交的作者及提交者。身份仅通过该进程的环境变量传递，不改写全局 Git 配置；查询失败时停止提交。切换 `gh` 当前账号后，下次提交自动采用新身份。历史提交的身份不会随账号切换改变。

- [上游 issues / PR 调研及整合记录](docs/UPSTREAM_REVIEW.md)
- [组件与验证记录](docs/VALIDATION.md)
- [后续更新优化方案](docs/ROADMAP.md)：真机验收 → 连接与架构优化 → 界面与性能优化
- [第三方组件及许可证](docs/THIRD_PARTY.md)

感谢原作者 **Stardawn0v0** 及贡献者。APK 安装功能参考 **hansaes** 的 [上游 PR #7](https://github.com/Stardawn0v0/PyQtScrcpy/pull/7)，已针对当前架构重新适配。其他上游问题的处理方式和验证边界均记录在整合文档中。

## License

本项目遵循 [GPL-3.0](LICENSE)，保留原项目版权。GPL 允许商业使用，修改和分发须遵守许可证义务。Qt、scrcpy、Android SDK 工具、FFmpeg、SDL、libusb 和图标分别遵循各自许可证，详见[第三方说明](docs/THIRD_PARTY.md)。
