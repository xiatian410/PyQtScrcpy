# 第三方组件

PyQtScrcpy 保留上游 GPL-3.0 LICENSE 及作者来源。此表用于追踪依赖；发布者应随分发形式履行各许可证义务并提供所需许可证、通知和对应源码。

| 组件 | 来源 | 许可证/说明 |
| --- | --- | --- |
| PyQt6 | https://www.riverbankcomputing.com/software/pyqt/ | GPLv3 或商业许可 |
| Qt 6 | https://www.qt.io/licensing/ | 各模块有 LGPL/GPL/商业条款，参见发行包许可证 |
| PyQt6-Fluent-Widgets | https://github.com/zhiyiYo/PyQt-Fluent-Widgets | GPLv3；未使用商业 Pro 组件 |
| PyQt6-Frameless-Window | https://github.com/zhiyiYo/PyQt-Frameless-Window | GPLv3 |
| scrcpy / server | https://github.com/Genymobile/scrcpy | Apache-2.0；本项目按官方包整套分发 |
| SDL / FFmpeg / libusb | scrcpy 官方发布包及其项目主页 | 各自许可证随构建选项变化，遵循官方包提供的 LICENSE/说明；保留原文件 |
| Android Platform-Tools | https://developer.android.com/tools/releases/platform-tools | Google Android SDK 条款及组件 NOTICE；保留 `NOTICE.txt` 和 `source.properties` |
| IconPark 图标 | https://iconpark.oceanengine.com/official | 图标来源沿用上游；图标并非项目自创 |

`bin/` 为 Windows x64 的 scrcpy 5.0.1 官方包，ADB 及 Windows USB DLL 更新为 Google Platform-Tools 37.0.1。`tools/` 由校验脚本下载对应平台组件，包含上游附带文件和本地 component.json。构建包保留工具目录和本说明。

平台包下载地址、版本和 SHA-256 见 `components.lock.json`。Google 校验来源为 repository2-3.xml 的 stable/channel-0；本次下载先验证官方 SHA-1，再写入本项目 SHA-256 锁定值。scrcpy SHA-256 来自官方 GitHub release asset digest。
