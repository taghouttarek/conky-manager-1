-- System Widgets - Network, Processes, Docker, K8s
-- Styled to match Conky-Revisited-2 theme (transparency-based)

require 'cairo'

-- Colors (single white, transparency creates hierarchy)
HTML_color = "#FFFFFF"
transparency_bg = 0.6
transparency_border = 0.1
transparency_title = 0.9
transparency_text = 0.6
transparency_active = 0.9
transparency_dim = 0.4

function hex2rgb(hex)
    hex = hex:gsub("#","")
    return tonumber("0x"..hex:sub(1,2))/255, tonumber("0x"..hex:sub(3,4))/255, tonumber("0x"..hex:sub(5,6))/255
end

r, g, b = hex2rgb(HTML_color)

function draw_square(cr, x, y, w, h, r, g, b, trans)
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_line_width(cr, 2)
    cairo_rectangle(cr, x, y, w, h)
    cairo_fill(cr)

    -- Border (same white, lower transparency)
    cairo_set_source_rgba(cr, r, g, b, transparency_border)
    cairo_set_line_width(cr, 1)
    cairo_rectangle(cr, x, y, w, h)
    cairo_stroke(cr)
end

function draw_text(cr, x, y, text, font_size, trans)
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_font_size(cr, font_size)
    cairo_move_to(cr, x, y)
    cairo_show_text(cr, text)
end

function draw_network_info(cr, x, y)
    -- Background
    draw_square(cr, x, y, 200, 150, r, g, b, transparency_bg)

    -- Title
    draw_text(cr, x + 10, y + 20, "NETWORK", 10, transparency_active)
    y = y + 35

    -- Interface
    local iface = conky_parse('${if_existing /sys/class/net/wlp2s0}wlp2s0${else}enp1s0f0${endif}')
    draw_text(cr, x + 10, y, "Iface: " .. iface, 9, transparency_dim)
    y = y + 18

    -- Local IP
    local local_ip = conky_parse('${addr wlp2s0}')
    if local_ip == "" then
        local_ip = conky_parse('${addr enp1s0f0}')
    end
    draw_text(cr, x + 10, y, "Local: " .. local_ip, 9, transparency_dim)
    y = y + 18

    -- External IP
    local ext_ip = conky_parse('${exec curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "N/A"}')
    draw_text(cr, x + 10, y, "Ext: " .. ext_ip, 9, transparency_dim)
    y = y + 18

    -- Download speed
    local down = conky_parse('${downspeed wlp2s0}')
    if down == "0B/s" then
        down = conky_parse('${downspeed enp1s0f0}')
    end
    draw_text(cr, x + 10, y, "Down: " .. down, 10, transparency_active)
    y = y + 18

    -- Upload speed
    local up = conky_parse('${upspeed wlp2s0}')
    if up == "0B/s" then
        up = conky_parse('${upspeed enp1s0f0}')
    end
    draw_text(cr, x + 10, y, "Up: " .. up, 10, transparency_active)

    return y + 20
end

function draw_network_bandwidth(cr, x, y)
    local w, h = 280, 120

    -- Background
    draw_square(cr, x, y, w, h, r, g, b, transparency_bg)

    -- Title
    draw_text(cr, x + 10, y + 20, "BANDWIDTH", 10, transparency_active)

    -- Download
    local down_speed = conky_parse('${downspeed wlp2s0}')
    if down_speed == "0B/s" then
        down_speed = conky_parse('${downspeed enp1s0f0}')
    end
    draw_text(cr, x + 10, y + 45, "Down: " .. down_speed, 11, transparency_active)

    -- Download bar
    local down_val = tonumber(conky_parse('${downspeedf wlp2s0}')) or 0
    if down_val == 0 then
        down_val = tonumber(conky_parse('${downspeedf enp1s0f0}')) or 0
    end
    local down_pct = math.min(down_val / 100, 1)

    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, 0.2)
    cairo_rectangle(cr, x + 10, y + 55, w - 20, 6)
    cairo_fill(cr)

    cairo_set_source_rgba(cr, r, g, b, transparency_active)
    cairo_rectangle(cr, x + 10, y + 55, (w - 20) * down_pct, 6)
    cairo_fill(cr)

    -- Upload
    local up_speed = conky_parse('${upspeed wlp2s0}')
    if up_speed == "0B/s" then
        up_speed = conky_parse('${upspeed enp1s0f0}')
    end
    draw_text(cr, x + 10, y + 80, "Up: " .. up_speed, 11, transparency_active)

    -- Upload bar
    local up_val = tonumber(conky_parse('${upspeedf wlp2s0}')) or 0
    if up_val == 0 then
        up_val = tonumber(conky_parse('${upspeedf enp1s0f0}')) or 0
    end
    local up_pct = math.min(up_val / 100, 1)

    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
    cairo_set_source_rgba(cr, r, g, b, 0.2)
    cairo_rectangle(cr, x + 10, y + 90, w - 20, 6)
    cairo_fill(cr)

    cairo_set_source_rgba(cr, r, g, b, transparency_active)
    cairo_rectangle(cr, x + 10, y + 90, (w - 20) * up_pct, 6)
    cairo_fill(cr)
