-- System Widgets - Network, Processes, Docker, K8s
-- Created: 2026-06-19

require 'cairo'

-- Colors (matching other themes)
HTML_color = "#FFFFFF"
HTML_color_active = "#FFFFFF"
HTML_color_dim = "#888888"
HTML_color_accent = "#4FC3F7"
HTML_color_docker = "#2196F3"
HTML_color_k8s = "#326CE5"

transparency = 0.7
transparency_active = 0.95
transparency_dim = 0.5

function hex2rgb(hex)
    hex = hex:gsub("#","")
    return tonumber("0x"..hex:sub(1,2))/255, tonumber("0x"..hex:sub(3,4))/255, tonumber("0x"..hex:sub(5,6))/255
end

r, g, b = hex2rgb(HTML_color)
r_a, g_a, b_a = hex2rgb(HTML_color_active)
r_d, g_d, b_d = hex2rgb(HTML_color_dim)
r_acc, g_acc, b_acc = hex2rgb(HTML_color_accent)
r_doc, g_doc, b_doc = hex2rgb(HTML_color_docker)
r_k8s, g_k8s, b_k8s = hex2rgb(HTML_color_k8s)

function draw_rounded_rect(cr, x, y, w, h, radius, r, g, b, trans)
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_line_width(cr, 2)
    cairo_arc(cr, x+radius, y+radius, radius, math.pi, 1.5*math.pi)
    cairo_arc(cr, x+w-radius, y+radius, radius, 1.5*math.pi, 2*math.pi)
    cairo_arc(cr, x+w-radius, y+h-radius, radius, 0, 0.5*math.pi)
    cairo_arc(cr, x+radius, y+h-radius, radius, 0.5*math.pi, math.pi)
    cairo_close_path(cr)
    cairo_fill(cr)
end

function draw_text(cr, x, y, text, font_size, r, g, b, trans)
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
    cairo_set_source_rgba(cr, r, g, b, trans)
    cairo_set_font_size(cr, font_size)
    cairo_move_to(cr, x, y)
    cairo_show_text(cr, text)
end

function draw_network_info(cr, x, y)
    -- Title
    draw_text(cr, x, y, "NETWORK INFO", 10, r_acc, g_acc, b_acc, transparency_active)
    y = y + 20

    -- Interface
    local iface = conky_parse('${if_existing /sys/class/net/wlp2s0}wlp2s0${else}enp1s0f0${endif}')
    draw_text(cr, x, y, "Interface: " .. iface, 9, r, g, b, transparency)
    y = y + 18

    -- Local IP
    local local_ip = conky_parse('${addr wlp2s0}')
    if local_ip == "" then
        local_ip = conky_parse('${addr enp1s0f0}')
    end
    draw_text(cr, x, y, "Local IP: " .. local_ip, 9, r, g, b, transparency)
    y = y + 18

    -- External IP
    local ext_ip = conky_parse('${exec curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "N/A"}')
    draw_text(cr, x, y, "External IP: " .. ext_ip, 9, r, g, b, transparency)
    y = y + 18

    -- Download speed
    local down = conky_parse('${downspeed wlp2s0}')
    if down == "0B/s" then
        down = conky_parse('${downspeed enp1s0f0}')
    end
    draw_text(cr, x, y, "↓ " .. down, 9, r_a, g_a, b_a, transparency_active)
    y = y + 18

    -- Upload speed
    local up = conky_parse('${upspeed wlp2s0}')
    if up == "0B/s" then
        up = conky_parse('${upspeed enp1s0f0}')
    end
    draw_text(cr, x, y, "↑ " .. up, 9, r_a, g_a, b_a, transparency_active)
    y = y + 18

    -- Total downloaded
    local total_down = conky_parse('${totaldown wlp2s0}')
    if total_down == "0B" then
        total_down = conky_parse('${totaldown enp1s0f0}')
    end
    draw_text(cr, x, y, "Total ↓: " .. total_down, 8, r_d, g_d, b_d, transparency_dim)

    return y + 20
end

function draw_network_bandwidth(cr, x, y, w, h)
    -- Background
    draw_rounded_rect(cr, x, y, w, h, 8, r, g, b, 0.15)

    -- Title
    draw_text(cr, x + 10, y + 18, "BANDWIDTH", 10, r_acc, g_acc, b_acc, transparency_active)

    -- Download bar
    local down_speed = tonumber(conky_parse('${downspeed wlp2s0}')) or 0
    if down_speed == 0 then
        down_speed = tonumber(conky_parse('${downspeed enp1s0f0}')) or 0
    end
    local max_speed = 100000000 -- 100MB/s
    local down_pct = math.min(down_speed / max_speed, 1)
    local bar_y = y + 35

    draw_text(cr, x + 10, bar_y, "↓ " .. conky_parse('${downspeed wlp2s0}'), 9, r_a, g_a, b_a, transparency_active)
    bar_y = bar_y + 15

    -- Download bar background
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
    cairo_set_source_rgba(cr, r, g, b, 0.2)
    cairo_rectangle(cr, x + 10, bar_y, w - 20, 8)
    cairo_fill(cr)

    -- Download bar fill
    cairo_set_source_rgba(cr, r_acc, g_acc, b_acc, transparency_active)
    cairo_rectangle(cr, x + 10, bar_y, (w - 20) * down_pct, 8)
    cairo_fill(cr)
    bar_y = bar_y + 25

    -- Upload bar
    local up_speed = tonumber(conky_parse('${upspeed wlp2s0}')) or 0
    if up_speed == 0 then
        up_speed = tonumber(conky_parse('${upspeed enp1s0f0}')) or 0
    end
    local up_pct = math.min(up_speed / max_speed, 1)

    draw_text(cr, x + 10, bar_y, "↑ " .. conky_parse('${upspeed wlp2s0}'), 9, r_a, g_a, b_a, transparency_active)
    bar_y = bar_y + 15

    -- Upload bar background
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
    cairo_set_source_rgba(cr, r, g, b, 0.2)
    cairo_rectangle(cr, x + 10, bar_y, w - 20, 8)
    cairo_fill(cr)

    -- Upload bar fill
    cairo_set_source_rgba(cr, 0.4, 0.8, 0.4, transparency_active)
    cairo_rectangle(cr, x + 10, bar_y, (w - 20) * up_pct, 8)
    cairo_fill(cr)
