# Build a directory bundle so native components can be replaced independently.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
for component in ['scrcpy', 'platform-tools']:
    if not (root / 'tools' / component).is_dir():
        raise SystemExit('Run python scripts/update_components.py before building')
datas = collect_data_files('qfluentwidgets') + [
    (str(root / 'tools' / 'scrcpy'), 'tools/scrcpy'),
    (str(root / 'tools' / 'platform-tools'), 'tools/platform-tools'),
    (str(root / 'LICENSE'), '.'),
    (str(root / 'docs' / 'THIRD_PARTY.md'), '.'),
    (str(root / 'components.lock.json'), '.'),
]
a = Analysis(['main.py'], pathex=[str(root)], binaries=[], datas=datas,
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['PyQt5', 'PySide2', 'PySide6'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PyQtScrcpy',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'res' / 'logo.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PyQtScrcpy')
