# ClickClick 🖱️⚡
Automated mouse clicker with a simple GUI, global hotkeys, and precise scheduling.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](requirements.txt) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](requirements.txt)

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
Use a virtual environment (recommended) and install dependencies.

Windows (cmd):
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux (bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Quickstart
Run the application from the project root:
```bash
python -m src.main
```

Basic usage:
1. Launch the app.
2. Configure click interval and behavior in the GUI.
3. Use the global hotkey to start/stop automated clicking.
4. Watch the status indicator to confirm the current state.

Notes:
- Default hotkeys and other options are defined in [src/config.py](src/config.py) and implemented via [src/hotkey_handler.py](src/hotkey_handler.py).

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

## License
Not detected. Consider adding a LICENSE file to clarify usage and distribution.