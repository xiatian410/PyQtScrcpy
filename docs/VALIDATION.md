# 验证记录与组件版本

日期：2026-11-18。环境：Linux x86_64、Python 3.13.5、Qt offscreen（无实体显示器）。

## 组件清单

| 组件 | 原版本 | 当前版本 |
| --- | --- | --- |
| Qt 绑定 | PyQt5 5.15.10 / Qt 5.15.2 | PyQt6 6.12.1 / Qt 6.12.0 |
| SIP | PyQt5-sip 12.13.0 | PyQt6-sip 13.13.1 |
| Fluent Widgets | 1.5.8 | PyQt6 版 1.11.3 |
| Frameless Window | 0.3.9 | PyQt6 版 0.8.2 |
| scrcpy | 仓库旧二进制，未在 Windows 执行确认版本 | 5.0.1，server 与主程序匹配 |
| Platform-Tools | 仓库旧二进制，未执行确认版本 | 37.0.1；ADB 1.0.41 |
| SDL | SDL2.dll | 官方 5.0.1 包 SDL3；Linux 实测 3.4.18 |
| FFmpeg 库 | avcodec-61 / avformat-61 / avutil-59 / swresample-5 | avcodec-63 / avformat-63 / avutil-61 / swresample-7（Windows）；Linux 实测 63.1.102 / 63.1.102 / 61.1.102 |
| libusb | 仓库旧 DLL | 官方 5.0.1 包；Linux 实测 1.0.30 |
| 打包 | Nuitka Action v1.1 + 浮动 main | PyInstaller 6.22.3，hooks-contrib 2026.10 |
| 测试 | 无 | pytest 9.2.0 |
| Actions | checkout v3 / setup-python v4 / upload-artifact v3 | v7.0.1 / v7.1.0 / v7.0.2 |

移除应用未使用的 numpy、scipy、pillow、colorthief、PyQt5-stubs 和旧的 Qt5/平台锁定项。darkdetect 0.8.0 仍由 Fluent 依赖且已是查询到的现行版。平台专用依赖由 Frameless Window 的环境标记解析；本机未安装 Windows/macOS 专用包。

版本信息来自 PyPI、GitHub official releases 和 Google Android repository stable/channel-0。完整锁定的外部组件 URL/校验值见 components.lock.json，Windows 单文件校验见 bin/components.json。

## 已执行

- 43 项 pytest 测试通过：纯逻辑、命令行隔离、APK 路径/序列号、配对码、连接失败、虚拟显示、摄像头解析、时长校验、归档解压安全、Qt 界面、语言切换、任务恢复、过期结果丢弃、数字控件可见性、图标加载、实际 scrcpy 帮助参数检查。
- `python -m pip check`：No broken requirements found。
- `pyuic6` 从 mainWindow.ui 重新生成，使用 PyQt6 6.12.1。
- 本机 scrcpy `--version` / `--help` 与 ADB `version` / `devices -l` 成功执行。
- Google 三平台包先验证官方 SHA-1，再生成 SHA-256；scrcpy Linux 与 Windows 包验证官方 SHA-256 后安装。
- Qt offscreen 冷启动、基本/高级界面截图检查；修复 Fluent 数字控件在 Qt 6.12 下输入区宽度异常，改用原生数字与时间控件；修复资源未显式注册导致图标缺失。
- Linux PyInstaller 目录式构建成功，产物位于 dist/PyQtScrcpy/。从 `/tmp` 启动打包后的程序，持续运行 5 秒且无标准错误输出；验证不依赖源码工作目录。构建与启动日志保存在本地 verification/。
- UI 重新生成与已保存代码逐字节一致；`git diff --check` 通过。

## 待真实环境验收

`adb devices -l` 为空，本机没有 Android 设备。因此没有宣称真实 USB/无线投屏、控制、音视频录制、APK 安装、摄像头或虚拟显示已成功。Windows/macOS 的 CI 配置已写好，但此任务没有推送远端，尚无远端 CI 运行结果。Windows DLL 仅完成官方包校验与更新，没有在 Windows 执行。

Linux offscreen 不代表 X11/Wayland 桌面、多屏 DPI 或 Windows 拖动体验已经验收。Linux 构建使用当前系统 glibc，不能据此承诺在更旧发行版运行。正式发布前按 ROADMAP 的 P0 矩阵验收。
