# Genshin MIDI Bridge

将 MIDI 键盘实时映射为游戏乐器按键的 Windows 桌面工具。

## 下载与安装

1. 打开 GitHub 仓库右侧的 **Releases**。
2. 下载最新版本的 `Genshin-MIDI-Bridge-Setup.exe`。
3. 运行安装程序；Windows 出现管理员权限提示时选择“是”。
4. 从开始菜单或桌面快捷方式启动 **Genshin MIDI Bridge**。

如果 Windows SmartScreen 提示“Windows 已保护你的电脑”，这是因为个人发布的程序尚未购买代码签名证书。确认文件来自本仓库的 Release 后，可选择“更多信息 → 仍要运行”。

## 使用

1. 通过 USB 或蓝牙连接能够发送 MIDI Note On/Off 的键盘。
2. 启动 Genshin MIDI Bridge，在主页选择设备与游戏中的乐器。
3. 点击“连接”，再点击“开始映射”。
4. 切回游戏、打开对应乐器并演奏。

普通蓝牙打字键盘不是 MIDI 设备。蓝牙 MIDI 键盘如果没有显示，可能需要厂商驱动或 BLE-MIDI 桥接软件。应用内“说明书”提供了完整步骤和排错方法。

## 功能

- USB MIDI 与 Windows 可见的蓝牙 MIDI 输入
- 多种三排、两排、和弦、变化音与打击乐预设
- 可视化钢琴键盘，白键和黑键均可独立编辑
- 黑键左右映射、外侧音域折叠、移调、八度偏移和力度门槛
- CC64 延音踏板与踏板期间的同音重复触发
- 简体中文、English、Español、日本語
- `Ctrl + Alt + F8` 开始或停止映射
- 本地保存设置，不读取游戏进程，不修改游戏文件

## 为什么请求管理员权限

Windows 不允许普通权限程序向管理员权限的游戏窗口发送输入。应用默认请求管理员权限，以保证映射可以生效。程序只发送所配置的键盘按键。

## 从源码运行（开发者）

要求 Windows 10/11 和 Python 3。运行 `run.bat`，首次启动会创建 `.venv` 并安装依赖。

## 构建发布文件

运行 `build_exe.bat` 生成 `dist\Genshin-MIDI-Bridge.exe`。安装 [Inno Setup](https://jrsoftware.org/isinfo.php) 后，运行 `build_installer.bat` 生成 `dist\Genshin-MIDI-Bridge-Setup.exe`。

## 配置与日志

- 配置：`%LOCALAPPDATA%\GenshinMidiBridge\config.json`
- 日志：`%LOCALAPPDATA%\GenshinMidiBridge\app.log`

## 乐器模式

- 风物之诗琴、跃律琴、谐律键琴：三排二十一键
- 晚风圆号：两排十四键
- 余音、悠可琴：和弦位于低一个物理八度
- 老旧的诗琴：变化音对应真实黑键，不存在的音保持关闭
- 绮筵之鼓、聚聚鼓：仅映射实际存在的打击键

## 隐私

应用不联网、不收集遥测数据。设置和日志只保存在本机。
