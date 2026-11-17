import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
import time
from unittest.mock import patch
import pytest
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QApplication

from main import MainWindow


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.fixture
def window(app, tmp_path):
    with patch.object(MainWindow, 'get_devices'), patch.object(MainWindow, 'refresh_pro_page'):
        w = MainWindow()
        app.processEvents()
    w.record_output_path.setText(str(tmp_path))
    yield w
    app.removeTranslator(w.translator)
    w.close()
    w.deleteLater()
    app.processEvents()


def test_args_record_serial_and_modern_flags(window):
    window.enable_record.setChecked(True)
    window.always_on_top.setChecked(True)
    window.pro_page.setChecked(True)
    window.enable_orientation.setChecked(True)
    window.virtual_display.setChecked(True)
    window.virtual_size.setText('1920x1080/420')
    args = window.build_args('serial-B')
    assert '--serial=serial-B' in args
    assert '--always-on-top' in args
    assert '--display-orientation=0' in args
    assert '--video-buffer=0' in args
    assert '--new-display=1920x1080/420' in args
    recording = next(a.split('=', 1)[1] for a in args if a.startswith('--record='))
    assert Path(recording).suffix == '.mkv'
    assert Path(recording).parent.is_dir()
    assert '"' not in recording


def test_language_switch_preserves_values(window):
    window.video_bit.setText('8M')
    window.change_language(1)
    assert window.get_devices_btn.text() == 'Refresh devices'
    assert window.video_bit.text() == '8M'
    window.change_language(0)
    assert window.get_devices_btn.text() == '刷新设备列表'


def test_empty_camera_selection_safe(window):
    window.camera_info = {}
    window.camera_ids.clear()
    window.on_camera_id_change()
    window.on_camera_size_change()
    assert window.camera_fps.count() == 0


def test_background_failure_recovers_on_gui_thread(window, app):
    received = []
    def fail():
        raise RuntimeError('adb timeout')
    window.submit(fail, lambda result, error: received.append((error, QThread.currentThread())), busy=True)
    deadline = time.monotonic() + 5
    while not received and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert received == [('adb timeout', app.thread())]
    assert window.devices_card.isEnabled()
    assert not window.tasks


def test_stale_device_query_ignored(window, app):
    window.pro_page.setChecked(True)
    window.adb_devices.blockSignals(True)
    window.adb_devices.addItem('A')
    window.adb_devices.item(0).setData(Qt.ItemDataRole.UserRole, 'A')
    window.adb_devices.setCurrentRow(0)
    window.adb_devices.blockSignals(False)
    callbacks = []
    with patch.object(window, 'submit', side_effect=lambda fn, cb: callbacks.append(cb)):
        window.refresh_pro_page()
        window.adb_devices.blockSignals(True)
        window.adb_devices.clear()
        window.adb_devices.blockSignals(False)
        window.refresh_pro_page()
    callbacks[0](['99'], None)
    assert window.target_screen.count() == 0


def test_visible_numeric_input_and_icon(window, app):
    window.pro_page.setChecked(True)
    window.toggle_pro()
    window.show()
    app.processEvents()
    assert window.video_buffer.lineEdit().width() > 20
    assert window.record_limit_edit.lineEdit().width() > 40
    assert not window.windowIcon().isNull()


def test_options_accepted_by_installed_scrcpy(window):
    import backend
    try:
        backend.resolve_tool('scrcpy')
        backend.resolve_tool('adb')
    except FileNotFoundError:
        pytest.skip('Native tools are not installed')
    window.pro_page.setChecked(True)
    window.virtual_display.setChecked(True)
    window.virtual_app.setText('org.mozilla.firefox')
    window.virtual_keep.setChecked(True)
    window.virtual_decorations.setChecked(False)
    window.enable_record.setChecked(True)
    backend.check_capabilities(backend.run_tool('scrcpy', ['--help']), window.build_args('test-device'))
