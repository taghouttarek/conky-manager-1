# Conky Manager

A full-featured Python/Tkinter GUI for managing Conky themes on Linux.

## Features

- **Theme Discovery** - Automatically scans `~/.config/conky/` for themes
- **Theme Switching** - Activate/deactivate themes with one click
- **Multi-Theme Support** - Run multiple themes simultaneously
- **Multi-Select** - Select and operate on multiple themes at once (Ctrl+Click / Shift+Click)
- **Run/Stop/Restart** - Start, stop, or restart selected themes
- **Restart All** - Restart all running themes at once
- **Archive Import** - Import themes from zip, tar, tar.gz, tar.xz, 7z
- **Folder Import** - Import themes directly from local folders
- **Autostart** - Configure themes to start on login via `.desktop` entries
- **Layout Editor** - Drag-and-drop interface for positioning widgets with zoom controls
- **Auto-Update** - Check for updates from git repo, backup and apply automatically
- **Theme Editing** - Edit theme configs directly from the manager
- **Theme Deletion** - Remove unused themes (multi-select supported)
- **Dark Icon Style** - All widgets use consistent dark icon styling

## Included Themes

### System Widgets
| Theme | Description |
|-------|-------------|
| `network-conky-manager` | Network info (interface, local/external IP) |
| `bandwidth-conky-manager` | Download/upload speed |
| `processes-conky-manager` | Top 10 processes by CPU |
| `docker-conky-manager` | Running Docker containers |
| `k8s-conky-manager` | Kubernetes context, namespace, nodes |

### Monitoring
| Theme | Description |
|-------|-------------|
| `crypto-conky-manager` | Cryptocurrency prices with 7-day chart (default: SOL) |
| `kev-conky-manager` | CISA Known Exploited Vulnerabilities feed |
| `infra-conky-manager` | Infrastructure CVEs (k8s, docker, postgres, redis, etc.) |
| `weather-conky-manager` | Weather display with OpenWeatherMap API |

### Desktop Widgets
| Theme | Description |
|-------|-------------|
| `calendar-conky-manager` | Calendar with circular design |
| `revisited-conky-manager` | Revisited desktop widgets (circle/square, horizontal/vertical) |
| `claude-conky-manager` | Claude-themed ring widgets |

## Installation

### Option 1: .deb Package (Recommended)

```bash
# Download and install
sudo dpkg -i conky-manager_2.0.4_all.deb
sudo apt install -f  # Fix dependencies if needed
```

### Option 2: Install Script

```bash
git clone https://github.com/taghouti-org/conky-manager.git
cd conky-manager
sudo bash install.sh
```

### Option 3: Manual Install

```bash
# Install dependencies
sudo apt install conky python3-tk lua5.3 git

# Clone and install
git clone https://github.com/taghouti-org/conky-manager.git
cd conky-manager

# Copy to /opt
sudo cp -r . /opt/conky-manager

# Create launcher
mkdir -p ~/.local/bin
cat > ~/.local/bin/conky-manager << 'EOF'
#!/bin/bash
exec python3 "/opt/conky-manager/conky_manager.py" "$@"
EOF
chmod +x ~/.local/bin/conky-manager

# Copy themes
cp -r themes/*-conky-manager ~/.config/conky/

# Create desktop entry
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/conky-manager.desktop << EOF
[Desktop Entry]
Name=Conky Manager
Exec=~/.local/bin/conky-manager
Icon=conky-manager
Terminal=false
Type=Application
Categories=Utility;System;
EOF
```

### Dependencies

```bash
# Required
sudo apt install conky python3-tk lua5.3 git

# Optional (for specific themes)
pip3 install pyowm  # Weather theme
sudo apt install lm-sensors  # Calendar theme
```

## Usage

```bash
# Launch the GUI
conky-manager

# Or run directly
python3 /opt/conky-manager/conky_manager.py
```

### Manager Features

- **Run Theme** - Start selected theme(s)
- **Stop Theme** - Stop selected theme(s)
- **Restart Theme** - Restart selected theme(s)
- **Stop All** - Stop all running themes
- **Restart** - Restart all running themes
- **Layout** - Open drag-and-drop layout editor
- **Update** - Check for and apply updates from git repo
- **Restart Manager** - Restart the manager application

### Layout Editor

The layout editor provides a visual interface for positioning widgets:

- **Move Mode** - Drag widgets to reposition
- **Resize Mode** - Drag corners to resize
- **Zoom +/-** - Zoom in/out for precision
- **Save** - Save positions to layout.json
- **Apply** - Update gap_x/gap_y in conkyrc AND x/y in settings.lua, then restart themes

### Auto-Update

The manager automatically checks for updates on startup:
- Compares local version with remote VERSION file
- Shows "Update (NEW)" button when updates available
- Backs up current installation before applying
- Updates manager files and all themes

## Conky 1.19 Compatibility

This manager supports Conky 1.19+ with Lua-based configuration:

```lua
conky.config = {
    background = false,
    update_interval = 1,
    own_window = true,
    own_window_type = 'normal',
    font = 'Dejavu Sans:size=10',
    minimum_width = 300,
    minimum_height = 200,
}

conky.text = [[
${cpu}%
]]
```

### Deprecated Syntax (do not use)

- `xftfont` → use `font`
- `minimum_size W H` → use `minimum_width = W,` and `minimum_height = H,`

## Unified Widget Positioning

All themes use the same positioning model:

1. **Fullscreen window** (1920x1080) with `alignment = 'top_left'`, `gap_x = 0`, `gap_y = 0`
2. **Absolute screen coordinates** in Lua (`local x = N`, `local y = N`)
3. **Layout editor** updates both `gap_x`/`gap_y` in conkyrc and `x`/`y` in settings.lua
4. **Auto-restart** after applying positions so changes take effect

This ensures the same logic works for all themes (system widgets, calendar, weather, revisited, etc.).

## Testing

Non-regression test suite with 70 tests covering theme structure, Lua syntax, business logic, and layout editor.

```bash
# Install test dependencies
pip3 install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_theme_structure.py -v
pytest tests/test_lua_syntax.py -v
pytest tests/test_layout_editor.py -v
pytest tests/test_conky_manager.py -v
```

## Uninstall

```bash
# Using uninstall script
sudo bash /opt/conky-manager/uninstall.sh

# Or using .deb
sudo dpkg -r conky-manager
```

## File Locations

| Path | Description |
|------|-------------|
| `/opt/conky-manager/` | Installation directory |
| `~/.config/conky/` | Theme configurations |
| `~/.local/share/conky-manager/` | Manager data and backups |
| `~/.local/bin/conky-manager` | Launcher script |
| `~/.local/share/applications/conky-manager.desktop` | Desktop entry |

## License

MIT License
