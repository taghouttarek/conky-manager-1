--[[
    ================================================================================
    conky_draw_rings.lua - Conky Lua script circles
    Optimized for: Nordic Frost Minimalist
    To use this, add the following to your conky.config:
        lua_load = 'conky_draw_rings.lua',
        lua_draw_hook_pre = 'draw_conky_rings',
    ================================================================================
--]]

require 'cairo'

local ring_settings = {
    {
        name = 'cpu',
        arg = 'cpu0',
        max = 100,
        x = 100,
        y = 100,
        radius = 45,
        thickness = 8,
        bg_colour = 0x5e5e5e,
        bg_alpha = 0.2,
        fg_colour = 0x88c0d0,
        fg_alpha = 0.9,
    },
    {
        name = 'memperc',
        arg = '',
        max = 100,
        x = 100,
        y = 100,
        radius = 32,
        thickness = 8,
        bg_colour = 0x5e5e5e,
        bg_alpha = 0.2,
        fg_colour = 0xffffff,
        fg_alpha = 0.8,
    }
}

function draw_ring(cr, t)
    local val = tonumber(conky_parse(string.format('${%s %s}', t['name'], t['arg'])))
    if not val then return end
    
    local pct = val / t['max']
    local angle_0 = -math.pi / 2
    local angle_f = angle_0 + (pct * 2 * math.pi)
    
    -- Background ring
    cairo_arc(cr, t['x'], t['y'], t['radius'], 0, 2 * math.pi)
    cairo_set_source_rgba(cr, ((t['bg_colour'] / 0x10000) % 0x100) / 255, ((t['bg_colour'] / 0x100) % 0x100) / 255, (t['bg_colour'] % 0x100) / 255, t['bg_alpha'])
    cairo_set_line_width(cr, t['thickness'])
    cairo_stroke(cr)
    
    -- Foreground ring
    cairo_arc(cr, t['x'], t['y'], t['radius'], angle_0, angle_f)
    cairo_set_source_rgba(cr, ((t['fg_colour'] / 0x10000) % 0x100) / 255, ((t['fg_colour'] / 0x100) % 0x100) / 255, (t['fg_colour'] % 0x100) / 255, t['fg_alpha'])
    cairo_stroke(cr)
end

function conky_draw_conky_rings()
    if conky_window == nil then return end
    local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable, conky_window.visual, conky_window.width, conky_window.height)
    local cr = cairo_create(cs)
    
    for i in pairs(ring_settings) do
        draw_ring(cr, ring_settings[i])
    end
    
    cairo_destroy(cr)
    cairo_surface_destroy(cs)
end
