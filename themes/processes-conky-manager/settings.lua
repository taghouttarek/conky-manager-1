require 'cairo'

HTML_color = "#FFFFFF"
HTML_color_border = "#FFFFFF"
transparency_bg = 0.6
transparency_border = 0.1
transparency_text = 0.6
transparency_value = 0.9

mode = 1
border_size = 4

operator = {CAIRO_OPERATOR_SOURCE, CAIRO_OPERATOR_CLEAR}
operator_transpose = {CAIRO_OPERATOR_CLEAR, CAIRO_OPERATOR_SOURCE}

function hex2rgb(hex)
    hex = hex:gsub("#","")
    return (tonumber("0x"..hex:sub(1,2))/255), (tonumber("0x"..hex:sub(3,4))/255), tonumber(("0x"..hex:sub(5,6))/255)
end

r, g, b = hex2rgb(HTML_color)
r_border, g_border, b_border = hex2rgb(HTML_color_border)

function draw_icon_processes(cr, x, y, size)
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, transparency_value)
    cairo_set_line_width(cr, 1.5)
    local radius = size * 0.35
    local teeth = 8
    for i = 0, teeth - 1 do
        local angle = (i / teeth) * 2 * math.pi
        local next_angle = ((i + 0.5) / teeth) * 2 * math.pi
        local x1 = x + radius * math.cos(angle)
        local y1 = y + radius * math.sin(angle)
        local x2 = x + (radius + size * 0.15) * math.cos(angle + 0.1)
        local y2 = y + (radius + size * 0.15) * math.sin(angle + 0.1)
        local x3 = x + (radius + size * 0.15) * math.cos(next_angle - 0.1)
        local y3 = y + (radius + size * 0.15) * math.sin(next_angle - 0.1)
        local x4 = x + radius * math.cos(next_angle)
        local y4 = y + radius * math.sin(next_angle)
        cairo_move_to(cr, x1, y1)
        cairo_line_to(cr, x2, y2)
        cairo_line_to(cr, x3, y3)
        cairo_line_to(cr, x4, y4)
        cairo_stroke(cr)
    end
    cairo_arc(cr, x, y, size * 0.15, 0, 2 * math.pi)
    cairo_stroke(cr)
end

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

function draw_top_processes(cr, x, y)
    local w, h = 250, 220

    draw_square(cr, x, y, w, h, transparency_bg)

    draw_icon_processes(cr, x + 15, y + 15, 20)
    draw_text(cr, x + 35, y + 20, "TOP PROCESSES", 12, transparency_value)

    local proc_y = y + 45

    for i = 1, 10 do
        local name = conky_parse('${top name ' .. i .. '}')
        local cpu = conky_parse('${top cpu ' .. i .. '}')

        if name and name ~= "" then
            if string.len(name) > 14 then
                name = string.sub(name, 1, 12) .. ".."
            end
            draw_text(cr, x + 10, proc_y, name, 12, transparency_text)
            draw_text(cr, x + w - 50, proc_y, cpu .. "%", 12, transparency_value)
            proc_y = proc_y + 17
        end
    end
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height
    cairo_select_font_face(cr, "Dejavu Sans Book", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)

    local widget_h = 220
    local x = 1640
    local y = 306

    draw_top_processes(cr, x, y)
end

function conky_start_widgets()
    local function draw_conky_function(cr)
        draw_function(cr)
    end

    if conky_window == nil then return end
    local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable, conky_window.visual, conky_window.width, conky_window.height)

    local cr = cairo_create(cs)

    local updates = conky_parse('${updates}')
    update_num = tonumber(updates)

    if update_num > 5 then
        draw_conky_function(cr)
    end
    cairo_surface_destroy(cs)
    cairo_destroy(cr)
end
