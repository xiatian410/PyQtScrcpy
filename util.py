"""Device discovery and scrcpy output parsing, independent from Qt."""
import re

from backend import parse_devices, run_tool


def devices():
    return parse_devices(run_tool('adb', ['devices', '-l']))


def get_display_ids(device_id):
    output = run_tool('scrcpy', ['--serial', device_id, '--list-displays'])
    return list(dict.fromkeys(re.findall(r'--display-id=(\d+)', output)))


def parse_camera_sizes(output):
    cameras = {}
    current = None
    fps = []
    high_speed = False
    for line in output.splitlines():
        line = line.strip()
        match = re.search(r'--camera-id=([^\s]+).*fps=\[([^]]*)\]', line)
        if match:
            current = match[1]
            fps = [v.strip() for v in match[2].split(',') if v.strip()]
            cameras[current] = {}
            high_speed = False
        elif 'High speed capture' in line:
            high_speed = True
        elif current is not None:
            size = re.match(r'-\s*(\d+x\d+)(?:\s*\(fps=\[([^]]*)\]\))?', line)
            if size:
                values = [v.strip() for v in size[2].split(',')] if size[2] else fps
                cameras[current][size[1] + (' [high-speed]' if high_speed else '')] = values
    return cameras


def get_camera_sizes(device_id):
    return parse_camera_sizes(run_tool('scrcpy', ['--serial', device_id, '--list-camera-sizes']))


def time_to_seconds(time_str):
    if not re.fullmatch(r'\d{2}:\d{2}:\d{2}', time_str):
        raise ValueError('Time must use HH:mm:ss')
    h, m, s = map(int, time_str.split(':'))
    if m > 59 or s > 59 or h * 3600 + m * 60 + s == 0:
        raise ValueError('Duration must be positive; minutes and seconds must be below 60')
    return h * 3600 + m * 60 + s


def convert_bitrate(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([KM]?)', value.strip().upper())
    if not match:
        raise ValueError('Invalid bitrate')
    rate = int(float(match[1]) * {'': 1, 'K': 1000, 'M': 1000000}[match[2]])
    if rate <= 0:
        raise ValueError('Bitrate must be positive')
    return rate
