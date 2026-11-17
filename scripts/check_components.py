"""Print the actual binaries and versions selected by the application."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import resolve_tool, run_tool

for name, flag in [('adb', 'version'), ('scrcpy', '--version')]:
    print(resolve_tool(name))
    print(run_tool(name, [flag]))
