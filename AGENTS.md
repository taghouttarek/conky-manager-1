# Conky Manager - Agent Instructions

## Overview
This is a Conky theme manager repository containing:
- `conky_manager.py` - Main manager application (Python/Tkinter)
- `layout_editor.py` - Drag-and-drop layout editor for widget positioning
- `themes/` - All conky themes
- `tests/` - Non-regression test suite (76 tests)
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
- Scans `~/.config/conky/` for themes
- Detects themes by config files: `conkyrc`, `*.conf`, `config.conf`, `conky.conf`
- If theme uses non-standard config name, create a `conkyrc` symlink in theme root
- Supports running multiple themes simultaneously
- Each theme runs as separate conky process with `-m <monitor>` flag

### Theme Structure
```
themes/<theme-name>/
├── conkyrc              # Config (loads positions.lua + settings.lua)
├── settings.lua         # Lua settings and drawing code
├── *.lua                # Additional Lua scripts
├── PNG/                 # Image assets (if any)
```

### Shared Positioning System
- `~/.config/conky/positions.lua` — shared position config for all themes
- `~/.config/conky/layout.json` — layout state (resolution, monitor, widget positions)
- All themes load `positions.lua` first via `lua_load`, then their own `settings.lua`
- Themes read `positions["<theme-name>"].x/.y` at runtime
- Layout editor writes both `layout.json` and `positions.lua`
- Each conkyrc must load: `lua_load = '~/.config/conky/positions.lua ~/.config/conky/<theme>/settings.lua'`

### Layout Editor (`layout_editor.py`)
- Scans running conky processes via `pgrep -a conky`
- Each theme is a `WidgetRect` with x/y/w/h in screen coordinates
- Canvas uses `scale` factor (0.5 default) for display
- Drag converts canvas deltas: `dx = canvas_delta / scale`
- Position clamped to `[0, screen_w - w]` x `[0, screen_h - h]`

**Features:**
- **Fullscreen on open** — `attributes('-zoomed', True)` with fallback
- **Resolution presets** — 1920x1080, 2560x1440, 3840x2160, Custom
- **Monitor selection** — dropdown with `xrandr --listmonitors` detection
- **Center All** button — centers bounding box of all widgets on screen
- **H/V center buttons** — per-widget horizontal/vertical centering (canvas tag_bind)
- **Multi-select** — Ctrl+Click to select multiple widgets, drag moves all together
- **Alignment guides** — red dashed lines appear when dragging near alignment points
- **Magnetic snapping** — snaps to other widget edges/centers, screen edges, screen center (2px threshold)
- **Equal spacing snap** — snaps when gap matches existing gap between other widgets
- **Per-widget minimum sizes** — `MIN_WIDGET_SIZES` dict enforces content-based min sizes
- **Auto-restart themes** after applying positions

**Key methods:**
- `save_positions()` — writes `layout.json` AND `positions.lua`
- `update_conkyrc_position()` — updates `gap_x/gap_y` to 0, `minimum_width/height`
- `restart_themes()` — kills and restarts themes with `-m <monitor>` flag
- `detect_monitors()` — parses `xrandr --listmonitors`
- `_compute_snap()` — core snapping algorithm with guide line generation

**Data flow:**
- `layout.json`: `{"resolution": {"w": N, "h": N}, "monitor": 0, "<theme>": {"x": N, "y": N, "w": N, "h": N}}`
- `positions.lua`: `screen = {w = N, h = N, monitor = 0}` + `positions = {["<theme>"] = {x = N, y = N}}`

## Conky 1.19 Compatibility

### Config Syntax (Lua format required)
```lua
conky.config = {
    background = false,
    update_interval = 1,
    own_window = true,
    own_window_type = 'normal',
    font = 'Dejavu Sans:size=10',
    minimum_width = 1920, minimum_height = 1200,
    alignment = 'top_left',
    gap_x = 0, gap_y = 0,
    lua_load = '~/.config/conky/positions.lua ~/.config/conky/<theme>/settings.lua',
    lua_draw_hook_pre = 'start_widgets',
}
conky.text = [[
]]
```

