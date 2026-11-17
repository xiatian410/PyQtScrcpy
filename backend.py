"""Qt-independent process execution and validation for adb and scrcpy."""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def resolve_tool(name: str) -> str:
    override = os.environ.get(f"PYQTSCRCPY_{name.upper()}")
    if override:
        path = shutil.which(override)
        if path:
            return path
        raise FileNotFoundError(f"Invalid PYQTSCRCPY_{name.upper()}: {override}")
    filename = name + (".exe" if sys.platform == "win32" else "")
    # External bundles take precedence over embedded files (allows updates).
    roots = [Path(sys.executable).parent, ROOT] if getattr(sys, "frozen", False) else [ROOT]
    for root in roots:
        for folder in (root / "tools" / "platform-tools", root / "tools" / "scrcpy", root / "bin"):
            candidate = folder / filename
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f"{name} not found. Run: python scripts/update_components.py")


def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    # Device choice is always passed explicitly, never inherited from another app.
    env.pop("ANDROID_SERIAL", None)
    env["ADB"] = resolve_tool("adb")
    return env


def run_tool(name: str, args: list[str], *, timeout: int = 30, input_text: str | None = None) -> str:
    command = [resolve_tool(name), *args]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, input=input_text, env=tool_env(),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode:
        raise RuntimeError(output or f"{name} exited with code {result.returncode}")
    return output


def adb_args(serial: str, *args: str) -> list[str]:
    if not serial or serial.startswith("-") or any(c.isspace() for c in serial):
        raise ValueError("Select a connected device first")
    return ["-s", serial, *args]


def parse_devices(output: str) -> tuple[dict[str, str], list[str], list[str]]:
    connected, unauthorized, offline = {}, [], []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[:2]
        if state == "device":
            model = next((p[6:].replace("_", " ") for p in parts[2:] if p.startswith("model:")), serial)
            connected[serial] = model
        elif state == "unauthorized":
            unauthorized.append(serial)
        elif state == "offline":
            offline.append(serial)
    return connected, unauthorized, offline


def validate_endpoint(value: str) -> str:
    value = value.strip()
    if value.startswith("["):
        match = re.fullmatch(r"\[([^\]]+)\]:(\d+)", value)
        if not match:
            raise ValueError("Use [IPv6]:port")
        ipaddress.IPv6Address(match[1])
        port = match[2]
    else:
        match = re.fullmatch(r"([A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?):(\d+)", value)
        if not match:
            raise ValueError("Use IP:port or hostname:port")
        port = match[2]
    integer(port, "port", 1, 65535)
    return value


def pair_device(endpoint: str, code: str) -> str:
    endpoint = validate_endpoint(endpoint)
    if not re.fullmatch(r"[0-9]{6}", code):
        raise ValueError("Pairing code must contain six digits")
    # Keep the temporary code out of the process command line and error logs.
    try:
        output = run_tool("adb", ["pair", endpoint], input_text=code + "\n", timeout=60)
    except RuntimeError as exc:
        raise RuntimeError(str(exc).replace(code, "******")) from None
    output = output.replace(code, "******")
    if not re.search(r"Successfully paired", output, re.I):
        raise RuntimeError(output)
    return output


def connect_device(endpoint: str) -> str:
    output = run_tool("adb", ["connect", validate_endpoint(endpoint)], timeout=30)
    if not re.search(r"(?:already )?connected to", output, re.I):
        raise RuntimeError(output)
    return output


def install_apk(serial: str, filename: str) -> str:
    path = Path(filename).resolve()
    if path.suffix.lower() != ".apk" or not path.is_file():
        raise ValueError("Select an existing APK file")
    output = run_tool("adb", adb_args(serial, "install", "-r", str(path)), timeout=300)
    if not re.search(r"^Success\s*$", output, re.M):
        raise RuntimeError(output)
    return output


def integer(value: str, name: str, minimum: int = 0, maximum: int = 2**31 - 1) -> str:
    if not re.fullmatch(r"[0-9]+", value) or not minimum <= int(value) <= maximum:
        raise ValueError(f"{name}: {minimum} .. {maximum}")
    return str(int(value))


def virtual_display_args(size: str, app: str = "", keep: bool = False, decorations: bool = True) -> list[str]:
    size = size.strip()
    if size:
        match = re.fullmatch(r"(?:(\d+)x(\d+))?(?:/(\d+))?", size)
        if not match:
            raise ValueError("Virtual display: WIDTHxHEIGHT[/DPI], /DPI, or empty")
        for v in match.groups():
            if v is not None:
                integer(v, "virtual display", 1, 65535)
    args = ["--new-display" + (f"={size}" if size else "")]
    if app.strip():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+", app.strip()):
            raise ValueError("Enter an Android package name (e.g. org.mozilla.firefox)")
        args.append(f"--start-app={app.strip()}")
    if keep:
        args.append("--no-vd-destroy-content")
    if not decorations:
        args.append("--no-vd-system-decorations")
    return args


def check_capabilities(help_text: str, args: list[str]) -> None:
    supported = set(re.findall(r"--[a-z][a-z0-9-]*", help_text))
    missing = sorted({a.split("=", 1)[0] for a in args if a.startswith("--")} - supported)
    if missing:
        raise ValueError("Installed scrcpy does not support: " + ", ".join(missing) + ". Update scrcpy.")
