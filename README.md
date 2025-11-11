# ClickClick 🖱️⚡
Automated mouse clicker with a simple GUI, global hotkeys, and precise scheduling.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](requirements.txt) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](requirements.txt) [![Download](https://img.shields.io/badge/Download-Executable-brightgreen)](#download-executable)

---

## Download Executable

**For Windows users who don't want to install Python:**

📦 [Download ClickClick.exe from Releases](../../releases/latest)

- ✅ **Single-file executable** - no installation required
- ✅ **Portable** - run from anywhere (USB drive, Desktop, etc.)
- ✅ **No Python needed** - includes everything bundled inside
- ✅ **Just double-click to run** - it's that simple!

**File size:** ~15-20 MB (includes Python runtime + all dependencies)

---

## What is ClickClick?
ClickClick is a lightweight Python application that automates mouse clicks. It provides a friendly GUI, hotkey controls to start/stop, configurable intervals, and a clear status indicator so you can automate repetitive click tasks safely and efficiently.

Core components:
- GUI: [src/gui_window.py](src/gui_window.py)
- Hotkeys: [src/hotkey_handler.py](src/hotkey_handler.py)
- Mouse automation: [src/mouse_controller.py](src/mouse_controller.py)
- Scheduling: [src/click_scheduler.py](src/click_scheduler.py)
- Status indicator: [src/status_indicator.py](src/status_indicator.py)
- Configuration: [src/config.py](src/config.py)

---

## Features
- Intuitive GUI to configure click behavior and intervals
- Global hotkeys to quickly start/stop automation
- Precise scheduling for consistent timing
- Visual status indicator for real-time feedback
- Test coverage for core mouse automation ([tests/test_mouse_controller.py](tests/test_mouse_controller.py))

---

## Prerequisites
- Python 3.8 or newer
- OS: Windows, Linux, or macOS
- Project dependencies listed in [requirements.txt](requirements.txt)
- On macOS and some Linux environments, you may need accessibility/input permissions for global hotkeys and mouse control

---

## Installation

### Option 1: Download Executable (Windows - No Python Required)

1. Go to the [Releases page](../../releases/latest)
2. Download `ClickClick.exe`
3. Double-click to run - that's it! 🎉

### Option 2: Run from Source (All Platforms)

Use a virtual environment (recommended) and install dependencies.

**Windows (cmd):**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux (bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Quickstart

### Using the Executable
1. Download and double-click `ClickClick.exe`
2. Configure click interval and behavior in the GUI
3. Use the global hotkey (Numpad 5) to start/stop automated clicking
4. Watch the status indicator overlay to confirm the current state

### Running from Source
Run the application from the project root:
```bash
python -m src.main
```

**Basic usage:**
1. Launch the app
2. Configure click interval and behavior in the GUI
3. Use the global hotkey to start/stop automated clicking
4. Watch the status indicator to confirm the current state

**Notes:**
- Default hotkeys and other options are defined in [`config.py`](src/config.py)
- Settings are saved to `settings.json` in your project directory

---

## Configuration
Adjust defaults in [src/config.py](src/config.py). Typical options include:
- Click interval and scheduling
- Hotkey bindings
- Click type and behavior

---

## Testing
Run the test suite with pytest:
```bash
pytest
```
Example targeted run:
```bash
pytest tests/test_mouse_controller.py
```

---

## Project Structure
```
clickclick/
├─ src/
│  ├─ __init__.py
│  ├─ main.py              # Entry point
│  ├─ gui_window.py        # GUI interface
│  ├─ hotkey_handler.py    # Hotkey management
│  ├─ mouse_controller.py  # Mouse automation
│  ├─ click_scheduler.py   # Timing and scheduling
│  ├─ status_indicator.py  # Visual feedback
│  └─ config.py            # Configuration
├─ tests/
│  ├─ conftest.py
│  └─ test_mouse_controller.py
└─ requirements.txt
```

---

## Building Executable

Want to build your own executable? See [BUILD.md](BUILD.md) for detailed instructions.

**Quick build:**
```bash
pip install -r requirements-dev.txt
build.bat
```

This creates a portable `ClickClick.exe` file you can distribute.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License
Not detected. Consider adding a LICENSE file to clarify usage and distribution.