end

function draw_top_processes(cr, x, y)
    local w, h = 280, 200

    -- Background
    draw_square(cr, x, y, w, h, r, g, b, transparency_bg)

    -- Title
    draw_text(cr, x + 10, y + 20, "TOP PROCESSES", 10, transparency_active)

    -- Process list
    local proc_y = y + 40

    for i = 1, 10 do
        local name = conky_parse('${top name ' .. i .. '}')
        local cpu = conky_parse('${top cpu ' .. i .. '}')

        if name and name ~= "" then
            -- Truncate long names
            if string.len(name) > 16 then
                name = string.sub(name, 1, 14) .. ".."
            end
            draw_text(cr, x + 10, proc_y, name, 9, transparency_dim)
            draw_text(cr, x + w - 50, proc_y, cpu .. "%", 9, transparency_active)
            proc_y = proc_y + 16
        end
    end
end

function draw_docker_containers(cr, x, y)
    local w, h = 280, 160

    -- Background
    draw_square(cr, x, y, w, h, r, g, b, transparency_bg)

    -- Title
    draw_text(cr, x + 10, y + 20, "DOCKER", 10, transparency_active)

    -- Container list
    local containers = conky_parse('${exec docker ps --format "{{.Names}}" 2>/dev/null || echo ""}')
    local cont_y = y + 40
    local count = 0

    if containers and containers ~= "" then
        for line in containers:gmatch("[^\n]+") do
            local name = line:match("^%s*(.-)%s*$")
            if name and name ~= "" and count < 7 then
                -- Truncate long names
                if string.len(name) > 20 then
                    name = string.sub(name, 1, 18) .. ".."
                end

                -- Status dot (green for running)
                cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE)
                cairo_set_source_rgba(cr, 0.4, 0.8, 0.4, transparency_active)
                cairo_arc(cr, x + 14, cont_y - 3, 3, 0, 2 * math.pi)
                cairo_fill(cr)

                draw_text(cr, x + 22, cont_y, name, 9, transparency_dim)
                cont_y = cont_y + 16
                count = count + 1
            end
        end
    end

    if count == 0 then
        draw_text(cr, x + 10, cont_y, "No containers", 9, transparency_dim)
    end
end

function draw_k8s_context(cr, x, y)
    local w, h = 280, 130

    -- Background
    draw_square(cr, x, y, w, h, r, g, b, transparency_bg)

    -- Title
    draw_text(cr, x + 10, y + 20, "K8S", 10, transparency_active)

    -- Current context
    local context = conky_parse('${exec kubectl config current-context 2>/dev/null || echo "N/A"}')
    draw_text(cr, x + 10, y + 45, context, 12, transparency_active)

    -- Namespace
    local namespace = conky_parse('${exec kubectl config view --minify --output "jsonpath={..namespace}" 2>/dev/null || echo "default"}')
    draw_text(cr, x + 10, y + 65, "NS: " .. namespace, 9, transparency_dim)

    -- Nodes
    local nodes = conky_parse('${exec kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0"}')
    draw_text(cr, x + 10, y + 85, "Nodes: " .. nodes, 9, transparency_dim)

    -- Pods
    local pods = conky_parse('${exec kubectl get pods --no-headers --all-namespaces 2>/dev/null | grep Running | wc -l || echo "0"}')
    draw_text(cr, x + 10, y + 105, "Pods: " .. pods, 9, transparency_dim)
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height

    -- Left side (centered vertically)
    local left_x = 30
    local total_left_height = 120 + 150 -- bandwidth + network info
    local left_y_start = (h - total_left_height) / 2

    draw_network_bandwidth(cr, left_x, left_y_start)
    draw_network_info(cr, left_x, left_y_start + 140)

    -- Right side (centered vertically)
    local right_x = w - 310
    local total_right_height = 200 + 160 + 130 -- processes + docker + k8s
    local right_y_start = (h - total_right_height) / 2

    draw_top_processes(cr, right_x, right_y_start)
    draw_docker_containers(cr, right_x, right_y_start + 220)
    draw_k8s_context(cr, right_x, right_y_start + 400)
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
