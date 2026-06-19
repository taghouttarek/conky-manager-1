-- 2014-02-24 by eXpander


---------------- USER CONFIGURATION ----------------
-- Set your number of physical cores to show temperatures of each.
number_of_physical_CPU_cores = 16      

-- Your GPU model. Only NVIDIA cards with NVIDIA proprietary drivers are official supported. Issue nvidia-smi to find your model!			    
graphic_card_model = "Type Your Model Here"

-- Show graphic card temperature? (Yes/No)
enable_graphic_card_temperature_sensor= "No" 

-- Colors
HTML_colors = "#FFFFFF"
HTML_colors_current = "#FFFFFF"
transparency = 0.3 -- Background circles transparency (0 to 1)
transparency_active = 0.9 -- Active/current elements transparency (0 to 1)

-- Scaled relative position from middle. Positive x and y means left and up, negative x and y means right and down.
x_rel_pos = 0
y_rel_pos = 0
























































require 'cairo'

function hex2rgb(hex)
  hex = hex:gsub("#","")
  return tonumber("0x"..hex:sub(1,2)), tonumber("0x"..hex:sub(3,4)), tonumber("0x"..hex:sub(5,6))
end

r,g,b = hex2rgb(HTML_colors)
r_c,g_c,b_c = hex2rgb(HTML_colors_current)

r = r/255
g = g/255
b = b/255

r_c = r_c/255
g_c = g_c/255
b_c = b_c/255

if enable_graphic_card_temperature_sensor == "Yes" then
  number_of_physical_CPU_cores = number_of_physical_CPU_cores + 1
end


function create_circle_hdd(cr,w,h,elements,distance_between_blocks, radius, line_width, current)
  cairo_set_line_width(cr, line_width)
  cairo_set_source_rgba(cr, r,g,b,transparency)
  cairo_new_path(cr)
  local number_of_arcs = (360 - (elements*distance_between_blocks)) / elements
  local start_angel = 270
  local percent_per_element = 100.0 / elements
  local charged_elements = current / percent_per_element
  
  for i=1, elements do
    if charged_elements >= i then
      cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency_active)
    end
    cairo_arc(cr, w,h,radius,start_angel*math.pi/180,(start_angel+number_of_arcs)*math.pi/180)
    cairo_stroke(cr)
    start_angel = start_angel+number_of_arcs+distance_between_blocks
    cairo_set_source_rgba(cr, r,g,b,transparency)
  end   
end
function create_circle(cr,w,h, elements, distance_between_blocks, two_number_degree, radius, line_width, operator, radius_shift_for_text, current, days, shift_days_distance)
  elements = tonumber(elements) or 12
  cairo_set_line_width(cr, line_width)
  cairo_set_source_rgba(cr, r,g,b,transparency)
  cairo_new_path(cr)
  local number_of_arcs = (360 - (elements*distance_between_blocks)) / elements
  local start_angel = 270
  
  for i=1, elements do
    if i == current then
      cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency_active)
    end
    cairo_arc(cr, w/2, h/2, radius, start_angel*math.pi/180, (start_angel+number_of_arcs)*math.pi/180)
    cairo_stroke(cr)
    start_angel = start_angel+number_of_arcs+distance_between_blocks
    cairo_set_source_rgba(cr, r,g,b,transparency)
  end 
  
  start_angel = 270
  cairo_set_operator(cr, operator)
  
  for i=1, elements do
    if i == current then
      cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency_active)
    end
    if string.len(tostring(i)) == 2 and days == "" then
      cairo_move_to(cr,w/2+((radius+radius_shift_for_text)*math.cos((start_angel+(((number_of_arcs-two_number_degree)/2)))*(math.pi/180.0))),h/2+((radius+radius_shift_for_text)*math.sin((start_angel+(((number_of_arcs-two_number_degree)/2)))*(math.pi/180.0))))
      cairo_rotate(cr, (((number_of_arcs-two_number_degree)/2)+(number_of_arcs+distance_between_blocks)*(i-1))*math.pi/180.0)
      cairo_show_text(cr,tostring(i))
      cairo_rotate(cr,-(((number_of_arcs-two_number_degree)/2)+(number_of_arcs+distance_between_blocks)*(i-1))*math.pi/180.0)
    elseif days ~= "" then
      cairo_move_to(cr,w/2+((radius+radius_shift_for_text)*math.cos((start_angel+((math.abs((number_of_arcs-shift_days_distance))/2)))*(math.pi/180.0))),h/2+((radius+radius_shift_for_text)*math.sin((start_angel+((math.abs((number_of_arcs-shift_days_distance))/2)))*(math.pi/180.0))))
      cairo_rotate(cr, ((math.abs((number_of_arcs-shift_days_distance))/2)+(number_of_arcs+distance_between_blocks)*(i-1)+4)*math.pi/180.0)
      cairo_show_text(cr,days[i])
      cairo_rotate(cr,-((math.abs((number_of_arcs-shift_days_distance))/2)+(number_of_arcs+distance_between_blocks)*(i-1)+4)*math.pi/180.0)      
    elseif string.len(tostring(i)) == 1 and days == "" then
      cairo_move_to(cr,w/2+((radius+radius_shift_for_text)*math.cos((start_angel+(((number_of_arcs-distance_between_blocks)/2)))*(math.pi/180.0))),h/2+((radius+radius_shift_for_text)*math.sin((start_angel+(((number_of_arcs-distance_between_blocks)/2)))*(math.pi/180.0))))
      cairo_rotate(cr, (((number_of_arcs-distance_between_blocks)/2)+(number_of_arcs+distance_between_blocks)*(i-1))*math.pi/180.0)
      cairo_show_text(cr,tostring(i))
      cairo_rotate(cr,-(((number_of_arcs-distance_between_blocks)/2)+(number_of_arcs+distance_between_blocks)*(i-1))*math.pi/180.0)
    end
    
    start_angel = start_angel+number_of_arcs+distance_between_blocks 
    cairo_set_source_rgba(cr, r,g,b,transparency)
  end
  cairo_close_path(cr)
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
end


