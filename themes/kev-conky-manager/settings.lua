-- Security Vulnerabilities Widget
-- Displays recent KEV entries from CISA

require 'cairo'
assert(os.setlocale("en_US.utf8", "numeric"))

-- Colors (matching system-widgets exactly)
HTML_color = "#FFFFFF"
HTML_color_border = "#FFFFFF"
transparency_bg = 0.6
transparency_border = 0.1
transparency_text = 0.6
transparency_value = 0.9
mode = 1
border_size = 4

HTML_critical = "#ff4444"

operator = {CAIRO_OPERATOR_SOURCE, CAIRO_OPERATOR_CLEAR}
operator_transpose = {CAIRO_OPERATOR_CLEAR, CAIRO_OPERATOR_SOURCE}

function hex2rgb(hex)
    hex = hex:gsub("#", "")
    return (tonumber("0x" .. hex:sub(1, 2)) / 255),
           (tonumber("0x" .. hex:sub(3, 4)) / 255),
           tonumber(("0x" .. hex:sub(5, 6)) / 255)
end

r, g, b = hex2rgb(HTML_color)
r_border, g_border, b_border = hex2rgb(HTML_color_border)
r_crit, g_crit, b_crit = hex2rgb(HTML_critical)

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

function draw_text(cr, x, y, text, font_size, trans)
    cairo_set_operator(cr, operator_transpose[mode])
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_font_size(cr, font_size)
    cairo_move_to(cr, x, y)
    cairo_show_text(cr, text)
end

function draw_icon_shield(cr, x, y, size)
    cairo_set_operator(cr, operator_transpose[mode])
    cairo_set_source_rgba(cr, r, g, b, transparency_value)
    cairo_set_line_width(cr, 1.5)
    local w = size * 0.35
    local h = size * 0.45
    -- Shield shape
    cairo_move_to(cr, x, y - h)
    cairo_line_to(cr, x + w, y - h * 0.5)
    cairo_line_to(cr, x + w, y + h * 0.2)
    cairo_line_to(cr, x, y + h)
    cairo_line_to(cr, x - w, y + h * 0.2)
    cairo_line_to(cr, x - w, y - h * 0.5)
    cairo_close_path(cr)
    cairo_stroke(cr)
    -- Exclamation mark
    cairo_move_to(cr, x, y - h * 0.3)
    cairo_line_to(cr, x, y + h * 0.15)
    cairo_stroke(cr)
    cairo_arc(cr, x, y + h * 0.35, 2, 0, 2 * math.pi)
    cairo_fill(cr)
end

function draw_vuln_widget(cr, x, y)
    local w, h = 250, 250

    draw_square(cr, x, y, w, h, transparency_bg)

    draw_icon_shield(cr, x + 15, y + 15, 20)
    draw_text(cr, x + 35, y + 20, "KEV", 12, transparency_value)

    -- Fetch data
    local raw = conky_parse("${exec python3 ~/.config/conky/kev-conky-manager/fetch_vulns.py --get_list --count 5 2>/dev/null}")

    local cy = y + 45
    local count = 0

    if raw and raw ~= "" then
        for line in raw:gmatch("[^\n]+") do
            local id, vendor, product, date = line:match("([^|]+)|([^|]+)|([^|]+)|([^|]+)")
            if id and count < 5 then
                -- CVE ID in red
                cairo_set_operator(cr, operator_transpose[mode])
                cairo_set_source_rgba(cr, r_crit, g_crit, b_crit, transparency_value)
                cairo_set_font_size(cr, 11)
                cairo_move_to(cr, x + 10, cy)
                cairo_show_text(cr, id)

                -- Vendor/Product
                local vp = vendor .. " " .. product
                if string.len(vp) > 28 then
                    vp = string.sub(vp, 1, 26) .. ".."
                end
                draw_text(cr, x + 10, cy + 14, vp, 9, transparency_text)

                -- Date
                draw_text(cr, x + 10, cy + 26, date, 8, transparency_text)

                cy = cy + 40
                count = count + 1
            end
        end
    end

    if count == 0 then
        draw_text(cr, x + 10, cy, "No KEV entries", 11, transparency_text)
    end

    -- Footer
    draw_text(cr, x + 10, y + h - 12, "Source: CISA KEV", 8, transparency_text)
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height
    cairo_select_font_face(cr, "Dejavu Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)

    -- Right side, below system widgets
    local widget_x = w - 994
    local widget_y = 660
    draw_vuln_widget(cr, widget_x, widget_y)
end

function conky_start_widgets()
    local function draw_conky_function(cr)
        draw_function(cr)
    end

    if conky_window == nil then return end
    local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable,
        conky_window.visual, conky_window.width, conky_window.height)
    local cr = cairo_create(cs)

    local updates = conky_parse("${updates}")
    if tonumber(updates) > 5 then
        draw_conky_function(cr)
    end
    cairo_surface_destroy(cs)
    cairo_destroy(cr)
end