### Deprecated Settings (do NOT use)
- `xftfont` → use `font`
- `minimum_size W H` → use `minimum_width = W,` and `minimum_height = H,`
- Old syntax (`background no`) → use Lua format (`background = false,`)

### Lua Requirements
- Use `tonumber()` when parsing conky exec output for arithmetic
- Example: `local val = tonumber(conky_parse('${exec command}')) or 0`
- Always include `updates > 5` guard in `conky_start_widgets`
- Always include `os.setlocale("en_US.utf8", "numeric")` in settings.lua

## Fix History

### Multi-Theme Support
- Added `start_conky()`, `stop_theme()`, `stop_conky()`, `is_theme_running()`
- Manager no longer kills all conky before starting a new theme
- Tracks running themes in settings.json

### Path Corrections
- All themes moved from `~/.conky/` to `~/.config/conky/`
- Updated `lua_load` paths in all configs

### Unified Widget Positioning (v2.0.4)
- All themes use fullscreen windows (1920x1200) with `gap_x = 0`, `gap_y = 0`
- Content positioned with absolute screen coordinates in Lua
- Shared `positions.lua` loaded by all themes via `lua_load`
- Layout editor writes `positions.lua` (not individual Lua files)
- Auto-restart themes after applying positions

### Code Review Fixes (v2.0.4)
- Fixed `hex2rgb()` blue channel bug across all 9 themes
- Added `os.setlocale("en_US.utf8", "numeric")` to 5 missing files
- Fixed `update_num` nil dereference in 7 files
- Fixed weather theme: `io.popen` leak, nil concatenation guards, global vars→local
- Fixed docker theme: `size * 05` typo → `size * 0.05`
- Layout editor: atomic file writes, error handling, PID validation

### Weather Widget Fix (v2.0.5)
- Added `updates > 5` guard to `conky_start_widgets` (was the only theme missing it)
- Added `pcall` error handling with logging to `error.log`
- Reduced `update_interval` from 15 to 3 for faster restart visibility

### Layout Editor Features (v2.0.6)
- Fullscreen on open (attributes('-zoomed', True))
- Monitor detection and selection via `xrandr --listmonitors`
- `-m <monitor>` flag for conky start/restart
- Center All button for centering all widgets on screen
- H/V center buttons per widget (canvas tag_bind)
- Multi-select with Ctrl+Click
- Alignment guides (red dashed lines)
- Magnetic snapping (2px threshold) to edges, centers, screen
- Equal spacing snap between widget pairs
- Per-widget minimum sizes via `MIN_WIDGET_SIZES`
- Configurable resolution with presets and manual entry

## Adding New Themes

1. Create `themes/<name>-conky-manager/` directory (MUST use `-conky-manager` suffix)
2. Create `settings.lua` with `require 'cairo'`, `os.setlocale`, `positions["<theme>"].x/.y`
3. Create `conkyrc` that loads `positions.lua` FIRST:
   ```lua
   lua_load = '~/.config/conky/positions.lua ~/.config/conky/<theme>-conky-manager/settings.lua',
   ```
4. Include `updates > 5` guard in `conky_start_widgets`
5. Run `luac -p settings.lua` to validate syntax
6. Add to `MIN_WIDGET_SIZES` in `layout_editor.py`
7. Add to `default_widgets` in `layout_editor.py` `load_widgets()`
8. Test: `conky -c ~/.config/conky/<theme>-conky-manager/conkyrc`
9. Copy to system: `cp -r themes/<theme>-conky-manager ~/.config/conky/`
10. Commit to repo

## Running Conky Manually

```bash
# Start single theme
conky -c ~/.config/conky/<theme-name>/conkyrc -d -m 0

# Start multiple themes
conky -c ~/.config/conky/theme1/conkyrc -d -m 0 &
conky -c ~/.config/conky/theme2/conkyrc -d -m 0 &

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
# Run all tests (76 tests)
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