end

function draw_top_processes(cr, x, y, w, h)
    -- Background
    draw_rounded_rect(cr, x, y, w, h, 8, r, g, b, 0.15)

    -- Title
    draw_text(cr, x + 10, y + 18, "TOP PROCESSES", 10, r_acc, g_acc, b_acc, transparency_active)

    -- Process list
    local procs = conky_parse('${top name 1}|${top cpu 1}|${top mem 1}')
    local proc_y = y + 38

    for i = 1, 8 do
        local name = conky_parse('${top name ' .. i .. '}')
        local cpu = conky_parse('${top cpu ' .. i .. '}')
        local mem = conky_parse('${top mem ' .. i .. '}')

        if name and name ~= "" then
            -- Truncate long names
            if string.len(name) > 14 then
                name = string.sub(name, 1, 12) .. ".."
            end
            draw_text(cr, x + 10, proc_y, name, 8, r, g, b, transparency)
            draw_text(cr, x + w - 50, proc_y, cpu .. "%", 8, r_a, g_a, b_a, transparency_active)
            proc_y = proc_y + 16
        end
    end
end

function draw_docker_containers(cr, x, y, w, h)
    -- Background
    draw_rounded_rect(cr, x, y, w, h, 8, r_doc, g_doc, b_doc, 0.15)

    -- Title
    draw_text(cr, x + 10, y + 18, "DOCKER CONTAINERS", 10, r_doc, g_doc, b_doc, transparency_active)

    -- Container list
    local containers = conky_parse('${exec docker ps --format "{{.Names}}|{{.Status}}" 2>/dev/null || echo ""}')
    local cont_y = y + 38
    local count = 0

    if containers and containers ~= "" then
        for line in containers:gmatch("[^\n]+") do
            local name, status = line:match("([^|]+)|([^|]+)")
            if name and count < 6 then
                -- Truncate long names
                if string.len(name) > 18 then
                    name = string.sub(name, 1, 16) .. ".."
                end

                -- Status indicator
                local status_color = {0.4, 0.8, 0.4} -- green
                if status and string.find(status, "Up") then
                    status_color = {0.4, 0.8, 0.4}
                else
                    status_color = {0.8, 0.4, 0.4} -- red
                end

                -- Status dot
                cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
                cairo_set_source_rgba(cr, status_color[1], status_color[2], status_color[3], transparency_active)
                cairo_arc(cr, x + 14, cont_y - 3, 3, 0, 2 * math.pi)
                cairo_fill(cr)

                draw_text(cr, x + 22, cont_y, name, 8, r, g, b, transparency)
                cont_y = cont_y + 16
                count = count + 1
            end
        end
    end

    if count == 0 then
        draw_text(cr, x + 10, cont_y, "No containers running", 8, r_d, g_d, b_d, transparency_dim)
    end
end

function draw_k8s_context(cr, x, y, w, h)
    -- Background
    draw_rounded_rect(cr, x, y, w, h, 8, r_k8s, g_k8s, b_k8s, 0.15)

    -- Title
    draw_text(cr, x + 10, y + 18, "K8S CONTEXT", 10, r_k8s, g_k8s, b_k8s, transparency_active)

    -- Current context
    local context = conky_parse('${exec kubectl config current-context 2>/dev/null || echo "N/A"}')
    draw_text(cr, x + 10, y + 40, context, 11, r_a, g_a, b_a, transparency_active)

    -- Namespace
    local namespace = conky_parse('${exec kubectl config view --minify --output "jsonpath={..namespace}" 2>/dev/null || echo "default"}')
    draw_text(cr, x + 10, y + 60, "NS: " .. namespace, 9, r, g, b, transparency)

    -- Cluster info
    local nodes = conky_parse('${exec kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0"}')
    draw_text(cr, x + 10, y + 80, "Nodes: " .. nodes, 9, r, g, b, transparency)

    -- Pods running
    local pods = conky_parse('${exec kubectl get pods --no-headers --all-namespaces 2>/dev/null | grep Running | wc -l || echo "0"}')
    draw_text(cr, x + 10, y + 100, "Pods: " .. pods, 9, r, g, b, transparency)
end

function draw_function(cr)
    local w, h = conky_window.width, conky_window.height

    -- Left side widgets (Network Info)
    draw_network_info(cr, 30, 50)

    -- Center widget (Bandwidth)
    draw_network_bandwidth(cr, 350, 50, 300, 160)

    -- Right side widgets
    draw_top_processes(cr, w - 350, 50, 320, 200)
    draw_docker_containers(cr, w - 350, 270, 320, 160)
    draw_k8s_context(cr, w - 350, 450, 320, 140)
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
