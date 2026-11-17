"""PyQtScrcpy desktop application. All widget access stays on the Qt thread."""
import datetime
import os
from pathlib import Path
import sys
import traceback

from PyQt6 import QtGui
from PyQt6.QtCore import (QObject, QRunnable, QThreadPool, QSettings, QTimer,
                          QProcess, Qt, pyqtSignal, QLocale, QProcessEnvironment)
from PyQt6.QtWidgets import (QApplication, QFileDialog, QDialog, QFormLayout,
                             QDialogButtonBox, QLineEdit, QPlainTextEdit, QVBoxLayout, QHBoxLayout)
from qfluentwidgets import MessageBox, PushButton, CheckBox, LineEdit, ComboBox
from qframelesswindow import FramelessWindow, StandardTitleBar

import backend
import util
import res_rc  # Register application resources; pyuic6 does not emit this import.
from consts import DATA_PATH, TOOL_AUTHOR, TOOL_NAME, TOOL_VERSION
from i18n import EnglishTranslator
from info_bar import info_bar
from mainWindow import Ui_Form


class TaskSignals(QObject):
    finished = pyqtSignal(object, object, object)


class Task(QRunnable):
    def __init__(self, function, callback):
        super().__init__()
        self.function, self.callback = function, callback
        self.signals = TaskSignals()

    def run(self):
        try:
            result, error = self.function(), None
        except Exception as exc:
            result, error = None, str(exc)
        self.signals.finished.emit(self.callback, result, error)


