---
name: create-conky-widget
description: Create conky widgets matching the system-widgets theme style - white, semi-transparent squares with borders, icon+title pattern, using Cairo drawing in Lua
---

# create-conky-widget

Create conky widgets for the conky-manager repo following the unified positioning system.

## Naming Convention

Theme directory MUST use the `-conky-manager` suffix:
```
themes/<widget-name>-conky-manager/
```

## File Structure

```
themes/<widget-name>-conky-manager/
├── conkyrc              # Config (loads positions.lua + settings.lua)
├── settings.lua         # Lua drawing code + theme settings
├── PNG/                 # Image assets (optional)
```

## Style Reference

Based on the system widgets (network, bandwidth, processes, docker, k8s):

### Colors & Transparency
```lua
HTML_color = "#FFFFFF"
HTML_color_border = "#FFFFFF"
transparency_bg = 0.6
transparency_border = 0.1
transparency_text = 0.6
transparency_value = 0.9
mode = 1          -- 1 = background, 2 = no background
border_size = 4
```

### Operators (CRITICAL - must use these exactly)
```lua
operator = {CAIRO_OPERATOR_SOURCE, CAIRO_OPERATOR_CLEAR}
operator_transpose = {CAIRO_OPERATOR_CLEAR, CAIRO_OPERATOR_SOURCE}
```
- `operator[mode]` for drawing backgrounds and fills
- `operator_transpose[mode]` for drawing text

### Font
- `Dejavu Sans Book` with `CAIRO_FONT_SLANT_NORMAL`
- Font sizes: 12 for labels, 14 for values

## Widget Structure

Each widget follows this pattern:

```lua
function draw_<widget_name>(cr, x, y)
    local w, h = <width>, <height>

    -- 1. Background square
    draw_square(cr, x, y, w, h, transparency_bg)

    -- 2. Icon + Title
    draw_icon_<widget_name>(cr, x + 15, y + 15, 20)
    draw_text(cr, x + 35, y + 20, "TITLE", 12, transparency_value)

    -- 3. Data rows (label on left, value on right)
    local cy = y + 45
    draw_text(cr, x + 10, cy, "Label", 12, transparency_text)
    draw_text(cr, x + 10, cy + 15, value, 12, transparency_value)
end
```

## Core Drawing Functions

### draw_square (background box)
```lua
function draw_square(cr, pos_x, pos_y, rectangle_x, rectangle_y, trans)
    cairo_set_operator(cr, operator[mode])
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_line_width(cr, 2)
    cairo_rectangle(cr, pos_x, pos_y, rectangle_x, rectangle_y)
    cairo_fill(cr)

    cairo_set_operator(cr, operator[mode])
    cairo_set_source_rgba(cr, r_border, g_border, b_border, transparency_border)
    cairo_set_line_width(cr, border_size)
    cairo_rectangle(cr, pos_x, pos_y, rectangle_x, rectangle_y)
    cairo_stroke(cr)
end
```

### draw_text
```lua
function draw_text(cr, x, y, text, font_size, trans)
    cairo_set_operator(cr, operator_transpose[mode])
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_font_size(cr, font_size)
    cairo_move_to(cr, x, y)
    cairo_show_text(cr, text)
end
```

### Icon Pattern
```lua
function draw_icon_<name>(cr, x, y, size)
    cairo_set_operator(cr, operator_transpose[mode])  -- CRITICAL: use transpose for dark icons
    cairo_set_source_rgba(cr, r, g, b, transparency_value)
    cairo_set_line_width(cr, 1.5)
    -- Draw icon shape here (arcs, lines, filled shapes, etc.)
end
```

**IMPORTANT**: Icons MUST use `operator_transpose[mode]` (not `operator[mode]`) to appear dark on the semi-transparent background.

## Widget Sizes (must register in MIN_WIDGET_SIZES)

Every widget must define its content dimensions (`local w, h = ...`) and register the minimum size in `layout_editor.py`:
```python
MIN_WIDGET_SIZES = {
    # ... existing entries ...
    "<widget-name>-conky-manager": (<min_width>, <min_height>),
}
```

Typical sizes: Width 220-250px, Height 120-250px depending on content.

Also add default position to `default_widgets` in `load_widgets()`:
```python
"<widget-name>-conky-manager": {"x": <x>, "y": <y>, "w": <w>, "h": <h>, "color": "<hex>"},
```

## conkyrc Template (CRITICAL - follow exactly)

```lua
conky.config = {
    background = false,
    update_interval = 2,
    override_utf8_locale = true,
    double_buffer = true,
    no_buffers = true,
    text_buffer_size = 2048,
    imlib_cache_size = 0,
    own_window = true,
    own_window_transparent = true,
    own_window_argb_visual = true,
    own_window_type = 'normal',
    own_window_hints = 'undecorated,below,sticky,skip_taskbar,skip_pager',
    border_inner_margin = 0,
    border_outer_margin = 0,
    minimum_width = 1920, minimum_height = 1200,
    alignment = 'top_left',
    gap_x = 0,
    gap_y = 0,
    draw_shades = false,
    draw_outline = false,
    draw_borders = false,
    draw_graph_borders = false,
    font = 'Dejavu Sans:size=10',
    xftalpha = 0.8,
    uppercase = false,
    default_color = 'FFFFFF',
    lua_load = '~/.config/conky/positions.lua ~/.config/conky/<widget-name>-conky-manager/settings.lua',
    lua_draw_hook_pre = 'start_widgets',
}
conky.text = [[
]]
```

