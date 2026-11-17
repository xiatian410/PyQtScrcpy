# PyQtScrcpy

基于 PyQt6 的 scrcpy 桌面界面，支持 USB / 无线投屏、APK 安装、录屏、摄像头捕获和虚拟显示。由 [Stardawn0v0/PyQtScrcpy](https://github.com/Stardawn0v0/PyQtScrcpy) 派生，本分支对上游 issues 和 PR 进行了适配整合。

## 运行

推荐 Python 3.13 或 3.14（最低 3.12）。Windows 10/11、Linux x86_64 和 macOS；Linux 桌面需要 Qt 的系统运行库。Windows 便携组件在 `bin/` 中，其他平台可使用下面的下载脚本。

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/update_components.py
python main.py
```

Debian/Ubuntu 创建虚拟环境前可安装 `python3-venv`；Qt 缺少系统库时安装 `libegl1 libopengl0 libxkbcommon0 libxcb-cursor0`。Linux USB 访问还需发行版提供的 Android udev 规则和正确的用户组权限。

组件搜索顺序：`PYQTSCRCPY_ADB` / `PYQTSCRCPY_SCRCPY` 指定的可执行文件 → `tools/platform-tools`、`tools/scrcpy` → Windows `bin/` → 系统 PATH。运行 `python scripts/check_components.py` 可查看实际选择的文件及版本。

`components.lock.json` 固定官方下载地址与 SHA-256。下载脚本验证完整包后安装，保留 `tools/<组件>.previous` 供手动回退；关闭应用后将当前目录改名，并把 `.previous` 改回原目录名即可。升级 manifest 后重新运行脚本。脚本不会静默从网络选择未经测试的新版本。

## 使用

- **USB**：启用开发者选项和 USB 调试，接受手机授权，刷新列表并选择目标设备。未授权、离线状态会提示。
- **安装 APK**：选择设备后点击“安装 APK”。使用 `adb -s <serial> install -r` 覆盖安装，保留应用数据；降级、签名不匹配等错误显示 ADB 原始原因。
- **无线调试**：Android 11+ 在开发者选项启用无线调试。首次连接填写“使用配对码配对设备”页面的配对地址和六位配对码，并填写无线调试主页的连接地址。两处端口通常不同；已配对时只填连接地址。电脑和手机需在同一网络。旧设备可使用“有线连接转无线”。配对码不保存到设置，也不放入命令行。
- **虚拟显示**：打开高级面板，在“设备屏幕”页启用。尺寸支持 `1920x1080/420`、`/240` 或留空；可指定 Android 应用包名。创建虚拟显示时不再发送物理屏幕 ID。需要 scrcpy 3.0+ 和兼容的 Android 设备。
- **录屏**：选择目录，自动创建唯一时间戳 `.mkv` 文件。支持时长限制和不播放仅录制。
- **语言**：高级面板底部切换简体中文 / English，设置会保留。第三方工具输出保留原文。
- **日志**：高级面板“运行日志”查看 scrcpy 输出；异常退出时自动打开。最多保留 3000 行，日志可能包含设备标识，提交问题时请自行脱敏。
- **小米/红米/澎湃 OS**：有画面但无法控制时，检查开发者选项中的“USB 调试（安全设置）”。此权限由设备系统控制；更新电脑组件不能绕过。

关闭界面前会提示结束活跃投屏；正在进行 APK 安装、配对等操作时需等待任务结束。ADB 重置会影响同一电脑上的其他 ADB 客户端，请仅在连接故障时使用。

## 开发和构建

```bash
python -m pip install -r requirements-dev.txt
pyuic6 mainWindow.ui -o mainWindow.py
python -m pytest -q
python -m pip check
python scripts/update_components.py
python -m PyInstaller --noconfirm PyQtScrcpy.spec
```

Qt Designer 的静态界面由 `mainWindow.ui` 生成；新增运行时控件在 `main.py`。资源 `res_rc.py` 使用 PyQt6，保留原项目图标数据。请勿重新引入 PyQt5/PySide 绑定混用。

GitHub Actions 在 push/PR 时执行跨平台测试；手动运行工作流会生成 Windows、Linux、macOS 目录式构建并上传 artifact。构建只在对应系统生成，不自动发布 Release。更新器只提供官方已有的架构组合；Linux ARM 请自行安装组件并通过环境变量指定。

## 版本和维护资料

截至 2026-11-18 核对的稳定版本：PyQt6 6.12.1（Qt 6.12.0）、Fluent Widgets 1.11.3、Frameless Window 0.8.2、scrcpy 5.0.1、Android Platform-Tools 37.0.1。Platform-Tools 37.0.3 在官方仓库属于预览通道，本分支不采用。

- [上游整合记录](docs/UPSTREAM_REVIEW.md)
- [组件与验证记录](docs/VALIDATION.md)
- [后续更新优化方案](docs/ROADMAP.md)
- [第三方组件和许可证](docs/THIRD_PARTY.md)

## License

本项目遵循 [GPL-3.0](LICENSE)，保留原项目版权。GPL 允许商业使用，分发及修改须遵守许可证义务。Qt、scrcpy、Android SDK 工具、FFmpeg、SDL、libusb 和图标分别遵循各自许可证，详见第三方说明。
