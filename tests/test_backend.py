import subprocess
from unittest.mock import patch

import pytest

import backend
import util
from scripts.update_components import safe_member, extract


def test_devices_include_all_states_and_models():
    text = 'List of devices attached\nabc device product:p model:Pixel_9 transport_id:1\nother unauthorized\n192.168.1.3:5555 offline\n'
    assert backend.parse_devices(text) == ({'abc': 'Pixel 9'}, ['other'], ['192.168.1.3:5555'])


@pytest.mark.parametrize('value', ['192.168.1.2:5555', 'phone.local:32100', '[::1]:5555'])
def test_endpoint(value):
    assert backend.validate_endpoint(value) == value


@pytest.mark.parametrize('value', ['host:0', 'host:65536', 'host', '-x:123', 'a;touch b:123', '::1:123', 'x:12\n--help', '[xx]:123'])
def test_bad_endpoint(value):
    with pytest.raises(ValueError):
        backend.validate_endpoint(value)


def test_apk_uses_selected_device_and_literal_path(tmp_path):
    apk = tmp_path / '中文 & $(echo test).apk'
    apk.touch()
    with patch('backend.run_tool', return_value='Success') as run:
        backend.install_apk('device-B', str(apk))
    assert run.call_args.args == ('adb', ['-s', 'device-B', 'install', '-r', str(apk)])
    assert run.call_args.kwargs['timeout'] == 300


def test_adb_failure_even_when_exit_code_zero():
    with patch('backend.run_tool', return_value='failed to connect'):
        with pytest.raises(RuntimeError):
            backend.connect_device('phone:5555')


def test_pair_code_is_not_in_argv():
    with patch('backend.run_tool', return_value='Successfully paired') as run:
        backend.pair_device('phone:33333', '123456')
    assert run.call_args.args == ('adb', ['pair', 'phone:33333'])
    assert run.call_args.kwargs['input_text'] == '123456\n'


def test_pair_failure_redacts_code_and_does_not_accept_error_output():
    with patch('backend.run_tool', side_effect=RuntimeError('invalid code 123456')):
        with pytest.raises(RuntimeError, match=r'invalid code \*{6}'):
            backend.pair_device('phone:33333', '123456')
    with patch('backend.run_tool', return_value='Failed to pair'):
        with pytest.raises(RuntimeError, match='Failed to pair'):
            backend.pair_device('phone:33333', '123456')


def test_tool_environment_does_not_inherit_device_selection(monkeypatch):
    monkeypatch.setenv('ANDROID_SERIAL', 'wrong-device')
    with patch('backend.resolve_tool', return_value='/tools/adb'):
        environment = backend.tool_env()
    assert 'ANDROID_SERIAL' not in environment
    assert environment['ADB'] == '/tools/adb'


def test_virtual_display_options():
    assert backend.virtual_display_args('1920x1080/420', 'org.mozilla.firefox', True, False) == [
        '--new-display=1920x1080/420', '--start-app=org.mozilla.firefox',
        '--no-vd-destroy-content', '--no-vd-system-decorations']
    assert backend.virtual_display_args('') == ['--new-display']
    assert backend.virtual_display_args('/240') == ['--new-display=/240']


@pytest.mark.parametrize('size', ['0x1080', '1920x', '/0', 'abc', '12x12/3 --help'])
def test_invalid_virtual_display(size):
    with pytest.raises(ValueError):
        backend.virtual_display_args(size)


def test_capability_gate():
    backend.check_capabilities('--serial value --video-buffer=ms', ['--serial=A', '--video-buffer=0'])
    with pytest.raises(ValueError, match='--new-display'):
        backend.check_capabilities('--serial', ['--new-display'])


def test_command_timeout_decoding_and_no_shell():
    with patch('backend.resolve_tool', return_value='/tools/adb'), patch('backend.tool_env', return_value={}), patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'ok', '')) as run:
        assert backend.run_tool('adb', ['devices']) == 'ok'
    assert run.call_args.args[0] == ['/tools/adb', 'devices']
    assert run.call_args.kwargs['timeout'] == 30
    assert run.call_args.kwargs['encoding'] == 'utf-8'
    assert not run.call_args.kwargs.get('shell', False)


def test_camera_parser_empty_and_high_speed():
    assert util.parse_camera_sizes('No camera found') == {}
    cameras = util.parse_camera_sizes('''--camera-id=external-0 (back, 4000x3000, fps=[15, 30])
    - 1920x1080
    High speed capture (--camera-high-speed):
    - 1280x720 (fps=[120, 240])''')
    assert cameras['external-0']['1920x1080'] == ['15', '30']
    assert cameras['external-0']['1280x720 [high-speed]'] == ['120', '240']


@pytest.mark.parametrize('value', ['00:00:00', '00:60:00', 'bad', '00:00:99'])
def test_invalid_duration(value):
    with pytest.raises(ValueError):
        util.time_to_seconds(value)


def test_duration_and_bitrate():
    assert util.time_to_seconds('01:02:03') == 3723
    assert util.convert_bitrate('2.50 M') == 2500000


@pytest.mark.parametrize('name', ['../x', '/etc/passwd', 'C:/x', '..\\x'])
def test_archive_path_rejected(name):
    with pytest.raises(ValueError):
        safe_member(name)


def test_archive_traversal_does_not_extract(tmp_path):
    import zipfile
    path = tmp_path / 'bad.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('../escaped', 'bad')
    with pytest.raises(ValueError):
        extract(path, tmp_path / 'out')
    assert not (tmp_path / 'escaped').exists()