**Key points:**
- `gap_x = 0`, `gap_y = 0` always — positioning done in Lua via `positions.lua`
- `minimum_width = 1920`, `minimum_height = 1200` — fullscreen window
- `lua_load` loads `positions.lua` FIRST, then `settings.lua`

## Positioning (CRITICAL - read from positions.lua)

Positions are NOT hardcoded. They are read from the shared `~/.config/conky/positions.lua` at runtime:

```lua
function draw_function(cr)
    local w, h = conky_window.width, conky_window.height
    cairo_select_font_face(cr, "Dejavu Sans Book", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)

    local x = positions["<widget-name>-conky-manager"].x
    local y = positions["<widget-name>-conky-manager"].y

    draw_<widget>(cr, x, y)
end
```

The `positions` table is loaded by `positions.lua` which is loaded first in `lua_load`. It contains:
```lua
positions = {
    ["<widget-name>-conky-manager"] = {x = N, y = N},
    ...
}
```

## settings.lua Template (CRITICAL - follow exactly)

```lua
-- ###<Widget> settings###
-- (your theme-specific settings here)
-- ###Style (matching system-widgets)###
HTML_color = "#FFFFFF"
HTML_color_border = "#FFFFFF"
transparency_bg = 0.6
transparency_border = 0.1
transparency_text = 0.6
transparency_value = 0.9
-- ###Mode###
mode = 1
border_size = 4
-- ###Dont change code below###
require 'cairo'
assert(os.setlocale("en_US.utf8", "numeric"))

-- hex2rgb, draw_square, draw_text, draw_icon, etc.

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height

    local x = positions["<widget-name>-conky-manager"].x
    local y = positions["<widget-name>-conky-manager"].y

    draw_<widget>(cr, x, y)
end

function conky_start_widgets()
    local function draw_conky_function(cr)
        draw_function(cr)
    end

    if conky_window == nil then return end
    local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable,
        conky_window.visual, conky_window.width, conky_window.height)
    local cr = cairo_create(cs)

    local updates = conky_parse('${updates}')
    if tonumber(updates or "0") > 5 then
        draw_conky_function(cr)
    end
    cairo_surface_destroy(cs)
    cairo_destroy(cr)
end
```

**Key requirements:**
- `require 'cairo'` — needed for all cairo drawing
- `os.setlocale("en_US.utf8", "numeric")` — required for numeric formatting
- `tonumber(updates or "0") > 5` — wait for conky to initialize before drawing
- `positions["<theme>"].x/.y` — read position from shared positions.lua
- `cairo_surface_destroy(cs)` before `cairo_destroy(cr)` — standard cleanup order

## Data Fetching
Use `conky_parse("${exec ...}")` for external data:
```lua
local val = conky_parse("${exec python3 /path/to/script --flag 2>/dev/null}")
```
Use `tonumber()` when parsing for arithmetic:
```lua
local num = tonumber(conky_parse('${exec ...}')) or 0
```

## Existing Widgets (for reference)
- `themes/network-conky-manager/` — network info
- `themes/bandwidth-conky-manager/` — download/upload speed
- `themes/processes-conky-manager/` — top processes by CPU
- `themes/docker-conky-manager/` — Docker containers
- `themes/k8s-conky-manager/` — Kubernetes context
- `themes/crypto-conky-manager/` — crypto prices with chart
- `themes/kev-conky-manager/` — CISA KEV feed
- `themes/infra-conky-manager/` — infrastructure CVEs
- `themes/weather-conky-manager/` — weather (circle style)
- `themes/calendar-conky-manager/` — calendar with rings
- `themes/revisited-conky-manager/` — desktop widgets
- `themes/claude-conky-manager/` — Claude ring widgets

## Steps to Create a New Widget

1. Create `themes/<name>-conky-manager/` directory
2. Create `settings.lua` following the template above
3. Create `conkyrc` following the template above (load positions.lua first!)
4. Run `luac -p settings.lua` to validate Lua syntax
5. Test: `conky -c ~/.config/conky/<name>-conky-manager/conkyrc`
6. Add entry to `MIN_WIDGET_SIZES` in `layout_editor.py`:
   ```python
   "<name>-conky-manager": (<min_width>, <min_height>),
   ```
7. Add entry to `default_widgets` in `layout_editor.py` `load_widgets()`:
   ```python
   "<name>-conky-manager": {"x": <x>, "y": <y>, "w": <w>, "h": <h>, "color": "<hex>"},
   ```
8. Copy to system: `cp -r themes/<name>-conky-manager ~/.config/conky/`
9. Commit to repo
