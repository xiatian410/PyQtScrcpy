"""Application translations, including the Qt Designer form."""
from PyQt6.QtCore import QTranslator

EN = {
    '刷新设备列表': 'Refresh devices', '重置ADB': 'Restart ADB',
    '投屏中保持亮屏': 'Stay awake',
    '有线连接转无线（连接成功后可拔线）': 'Switch USB to Wi-Fi',
    '--tcpip\n有线连接成功后自动转为无线通道\n此功能需要被控设备与此电脑处在同一局域网': '--tcpip\nSwitch USB to Wi-Fi on the same network',
    '连接成功后熄屏': 'Turn screen off', '断开投屏后熄屏': 'Power off on close',
    '禁用输入控制': 'Read-only', '置顶Scrcpy窗口': 'Always on top',
    '开启录制': 'Record', '选择': 'Browse', '文件保存路径': 'Recording folder',
    '限制录制时间为': 'Time limit', '录制时禁用投屏': 'Record without playback',
    '启动 Scrcpy 投屏': 'Start scrcpy', '视频通道': 'Video', '设置旋转': 'Rotation',
    '缓冲时间 ms': 'Buffer (ms)', '设置帧率': 'Frame rate', '目标屏幕': 'Display',
    '一般只有一个屏幕': 'Usually display 0', '分辨率限制': 'Maximum size',
    '--max-size\n长或宽的最大值': '--max-size\nMaximum width or height',
    '限制长或宽的最大值': 'Maximum width or height', '摄像头ID': 'Camera ID',
    '分辨率': 'Resolution', '帧率': 'FPS', '严禁将此功能用于任何违法用途': 'Camera capture requires Android 12+',
    '编解码器': 'Codec', 'AV1（可能不支持）': 'AV1 (if supported)', '码率：': 'Bitrate:',
    '音频通道': 'Audio', '系统声音': 'Device audio', '麦克风': 'Microphone', '默认': 'Default',
    '设备管理器': 'Device manager', '自定义隧道端口：': 'Tunnel port:',
    '关于PyQtScrcpy': 'About PyQtScrcpy', '安装PyQtScrcpy进系统': 'Component versions',
    '正在获取配置': 'Loading configuration',
}


class EnglishTranslator(QTranslator):
    def translate(self, context, sourceText, disambiguation=None, n=-1):
        return EN.get(sourceText, sourceText)
