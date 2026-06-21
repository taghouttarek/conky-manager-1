# Conky Manager - Agent Instructions

## Overview
This is a Conky theme manager repository containing:
- `conky_manager.py` - Main manager application (Python/Tkinter)
- `layout_editor.py` - Drag-and-drop layout editor for widget positioning
- `themes/` - All conky themes
- `tests/` - Non-regression test suite (70 tests)
- `install.sh` / `uninstall.sh` - Installation scripts

## Key Rules

### Always Persist Changes
Any fix, modification, or new theme applied to the system MUST be committed back to this repo:
- Config fixes (path corrections, syntax updates, compatibility patches)
- New themes added to `themes/` directory
- Manager code changes (new features, bug fixes)
- Lua script fixes

### Theme Locations
- **Repo**: `themes/<theme-name>/`
- **System**: `~/.config/conky/<theme-name>/`
- Install script copies from repo to system

### Manager Location
- **Repo**: `conky_manager.py`
- **System**: `~/.local/share/conky-manager/conky_manager.py`

## Architecture

### conky_manager.py
- Scans `~/.conky/` and `~/.config/conky/` for themes
- Detects themes by config files: `.conkyrc`, `conkyrc`, `*.conf`, `config.conf`, `conky.conf`
- If theme uses non-standard config name, create a `conkyrc` symlink in theme root
- Supports running multiple themes simultaneously
- Each theme runs as separate conky process

### Theme Structure
```
themes/<theme-name>/
├── conkyrc              # Symlink or actual config (required for manager detection)
├── settings.lua         # Lua settings (if theme uses lua)
├── *.lua                # Lua scripts
├── PNG/                 # Image assets (if any)
└── start_conky          # Actual config file (conky 1.19 syntax)
```

## Conky 1.19 Compatibility

### Config Syntax (Lua format required)
```lua
conky.config = {
    background = false,
    update_interval = 1,
    own_window = true,
    own_window_type = 'normal',
    font = 'Dejavu Sans:size=10',
    minimum_width = 300,
    minimum_height = 200,
    -- NO: xftfont, minimum_size (old syntax)
}

conky.text = [[
${cpu}%
]]
```

### Deprecated Settings (do NOT use)
- `xftfont` → use `font`
- `minimum_size W H` → use `minimum_width = W,` and `minimum_height = H,`
- Old syntax (`background no`) → use Lua format (`background = false,`)

### Lua Requirements
- Use `tonumber()` when parsing conky exec output for arithmetic
- Example: `local val = tonumber(conky_parse('${exec command}')) or 0`

## Fix History

### Multi-Theme Support
- Added `start_conky()`, `stop_theme()`, `stop_conky()`, `is_theme_running()`
- Manager no longer kills all conky before starting a new theme
- Tracks running themes in settings.json

### Path Corrections
- All themes moved from `~/.conky/` to `~/.config/conky/`
- Updated `lua_load` paths in all configs
- Updated `openweather.py` paths in weather settings.lua
- Updated `draw_weather_icon` PNG path in settings.lua

### Conky-Calendar-Extra Fixes
- Converted from old conky syntax to 1.19 Lua format
- Fixed `xftfont` → `font`
- Fixed `minimum_size` → `minimum_width/height`
- Added `tonumber()` for elements parameter in `create_circle()`
- Added nil check for temperature values in `vertical_bars()`

### Conky-Weather Fixes
- Updated API key, city, country in settings.lua
- Fixed PNG path from `~/.conky/` to `~/.config/conky/`

### Unified Widget Positioning (v2.0.4)
- All themes use fullscreen windows (1920x1080) with `gap_x = 0`, `gap_y = 0`
- Content positioned with absolute screen coordinates in Lua (`local x = N`, `local y = N`)
- Removed window-relative positioning (`w - N`, `(h - widget_h) / 2`)
- Layout editor updates both conkyrc (`gap_x`/`gap_y`) and settings.lua (`x`/`y`)
- Layout editor resolves symlinks before writing
- Layout editor scans all `.lua` files in theme dir for position variables
- Auto-restart themes after applying positions

### Code Review Fixes (v2.0.4)
- Fixed `hex2rgb()` blue channel bug across all 9 themes (was dividing string by 255)
- Added `os.setlocale("en_US.utf8", "numeric")` to 5 missing files
- Fixed `update_num` nil dereference in 7 files (crashes on first conky update)
- Fixed weather theme: `io.popen` leak → `os.getenv("HOME")`, nil concatenation guards
- Fixed weather theme: global variables (`ct`, `day`) → local, memory leak in `cairo_text_extents_t`
- Fixed docker theme: `size * 05` typo → `size * 0.05`
- Layout editor: error handling per-theme, PID validation, file write guard (only writes when changed)
- Layout editor: atomic file writes, UTF-8 encoding, corrupted JSON handling
- Removed hardcoded developer path from `get_repo_path()`

## Adding New Themes

1. Place theme in `themes/<theme-name>/`
2. Create `conkyrc` symlink pointing to actual config:
   ```bash
   cd themes/<theme-name>
   ln -sf actual_config_file conkyrc
   ```
3. If theme uses Lua, ensure paths are absolute or use `~/.config/conky/`
4. Convert old conky syntax to 1.19 Lua format if needed
5. Test with: `conky -c themes/<theme-name>/<config-file>`
6. Commit to repo

## Running Conky Manually

```bash
# Start single theme
conky -c ~/.config/conky/<theme-name>/<config-file>

# Start multiple themes
conky -c ~/.config/conky/theme1/config &
conky -c ~/.config/conky/theme2/config &

# Stop all
killall conky

# Check running
ps aux | grep conky | grep -v grep
```

## Dependencies
- conky (1.19+)
- python3-tk (for manager GUI)
- lua5.3+ with cairo
- lm-sensors (for Calendar theme)
- pyowm (for Weather theme): `pip3 install pyowm`
- OpenWeatherMap API key (for Weather theme)
- pytest (for tests): `pip3 install pytest pytest-cov`

## Running Tests

```bash
# Run all tests (70 tests)
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_theme_structure.py -v

# Run only Lua validation
pytest tests/test_lua_syntax.py -v

# Run only layout editor tests
pytest tests/test_layout_editor.py -v
```
