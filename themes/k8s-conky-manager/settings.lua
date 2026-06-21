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

function draw_icon_k8s(cr, x, y, size)
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, transparency_value)
    cairo_set_line_width(cr, 1.5)
    local radius = size * 0.35
    local spokes = 7
    cairo_arc(cr, x, y, radius, 0, 2 * math.pi)
    cairo_stroke(cr)
    cairo_arc(cr, x, y, radius * 0.3, 0, 2 * math.pi)
    cairo_stroke(cr)
    for i = 0, spokes - 1 do
        local angle = (i / spokes) * 2 * math.pi
        cairo_move_to(cr, x + radius * 0.3 * math.cos(angle), y + radius * 0.3 * math.sin(angle))
        cairo_line_to(cr, x + radius * math.cos(angle), y + radius * math.sin(angle))
        cairo_stroke(cr)
    end
    cairo_move_to(cr, x, y - radius)
    cairo_line_to(cr, x, y - radius - size * 0.15)
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

function draw_k8s_context(cr, x, y)
    local w, h = 250, 140

    draw_square(cr, x, y, w, h, transparency_bg)

    draw_icon_k8s(cr, x + 15, y + 15, 20)
    draw_text(cr, x + 35, y + 20, "K8S", 12, transparency_value)

    local context = conky_parse('${exec kubectl config current-context 2>/dev/null || echo "N/A"}')
    draw_text(cr, x + 10, y + 45, "Context", 12, transparency_text)
    draw_text(cr, x + 10, y + 60, context, 14, transparency_value)

    local namespace = conky_parse('${exec kubectl config view --minify --output "jsonpath={..namespace}" 2>/dev/null || echo "default"}')
    draw_text(cr, x + 10, y + 80, "Namespace", 12, transparency_text)
    draw_text(cr, x + 10, y + 95, namespace, 12, transparency_value)

    local nodes = conky_parse('${exec kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0"}')
    draw_text(cr, x + 10, y + 115, "Nodes: " .. nodes, 12, transparency_value)
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height
    cairo_select_font_face(cr, "Dejavu Sans Book", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)

    local widget_h = 140
    local x = 1640
    local y = 718

    draw_k8s_context(cr, x, y)
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
