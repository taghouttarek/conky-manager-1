-- draw_background.lua
-- Draws a semi-transparent rounded rectangle behind the Conky window.

require 'cairo'

function conky_draw_background()
    if conky_window == nil then return end
    local w = conky_window.width
    local h = conky_window.height
    local cs = cairo_xlib_surface_create(
        conky_window.display,
        conky_window.drawable,
        conky_window.visual,
        w, h
    )
    local cr = cairo_create(cs)

    local radius = 18
    local degrees = math.pi / 180

    -- Rounded rectangle path
    cairo_new_sub_path(cr)
    cairo_arc(cr, radius, radius, radius, 180 * degrees, 270 * degrees)
    cairo_arc(cr, w - radius, radius, radius, -90 * degrees, 0 * degrees)
    cairo_arc(cr, w - radius, h - radius, radius, 0 * degrees, 90 * degrees)
    cairo_arc(cr, radius, h - radius, radius, 90 * degrees, 180 * degrees)
    cairo_close_path(cr)

    -- Fill with Catppuccin Mocha base + 85% opacity
    cairo_set_source_rgba(cr, 0.18, 0.19, 0.25, 0.85)  -- #2E3340
    cairo_fill(cr)

    -- Optional: a very subtle border
    cairo_set_source_rgba(cr, 0.45, 0.53, 0.70, 0.4)   -- #7287B2
    cairo_set_line_width(cr, 1.0)
    cairo_stroke(cr)

    cairo_destroy(cr)
    cairo_surface_destroy(cs)
end
