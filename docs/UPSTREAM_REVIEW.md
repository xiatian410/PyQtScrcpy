# 上游调研与整合记录

调研日期：2026-11-18。通过 GitHub REST API 获取 issues（含关闭项）、评论、全部 PR、PR 文件差异及分支比较。

## 基线

- fork：https://github.com/xiatian410/PyQtScrcpy
- upstream：https://github.com/Stardawn0v0/PyQtScrcpy
- 双方 main：`80dfd95e5c5445cbd6131d75c8ea6e6e95b437b2`，比较结果 identical（ahead 0 / behind 0）。
- 当前本地开发分支：`feat/modernize-components`。
- 上游只有一个 PR（#7，open）；未发现其他待整合分支差异。
- 这里的“整合”指本地适配实现，未向 GitHub 推送，也未修改上游 issue / PR 状态。

## Issue / PR 处理

| 来源 | 上游状态 | 本次处理 | 验收边界 |
| --- | --- | --- | --- |
| [#1 窗口拖动卡顿](https://github.com/Stardawn0v0/PyQtScrcpy/issues/1) | closed | 统一 PyQt6，升级 Frameless Window；采用普通无边框窗口，移除强制 Mica 和旧背景特效分支 | Windows 10/11 拖动体验仍须实机验收 |
| [#2 Linux 不支持](https://github.com/Stardawn0v0/PyQtScrcpy/issues/2) | closed | 清理旧科学计算依赖，平台依赖由 Qt 扩展包声明；跨平台组件发现；去除 Windows shell 启动和目录假设 | 本机 Linux 验证；Windows/macOS 添加 CI，远端执行待推送 |
| [#3 GPL 与禁止商用](https://github.com/Stardawn0v0/PyQtScrcpy/issues/3) | closed | 保留 GPL-3.0；README 明确商业使用和分发义务；补充第三方说明 | 不改动原 LICENSE |
| [#4 Redmi 无法控制](https://github.com/Stardawn0v0/PyQtScrcpy/issues/4) | closed | 使用选中设备显式查询 `persist.security.adbinput`，精确判断 `0`；保留设备安全设置引导 | OEM 权限需用户在手机启用，不能声称软件绕过 |
| [#5 English](https://github.com/Stardawn0v0/PyQtScrcpy/issues/5) | open | Qt Designer 字符串翻译 + 新功能中英文文案；语言持久化；切换保留参数 | 第三方诊断输出保留原文 |
| [#6 虚拟显示](https://github.com/Stardawn0v0/PyQtScrcpy/issues/6) | open | `--new-display`、尺寸/DPI、`--start-app`、应用保留和系统装饰；与物理 display-id 互斥 | 参数与能力检测自动验证，设备兼容需真机 |
| [PR #7 安装 APK](https://github.com/Stardawn0v0/PyQtScrcpy/pull/7) | open | 保留功能设计并重新适配，显式 `-s`，`install -r`，安全参数数组，300 秒超时，GUI 线程恢复状态 | 真实 APK 安装需设备验收 |
| [#8 无线连接](https://github.com/Stardawn0v0/PyQtScrcpy/issues/8) | open | `adb pair` + `adb connect`；分离配对/连接端口；IPv4、主机名、括号 IPv6；隐藏且不保存配对码 | mDNS 自动发现留待下一阶段 |

PR #7 作者为 **hansaes**，审阅 head：`06d1037a73dd58a73a55b021e2c4db7a4b10b3b2`。其原补丁还包含异常的 `self.da` 注解语句、重复安装按钮定义、使用全局设备环境变量、shell 拼接及后台线程修改控件，因此本次采用注明来源的适配整合，而非直接应用整个补丁。

## 同步修复

- `--orientation` → `--display-orientation`；`--display-buffer` → `--video-buffer`；启动前用实际 scrcpy `--help` 验证所有参数。
- 录制目录转换为唯一 MKV 文件；修复“置顶”复选框未生效。
- 摄像头 ID 保留字符串，空结果不崩溃，高速模式实际传入 `--camera-high-speed`。
- 不再修改全局 `ANDROID_SERIAL`；切换设备丢弃过期结果；按需查询屏幕或摄像头。
- 子进程输出 UTF-8 容错解码，支持含空格/中文/特殊字符路径，避免 shell 解释。
- 任务超时和错误路径恢复控件；移除吞掉 RuntimeError 的全局异常处理。
- 错误日志写入用户目录；新增有上限的运行日志。
- “安装进系统”未实现占位按钮改为可用的组件版本检查，“关于”显示来源与许可证。

## 一手资料

- [分支对比](https://github.com/Stardawn0v0/PyQtScrcpy/compare/main...xiatian410:PyQtScrcpy:main)
- [scrcpy v5.0.1](https://github.com/Genymobile/scrcpy/releases/tag/v5.0.1)
- [scrcpy v5.0.1 CLI 源码](https://github.com/Genymobile/scrcpy/blob/v5.0.1/app/src/cli.c)
- [Android Platform-Tools 发布说明](https://developer.android.com/tools/releases/platform-tools)
- [Android 仓库稳定通道元数据](https://dl.google.com/android/repository/repository2-3.xml)
- [PyQt6](https://pypi.org/project/PyQt6/) / [Fluent Widgets](https://pypi.org/project/PyQt6-Fluent-Widgets/) / [Frameless Window](https://pypi.org/project/PyQt6-Frameless-Window/)