function vertical_bars(cr,w,h,x,y,conky_value)
    cairo_set_source_rgba(cr, r,g,b,transparency)
    local max_temp = 100
    local percent_per_block = max_temp / 10
    if conky_value == nil then conky_value = 0 end
    local number_of_filled_blocks = math.floor((conky_value/percent_per_block)+0.5)
    
    for i=1,10 do
      if number_of_filled_blocks >= i then
	cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency_active)
      end
      cairo_rectangle(cr, w, h/2+y-i*5,15,4)
      cairo_fill(cr)
      cairo_set_source_rgba(cr, r,g,b,transparency)
    end
  
end

function draw_circles(cr, x_start,y_start,radius, angle_1, angle_2, free_perc, angle_step)
	 cairo_select_font_face (cr, "Dejavu Sans Condensed", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
	 local number_of_circles = 360 / angle_step
	 local angle_start = 90
	 cairo_set_line_width(cr, 1)
	 local percent_per_circle = 100.0 / number_of_circles
	 local number_of_nonfree_circles = math.floor(((100.0 - tonumber(free_perc)) / percent_per_circle)+0.5)
	 cairo_set_source_rgba(cr, r,g,b,transparency)
	 
	for i=1,number_of_circles do
	  cairo_arc(cr,x_start+(radius*math.cos(angle_start*(math.pi/180.0))),y_start-(radius+5)+radius-(radius*math.sin(angle_start*(math.pi/180.0))),2,angle1,angle2)
	  if i <= number_of_nonfree_circles then
	    cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency)
	    cairo_fill(cr)
	  else
	    cairo_set_source_rgba(cr, r,g,b,transparency)
	    cairo_fill(cr)
	  end
	  angle_start = angle_start - angle_step
	end
	cairo_set_source_rgba(cr, r,g,b,transparency)
	
end

