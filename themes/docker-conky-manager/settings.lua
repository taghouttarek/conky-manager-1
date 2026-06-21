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

function draw_icon_docker(cr, x, y, size)
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, transparency_value)
    cairo_set_line_width(cr, 1.5)
    cairo_move_to(cr, x - size * 0.4, y + size * 0.2)
    cairo_line_to(cr, x + size * 0.4, y + size * 0.2)
    cairo_line_to(cr, x + size * 0.45, y + size * 0.35)
    cairo_line_to(cr, x - size * 0.35, y + size * 0.35)
    cairo_close_path(cr)
    cairo_stroke(cr)
    for i = 0, 2 do
        local cx = x - size * 0.25 + i * size * 0.2
        cairo_rectangle(cr, cx, y, size * 0.15, size * 0.15)
        cairo_stroke(cr)
    end
    cairo_move_to(cr, x - size * 0.4, y + size * 0.45)
    for i = 0, 8 do
        local wx = x - size * 0.4 + i * size * 0.1
        local wy = y + size * 0.45 + ((i % 2 == 0) and 0 or size * 05)
        cairo_line_to(cr, wx, wy)
    end
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

function draw_docker_containers(cr, x, y)
    local w, h = 250, 180

    draw_square(cr, x, y, w, h, transparency_bg)

    draw_icon_docker(cr, x + 15, y + 15, 20)
    draw_text(cr, x + 35, y + 20, "DOCKER", 12, transparency_value)

    local containers = conky_parse('${exec docker ps --format "{{.Names}}" 2>/dev/null || echo ""}')
    local cont_y = y + 45
    local count = 0

    if containers and containers ~= "" then
        for line in containers:gmatch("[^\n]+") do
            local name = line:match("^%s*(.-)%s*$")
            if name and name ~= "" and count < 8 then
                if string.len(name) > 18 then
                    name = string.sub(name, 1, 16) .. ".."
                end

                cairo_set_operator(cr, operator[mode])
                cairo_set_source_rgba(cr, 0.4, 0.8, 0.4, transparency_value)
                cairo_arc(cr, x + 14, cont_y - 3, 3, 0, 2 * math.pi)
                cairo_fill(cr)

                draw_text(cr, x + 22, cont_y, name, 12, transparency_text)
                cont_y = cont_y + 17
                count = count + 1
            end
        end
    end

    if count == 0 then
        draw_text(cr, x + 10, cont_y, "No containers", 12, transparency_text)
    end
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height
    cairo_select_font_face(cr, "Dejavu Sans Book", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)

    local widget_h = 180
    local x = w - 280
    local y = (h - widget_h) / 2

    draw_docker_containers(cr, x, y)
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
