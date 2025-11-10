# ClickClick - Python Autoclicker

A minimal, cross-platform Python desktop application for automated mouse clicking with realistic human-like behavior simulation and visual status indication.

## 📋 Project Overview

ClickClick is a lightweight autoclicker tool designed to automate repetitive clicking tasks while simulating natural human clicking patterns. The application features a minimal GUI overlay that provides visual feedback on the clicking status, making it easy to know when the autoclicker is active.

## ✨ Core Features (MVP)

- **Hotkey Toggle Control**: Press **Numpad 5** (customizable) to start/stop the autoclicker
- **Visual Status Indicator**: Small circular overlay (30x30px) in screen corner
  - 🔴 Red = Stopped/Inactive
  - 🟢 Green = Running/Active
- **Position Locking**: Captures and locks onto mouse position when activated
- **Randomized Click Timing**: Random delays between 1-3 seconds to simulate human behavior
- **Position Randomization**: Small random offsets (±3 pixels on X and Y axis) for natural variation
- **Left-Click Only**: Performs standard left mouse button clicks
- **Silent Operation**: Graceful error handling with no intrusive error messages
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## 🛠️ Technology Stack

**Core Libraries:**
- **PyAutoGUI** - Mouse control and clicking operations
- **pynput** - Keyboard hotkey listening and event handling
- **tkinter** (built-in) - Minimal GUI overlay for status indicator
- **random** (built-in) - Randomization logic for delays and offsets

**Python Version:**
- Python 3.8 or higher

## 💻 System Requirements

- **Operating Systems**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 50 MB minimum
- **Display**: Any resolution (indicator will position in screen corner)
- **Permissions**: 
  - Windows: No special permissions required
  - macOS: Accessibility permissions for keyboard/mouse control
  - Linux: X11 or Wayland display server

## 📦 Installation Instructions

*Installation instructions will be provided after implementation.*

Basic steps will include:
1. Clone or download the repository
2. Install Python 3.8+ if not already installed
3. Install required dependencies via pip: `pip install -r requirements.txt`
4. Run the application: `python src/main.py`

## 🚀 Usage Instructions

*Detailed usage instructions will be provided after implementation.*

Basic usage workflow:
1. Run the application - a small red circular indicator will appear in the corner of your screen
2. Position your mouse cursor at the desired click location
3. Press **Numpad 5** to activate - the indicator turns green and the position is locked
4. The application will automatically click at the locked position with randomized timing and small offsets
5. Press **Numpad 5** again to stop - the indicator turns red
6. Press **Ctrl+C** in the terminal or close the indicator window to exit completely

## ⚙️ Configuration

The application includes customizable settings in [`config.py`](src/config.py):

- **Hotkey**: Default is Numpad 5, easily changeable
- **Click Delay Range**: Default 1-3 seconds
- **Position Offset Range**: Default ±3 pixels
- **Indicator Size**: Default 30x30 pixels
- **Indicator Position**: Corner placement (configurable)

## 🏗️ Architecture

For detailed technical architecture, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

Key architectural components:
- Modular design with separated concerns
- Event-driven hotkey system
- Thread-safe state management
- Minimal GUI overlay with tkinter
- Cross-platform compatibility layer

## 🔮 Future Extensibility

This MVP is designed with modularity in mind to support future enhancements:

### Planned Features (Post-MVP)
- **Enhanced GUI**: Full settings window with controls
- **Multiple Click Types**: Right-click, double-click, middle-click support
- **Click Profiles**: Save/load different configuration profiles
- **Multiple Hotkeys**: Different hotkeys for different click types
- **Click Patterns**: Sequential clicking at multiple positions
- **Recording Mode**: Record and playback click sequences
- **Advanced Randomization**: Configurable randomization algorithms
- **Statistics**: Track clicks, uptime, and usage patterns
- **Hotkey Customization UI**: In-app hotkey configuration
- **Portable Executable**: Standalone .exe for Windows

### Extension Points
- **Plugin System**: For custom click behaviors
- **API Interface**: For programmatic control
- **Scripting Support**: For complex automation scenarios
- **Multi-monitor Support**: Position indicators per monitor

## 📝 Project Structure

```
clickclick/
├── README.md                 # This file
├── ARCHITECTURE.md          # Technical architecture documentation
├── requirements.txt         # Python dependencies
├── src/
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration constants
│   ├── hotkey_handler.py   # Hotkey listening logic
│   ├── mouse_controller.py # Mouse click operations
│   ├── click_scheduler.py  # Click timing and coordination
│   └── status_indicator.py # GUI status overlay
└── tests/
    └── (future test files)
```

## 🤝 Contributing

*Contribution guidelines will be added after MVP completion.*

## 📄 License

*License information will be added.*

## ⚠️ Disclaimer

This tool is intended for legitimate automation tasks. Users are responsible for ensuring compliance with the terms of service of any applications or games where this tool is used. Misuse of automation tools may violate terms of service or applicable laws.

## 🐛 Known Limitations (MVP)

- Single click position per session
- Console must remain open during operation
- No click history or logging
- Limited error feedback (silent failures)

These limitations are intentional for the MVP and will be addressed in future releases.

---

**Version**: 1.0.0-MVP  
**Status**: Architecture Phase  
**Last Updated**: 2025-11-10