function draw_function(cr)
  local w,h=conky_window.width,conky_window.height	
  cairo_set_line_width(cr, 3)
  cairo_set_font_size(cr,12)
  cairo_select_font_face (cr, "Dejavu Sans Condensed", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
  
-- Number of weeks per year --- 
  create_circle(cr,w-x_rel_pos,h-y_rel_pos, 52.0, 2, 3.5, 225, 3, CAIRO_OPERATOR_OVER, 4, tonumber(conky_parse('${exec date +%V}')), '')
  
-- Number of days in a month ---
  create_circle(cr,w-x_rel_pos,h-y_rel_pos, tonumber(conky_parse('${exec cal |egrep -v [a-z] |wc -w}')), 2, 3.5, 200, 13,CAIRO_OPERATOR_CLEAR, -4.5,tonumber(conky_parse('${exec date +%d}')), '')
  
--- Days ---
-- function create_circle(cr,w,h, elements, distance_between_blocks, two_number_degree, radius, line_width, operator, radius_shift_for_text, current, days, shift_days_distance)
 
  local days = {"Mon", "Tue", "Wed","Thu", "Fri", "Sat", "Sun"}
  create_circle(cr,w-x_rel_pos,h-y_rel_pos, 7, 2, 3.5, 150, 13, CAIRO_OPERATOR_CLEAR, -4, tonumber(conky_parse('${exec date +%u}')), days, 8.5)
  
--- Month ---
  
  local month = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}
  create_circle(cr,w-x_rel_pos,h-y_rel_pos, 12, 2, 3.5, 175, 13, CAIRO_OPERATOR_CLEAR, -4, tonumber(conky_parse('${exec date +%m}')), month, 5.5)
  
  
--- Clock ---
  local hours = conky_parse('${exec date +%H}')
  local minutes = conky_parse('${exec date +%M}')
  local seconds = tonumber(conky_parse('${exec date +%S}'))
  local colon_visible = (seconds % 2 == 0)
  
  cairo_set_font_size(cr,42)
  cairo_set_source_rgba(cr, r_c,g_c,b_c,transparency_active)
  
  if colon_visible then
    cairo_move_to(cr, (w-x_rel_pos)/2-54,(h-y_rel_pos)/2)
    cairo_show_text(cr, hours .. ":" .. minutes)
  else
    cairo_move_to(cr, (w-x_rel_pos)/2-54,(h-y_rel_pos)/2)
    cairo_show_text(cr, hours .. " " .. minutes)
  end
  

--- Free space ---
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
  angle1 = 0.0  * (math.pi/180.0);  
  angle2 = 360.0 * (math.pi/180.0);
  
  create_circle_hdd(cr,(w-x_rel_pos)/2-60,(h-y_rel_pos)/2-80,20,3, 20, 3, 100-tonumber(conky_parse("${fs_free_perc /}")))
  create_circle_hdd(cr,(w-x_rel_pos)/2+60,(h-y_rel_pos)/2-80,20,3, 20, 3,100-tonumber(conky_parse("${fs_free_perc /home}")))
  

  cairo_arc(cr,(w-x_rel_pos)/2-60,(h-y_rel_pos)/2-80,14,0,2*math.pi)
  cairo_fill(cr)
  cairo_arc(cr,(w-x_rel_pos)/2+60,(h-y_rel_pos)/2-80,14,0,2*math.pi)
  cairo_fill(cr)
  
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR)
  cairo_move_to(cr, (w-x_rel_pos)/2-64, (h-y_rel_pos)/2-75)
  cairo_show_text(cr,"R")
  cairo_move_to(cr, (w-x_rel_pos)/2+56, (h-y_rel_pos)/2-75)
  cairo_show_text(cr,"H")
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
  
--- Temperatures ---

  local x = (w-x_rel_pos)/2
  local temp_val = tonumber(conky_parse("${exec sensors|grep 'Tctl:'|awk '{print $2}'| cut -b2,3,4,5}"))
  if temp_val == nil then temp_val = 0 end

  vertical_bars(cr,x-8,h-y_rel_pos,64,75,temp_val)
  cairo_arc(cr,x-1,(h-y_rel_pos)/2+50,6,0,2*math.pi)
  cairo_fill(cr)
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR)
  cairo_move_to(cr,x-8,(h-y_rel_pos)/2+53)
  cairo_show_text(cr,"CPU")
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER)
end

function conky_start_widgets()
	local function draw_conky_function(cr)
		local str=''
		local value=0		
		draw_function(cr)
	end
	
	-- Check that Conky has been running for at least 5s

	if conky_window==nil then return end
	local cs=cairo_xlib_surface_create(conky_window.display,conky_window.drawable,conky_window.visual, conky_window.width,conky_window.height)
	
	local cr=cairo_create(cs)	
	
	local updates=conky_parse('${updates}')
	update_num=tonumber(updates)
	
	if update_num>5 then
		draw_conky_function(cr)
	end
	cairo_surface_destroy(cs)
	cairo_destroy(cr)
end