class MainWindow(FramelessWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('PyQtScrcpy', 'PyQtScrcpy')
        self.language = self.settings.value('language', 'zh' if QLocale.system().name().startswith('zh') else 'en')
        self.translator = EnglishTranslator(self)
        if self.language == 'en':
            QApplication.instance().installTranslator(self.translator)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(4)
        self.tasks = set()
        self.processes = set()
        self.camera_info = {}
        self.video_source = 'screen'
        self.query_generation = 0
        self.busy_count = 0
        self.setupUi(self)
        self.setTitleBar(StandardTitleBar(self))
        self.titleBar.maxBtn.hide()
        self.titleBar.raise_()
        # QPixmap eagerly loads the registered resource, including on headless Qt.
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(':/icon/res/logo.png')))
        self.pro_page.setIcon(QtGui.QIcon())
        self.pro_page.setText('☰')
        self.pro_page.setToolTip(self.t('高级设置', 'Advanced settings'))
        self.setWindowTitle(f'{TOOL_NAME} {TOOL_VERSION}')
        self.orientation.addItems(['0°', '90°', '180°', '270°'])
        for key, zh, en in [('screen', '设备屏幕', 'Screen'), ('camera', '摄像头', 'Camera')]:
            self.video_source_switcher.addItem(routeKey=key, text=self.t(zh, en))
        self.video_source_switcher.setCurrentItem('screen')
        self.video_source_stacked.setCurrentIndex(0)
        self.video_source_switcher.currentItemChanged.connect(self.on_video_source_change)
        self.get_devices_btn.clicked.connect(self.get_devices)
        self.restart_adb_btn.clicked.connect(self.restart_adb)
        self.adb_devices.itemSelectionChanged.connect(self.refresh_pro_page)
        self.camera_ids.currentIndexChanged.connect(self.on_camera_id_change)
        self.camera_sizes.currentIndexChanged.connect(self.on_camera_size_change)
        self.choice_record_output_path.clicked.connect(self.choose_record_folder)
        self.run_scrcpy.clicked.connect(self.run)
        self.pro_page.clicked.connect(self.toggle_pro)
        self.video_bit_slider.valueChanged.connect(self.update_video_bitrate)
        self.audio_bit_slider.valueChanged.connect(self.update_audio_bitrate)
        self.abort_pyqtscrcpy.clicked.connect(self.about)
        self.install_pyqtscrcpy.clicked.connect(self.component_versions)
        self.devices_manager.setVisible(sys.platform == 'win32')
        self.devices_manager.clicked.connect(self.open_device_manager)
        self.add_controls()
        self.record_output_path.setText(self.settings.value('record_folder', str(Path.home())))
        self.relabel()
        self.toggle_pro()
        QTimer.singleShot(0, self.get_devices)

    def t(self, zh, en):
        return zh if self.language == 'zh' else en

    def notify(self, title, content='', style='i'):
        info_bar(self, title, content, style, 7000, position='↓')

    def submit(self, function, callback, busy=False):
        task = Task(function, callback)
        self.tasks.add(task)
        if busy:
            self.busy_count += 1
            self.devices_card.setEnabled(False)
        # Receiver is a QObject slot on the GUI thread, even when task finishes instantly.
        task.signals.finished.connect(self.task_finished)
        task.busy = busy
        self.pool.start(task)

    def task_finished(self, callback, result, error):
        sender = self.sender()
        task = next((t for t in self.tasks if t.signals is sender), None)
        if task:
            if task.busy:
                self.busy_count -= 1
                self.devices_card.setEnabled(self.busy_count == 0)
            self.tasks.discard(task)
        callback(result, error)

    def selected_serial(self):
        items = self.adb_devices.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else ''

    def require_serial(self):
        serial = self.selected_serial()
        if not serial:
            self.notify(self.t('请先选择设备', 'Select a device first'), style='w')
        return serial

    def add_controls(self):
        self.install_apk_btn = PushButton(self.devices_card)
        self.wireless_btn = PushButton(self.devices_card)
        actions = QHBoxLayout()
        actions.addWidget(self.install_apk_btn)
        actions.addWidget(self.wireless_btn)
        self.verticalLayout.insertLayout(1, actions)
        self.install_apk_btn.clicked.connect(self.install_apk)
        self.wireless_btn.clicked.connect(self.wireless_dialog)
        self.language_box = ComboBox(self)
        self.language_box.addItems(['简体中文', 'English'])
        self.language_box.setCurrentIndex(0 if self.language == 'zh' else 1)
        self.horizontalLayout_13.addWidget(self.language_box)
        self.language_box.currentIndexChanged.connect(self.change_language)
        self.logs_btn = PushButton(self)
        self.horizontalLayout_13.addWidget(self.logs_btn)
        self.logs_btn.clicked.connect(self.show_logs)
        self.virtual_display = CheckBox(self.screen_page)
        self.virtual_size = LineEdit(self.screen_page)
        self.virtual_size.setPlaceholderText('1920x1080/420')
        self.virtual_app = LineEdit(self.screen_page)
        self.virtual_app.setPlaceholderText('org.mozilla.firefox')
        self.virtual_keep = CheckBox(self.screen_page)
        self.virtual_decorations = CheckBox(self.screen_page)
        self.virtual_decorations.setChecked(True)
        for widget in [self.virtual_display, self.virtual_size, self.virtual_app, self.virtual_keep, self.virtual_decorations]:
            self.verticalLayout_13.addWidget(widget)
        self.virtual_display.toggled.connect(self.toggle_virtual)
        self.toggle_virtual(False)
        self.log_dialog = QDialog(self)
        self.log_dialog.resize(800, 480)
        layout = QVBoxLayout(self.log_dialog)
        self.log_view = QPlainTextEdit(self.log_dialog)
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        layout.addWidget(self.log_view)

    def relabel(self):
        self.install_apk_btn.setText(self.t('安装 APK', 'Install APK'))
        self.wireless_btn.setText(self.t('无线连接', 'Wireless'))
        self.logs_btn.setText(self.t('运行日志', 'Logs'))
        self.install_pyqtscrcpy.setText(self.t('组件版本', 'Component versions'))
        self.virtual_display.setText(self.t('创建虚拟显示', 'Create virtual display'))
        self.virtual_keep.setText(self.t('关闭后保留应用', 'Keep apps on close'))
        self.virtual_decorations.setText(self.t('显示系统装饰', 'System decorations'))
        self.virtual_size.setToolTip(self.t('尺寸/DPI；留空使用主屏幕参数', 'Size/DPI; empty uses main display settings'))
        self.virtual_app.setToolTip(self.t('启动应用包名（可留空）', 'App package to start (optional)'))
        self.video_source_switcher.setItemText('screen', self.t('设备屏幕', 'Screen'))
        self.video_source_switcher.setItemText('camera', self.t('摄像头', 'Camera'))
        self.log_dialog.setWindowTitle(self.t('Scrcpy 运行日志', 'Scrcpy logs'))
        self.label_6.setText(self.t('摄像头捕获需要 Android 12+', 'Camera capture requires Android 12+'))
        self.enable_video.setToolTip('--no-video')
        self.enable_audio.setToolTip('--no-audio')
        self.setWindowTitle(f'{TOOL_NAME} {TOOL_VERSION}')

    def change_language(self, index):
        self.language = 'zh' if index == 0 else 'en'
        self.settings.setValue('language', self.language)
        app = QApplication.instance()
        if index:
            app.installTranslator(self.translator)
        else:
            app.removeTranslator(self.translator)
        # Designer retranslation also contains value labels: preserve user values.
        video, audio = self.video_bit.text(), self.audio_bit.text()
        self.retranslateUi(self)
        self.video_bit.setText(video)
        self.audio_bit.setText(audio)
        self.relabel()
        self.toggle_pro()

    def toggle_virtual(self, enabled):
        self.enable_target_screen.setEnabled(not enabled)
        for w in [self.virtual_size, self.virtual_app, self.virtual_keep, self.virtual_decorations]:
            w.setEnabled(enabled)

    def toggle_pro(self):
        self.pro_page_stacked.setVisible(self.pro_page.isChecked())
        self.setMaximumWidth(1250 if self.pro_page.isChecked() else 450)
        self.resize(1250 if self.pro_page.isChecked() else 450, 720)
        if self.pro_page.isChecked():
            self.refresh_pro_page()

    def get_devices(self):
        previous = self.selected_serial()
        def done(result, error):
            if error:
                self.notify(self.t('设备查询失败', 'Device discovery failed'), error, 'e')
                return
            connected, unauthorized, offline = result
            self.adb_devices.blockSignals(True)
            self.adb_devices.clear()
            for serial, model in connected.items():
                self.adb_devices.addItem(f'{model} | {serial}')
                item = self.adb_devices.item(self.adb_devices.count() - 1)
                item.setData(Qt.ItemDataRole.UserRole, serial)
                if serial == previous:
                    self.adb_devices.setCurrentItem(item)
            if not self.adb_devices.selectedItems() and len(connected) == 1:
                self.adb_devices.setCurrentRow(0)
            self.adb_devices.blockSignals(False)
            self.refresh_pro_page()
            if unauthorized or offline:
                self.notify(self.t('设备需要处理', 'Devices need attention'),
                            f'unauthorized: {", ".join(unauthorized)}; offline: {", ".join(offline)}', 'w')
            elif not connected:
                self.notify(self.t('未发现设备', 'No devices found'), self.t('连接设备并允许 USB 调试', 'Connect a device and allow USB debugging'), 'w')
        self.submit(util.devices, done, busy=True)

    def restart_adb(self):
        def restart():
            backend.run_tool('adb', ['kill-server'])
            return backend.run_tool('adb', ['start-server'])
        self.submit(restart, lambda result, error: self.operation_done(result, error, refresh=True), busy=True)

    def operation_done(self, result, error, refresh=False):
        self.notify(self.t('操作失败', 'Operation failed') if error else self.t('操作成功', 'Success'), error or result or '', 'e' if error else 'o')
        if refresh and not error:
            self.get_devices()

    def refresh_pro_page(self):
        self.query_generation += 1
        generation, serial = self.query_generation, self.selected_serial()
        self.camera_info = {}
        self.camera_ids.clear()
        self.camera_sizes.clear()
        self.camera_fps.clear()
        self.target_screen.clear()
        if not serial or not self.pro_page.isChecked():
            self.pro_page_stacked.setCurrentIndex(0)
            return
        self.pro_page_stacked.setCurrentWidget(self.refresh_page)
        source = self.video_source
        def query():
            return util.get_camera_sizes(serial) if source == 'camera' else util.get_display_ids(serial)
        def done(result, error):
            if generation != self.query_generation or serial != self.selected_serial():
                return
            self.pro_page_stacked.setCurrentWidget(self.main_pro_page)
            if error:
                self.notify(self.t('配置查询失败', 'Configuration query failed'), error, 'w')
            elif source == 'camera':
                self.camera_info = result
                self.camera_ids.addItems(list(result))
            else:
                self.target_screen.addItems(result)
        self.submit(query, done)

    def on_video_source_change(self, source):
        self.video_source = source
        self.video_source_stacked.setCurrentWidget(self.screen_page if source == 'screen' else self.camera_page)
        self.audio_source_mic.setChecked(source == 'camera')
        self.audio_source_output.setChecked(source == 'screen')
        self.enable_max_fps.setEnabled(source == 'screen')
        self.refresh_pro_page()

    def on_camera_id_change(self):
        self.camera_sizes.clear()
        self.camera_sizes.addItems(list(self.camera_info.get(self.camera_ids.currentText(), {})))

    def on_camera_size_change(self):
        self.camera_fps.clear()
        self.camera_fps.addItems(self.camera_info.get(self.camera_ids.currentText(), {}).get(self.camera_sizes.currentText(), []))

    def choose_record_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.t('选择录屏目录', 'Recording folder'), self.record_output_path.text())
        if folder:
            self.record_output_path.setText(folder)
            self.settings.setValue('record_folder', folder)

    def build_args(self, serial):
        args = [f'--serial={serial}']
        for name in ['stay_awake', 'turn_screen_off', 'power_off_on_close', 'no_control', 'always_on_top']:
            if getattr(self, name).isChecked():
                args.append('--' + name.replace('_', '-'))
        if self.enable_record.isChecked():
            folder = Path(self.record_output_path.text()).expanduser()
            if not folder.is_dir():
                raise ValueError(self.t('请选择有效录屏目录', 'Choose an existing recording folder'))
            filename = 'scrcpy-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.mkv'
            args.append(f'--record={folder / filename}')
            if self.record_time_limit.isChecked():
                args.append(f'--time-limit={util.time_to_seconds(self.record_limit_edit.text())}')
            if self.no_playback.isChecked():
                args.append('--no-playback')
        if self.pro_page.isChecked():
            if not self.enable_video.isChecked() and not self.enable_audio.isChecked():
                raise ValueError(self.t('至少启用视频或音频', 'Enable video or audio'))
            if self.enable_video.isChecked():
                if self.enable_orientation.isChecked():
                    args.append('--display-orientation=' + self.orientation.currentText().replace('°', ''))
                args.append(f'--video-buffer={self.video_buffer.value()}')
                if self.video_source == 'screen':
                    if self.enable_max_fps.isChecked():
                        args.append('--max-fps=' + backend.integer(str(self.max_fps.value()), 'FPS', 1))
                    if self.virtual_display.isChecked():
                        args += backend.virtual_display_args(self.virtual_size.text(), self.virtual_app.text(), self.virtual_keep.isChecked(), self.virtual_decorations.isChecked())
                    elif self.enable_target_screen.isChecked():
                        args.append('--display-id=' + backend.integer(self.target_screen.currentText(), 'Display ID'))
                    if self.enable_max_size.isChecked():
                        args.append('--max-size=' + backend.integer(str(self.max_size.value()), 'Maximum size', 1))
                else:
                    if not self.camera_ids.currentText() or not self.camera_sizes.currentText():
                        raise ValueError(self.t('请选择摄像头和分辨率', 'Select a camera and resolution'))
                    args += ['--video-source=camera', '--camera-id=' + self.camera_ids.currentText(), '--camera-size=' + self.camera_sizes.currentText().split()[0], '--camera-fps=' + backend.integer(self.camera_fps.currentText(), 'Camera FPS', 1)]
                    if '[high-speed]' in self.camera_sizes.currentText():
                        args.append('--camera-high-speed')
                codec = 'h265' if self.video_h265.isChecked() else 'av1' if self.video_av1.isChecked() else 'h264'
                args += [f'--video-codec={codec}', f'--video-bit-rate={util.convert_bitrate(self.video_bit.text())}']
            else:
                args.append('--no-video')
            if self.enable_audio.isChecked():
                codec = 'aac' if self.audio_aac.isChecked() else 'flac' if self.audio_flac.isChecked() else 'opus'
                source = 'mic' if self.audio_source_mic.isChecked() else 'output'
                args += [f'--audio-source={source}', f'--audio-buffer={self.audio_buffer.value()}', f'--audio-codec={codec}']
                if codec != 'flac':
                    args.append(f'--audio-bit-rate={util.convert_bitrate(self.audio_bit.text())}')
            else:
                args.append('--no-audio')
        if self.enable_cust_port.isChecked():
            args.append('--tunnel-port=' + backend.integer(str(self.cust_port.value()), 'Port', 1, 65535))
        if self.tcpip_connect.isChecked():
            args.append('--tcpip')
        return args

    def run(self):
        serial = self.require_serial()
        if not serial:
            return
        try:
            args = self.build_args(serial)
        except ValueError as exc:
            self.notify(self.t('参数错误', 'Invalid options'), str(exc), 'e')
            return
        self.run_scrcpy.setEnabled(False)
        def prepare():
            help_text = backend.run_tool('scrcpy', ['--help'])
            backend.check_capabilities(help_text, args)
            status = ''
            if '--no-control' not in args:
                status = backend.run_tool('adb', backend.adb_args(serial, 'shell', 'getprop', 'persist.security.adbinput'))
            return backend.resolve_tool('scrcpy'), backend.tool_env(), status
        def done(result, error):
            self.run_scrcpy.setEnabled(True)
            if error:
                self.notify(self.t('无法启动', 'Unable to start'), error, 'e')
                return
            executable, env, status = result
            if status.strip() == '0':
                self.notify(self.t('设备限制输入控制', 'Device restricts input control'), self.t('请在设备开发者选项中启用 USB 调试（安全设置），然后重试。', 'Enable USB debugging (Security settings) in device developer options.'), 'w')
            self.launch_scrcpy(executable, args, env)
        self.submit(prepare, done)

    def launch_scrcpy(self, executable, args, env):
        process = QProcess(self)
        process.setProgram(executable)
        process.setArguments(args)
        process.setWorkingDirectory(str(Path(executable).parent))
        qenv = QProcessEnvironment()
        for key, value in env.items():
            qenv.insert(key, value)
        process.setProcessEnvironment(qenv)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(lambda: self.log_view.appendPlainText(bytes(process.readAllStandardOutput()).decode('utf-8', 'replace').rstrip()))
        process.finished.connect(lambda code, status: self.process_finished(process, code))
        process.errorOccurred.connect(lambda error: self.process_error(process, error))
        self.processes.add(process)
        self.log_view.appendPlainText(f'\n[{datetime.datetime.now().isoformat(timespec="seconds")}] {executable}\n{args!r}')
        process.start()

    def process_error(self, process, error):
        self.notify(self.t('Scrcpy 进程错误', 'Scrcpy process error'), process.errorString(), 'e')
        if error == QProcess.ProcessError.FailedToStart:
            self.processes.discard(process)
            process.deleteLater()

    def process_finished(self, process, code):
        self.processes.discard(process)
        self.log_view.appendPlainText(f'Process exited: {code}')
        if code:
            self.notify(self.t('Scrcpy 已退出', 'Scrcpy exited'), self.t('请查看运行日志中的设备错误信息', 'Check the logs for device errors'), 'e')
            self.show_logs()
        process.deleteLater()

    def install_apk(self):
        serial = self.require_serial()
        if not serial:
            return
        path, _ = QFileDialog.getOpenFileName(self, self.t('选择 APK', 'Select APK'), '', 'APK (*.apk)')
        if path:
            self.submit(lambda: backend.install_apk(serial, path), self.operation_done, busy=True)

    def wireless_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.t('无线调试', 'Wireless debugging'))
        layout = QFormLayout(dialog)
        endpoint, pair_endpoint, code = QLineEdit(dialog), QLineEdit(dialog), QLineEdit(dialog)
        endpoint.setPlaceholderText('192.168.1.100:37000')
        endpoint.setText(self.settings.value('wireless_endpoint', ''))
        pair_endpoint.setPlaceholderText('192.168.1.100:37001')
        code.setEchoMode(QLineEdit.EchoMode.Password)
        code.setMaxLength(6)
        layout.addRow(self.t('连接地址 IP:端口', 'Connect IP:port'), endpoint)
        layout.addRow(self.t('配对地址（可选，端口通常不同）', 'Pair IP:port (optional, usually different)'), pair_endpoint)
        layout.addRow(self.t('配对码（可选）', 'Pairing code (optional)'), code)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        target, pair_target, secret = endpoint.text(), pair_endpoint.text(), code.text()
        code.clear()
        try:
            target = backend.validate_endpoint(target)
            if pair_target or secret:
                pair_target = backend.validate_endpoint(pair_target)
                if len(secret) != 6 or not secret.isascii() or not secret.isdigit():
                    raise ValueError(self.t('配对码必须为六位数字', 'Pairing code must contain six digits'))
        except ValueError as exc:
            self.notify(self.t('地址或配对码无效', 'Invalid endpoint or code'), str(exc), 'e')
            return
        self.settings.setValue('wireless_endpoint', target)
        def connect():
            if pair_target:
                backend.pair_device(pair_target, secret)
            return backend.connect_device(target)
        self.submit(connect, lambda result, error: self.operation_done(result, error, refresh=True), busy=True)

    def component_versions(self):
        def query():
            return '\n\n'.join(backend.run_tool(name, ['--version'] if name == 'scrcpy' else ['version']) for name in ['adb', 'scrcpy'])
        self.submit(query, lambda result, error: self.message(self.t('组件版本', 'Component versions'), error or result))

    def message(self, title, text):
        box = MessageBox(title, text, self)
        box.cancelButton.hide()
        box.yesButton.setText('OK')
        box.exec()

    def about(self):
        self.message(TOOL_NAME, f'{TOOL_VERSION}\n{TOOL_AUTHOR}\nGPL-3.0\nhttps://github.com/xiatian410/PyQtScrcpy\nUpstream: Stardawn0v0/PyQtScrcpy\nAPK feature: hansaes, upstream PR #7')

    def show_logs(self):
        self.log_dialog.show()
        self.log_dialog.raise_()

    def open_device_manager(self):
        if sys.platform == 'win32':
            os.startfile('devmgmt.msc')

    def update_audio_bitrate(self, value):
        choices = [(10, '32K'), (20, '64K'), (40, '128K'), (60, '256K'), (80, '512K'), (95, '1M'), (101, '2M')]
        self.audio_bit.setText(next(text for limit, text in choices if value < limit))

    def update_video_bitrate(self, value):
        bitrate = max(1, value) * 50
        self.video_bit.setText(f'{bitrate / 1000:.2f}M' if bitrate >= 1000 else f'{bitrate}K')

    def closeEvent(self, event):
        if self.tasks:
            self.notify(self.t('任务仍在执行', 'Tasks are still running'), self.t('请等待操作结束后关闭窗口', 'Wait for the current operation to finish'), 'w')
            event.ignore()
            return
        if self.processes:
            box = MessageBox(self.t('结束投屏', 'Stop mirroring'), self.t('关闭窗口将结束正在运行的投屏。', 'Closing this window stops active mirroring sessions.'), self)
            if not box.exec():
                event.ignore()
                return
            for process in list(self.processes):
                process.terminate()
                if not process.waitForFinished(1000):
                    process.kill()
                    process.waitForFinished(1000)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(TOOL_NAME)
    window = MainWindow()
    def exception_hook(kind, value, tb):
        output = ''.join(traceback.format_exception(kind, value, tb))
        folder = Path(DATA_PATH)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'error.log').write_text(output, encoding='utf-8')
        window.notify(window.t('程序发生错误', 'Application error'), str(value), 'e')
    sys.excepthook = exception_hook
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
