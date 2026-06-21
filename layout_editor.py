#!/usr/bin/env python3
"""Layout Editor - Drag and drop interface for positioning conky widgets"""
import tkinter as tk
from tkinter import ttk
import json
import os
import subprocess
from pathlib import Path

LAYOUT_FILE = Path.home() / ".config" / "conky" / "layout.json"
SCREEN_W = 1920
SCREEN_H = 1080
SCALE = 0.5  # Canvas scale factor (adjusted by zoom)


def load_layout():
    if LAYOUT_FILE.exists():
        with open(LAYOUT_FILE) as f:
            return json.load(f)
    return {}


def save_layout(data):
    LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAYOUT_FILE, "w") as f:
        json.dump(data, f, indent=2)


class WidgetRect:
    def __init__(self, canvas, name, x, y, w, h, color="#ffffff"):
        self.canvas = canvas
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.rect = None
        self.label = None
        self.resize_handle = None
        self.drag_data = {"x": 0, "y": 0}
        self.resizing = False
        self.draw()

    def draw(self):
        sx, sy, sw, sh = self.x * SCALE, self.y * SCALE, self.w * SCALE, self.h * SCALE
        # Widget rectangle
        self.rect = self.canvas.create_rectangle(
            sx, sy, sx + sw, sy + sh,
            fill=self.color, outline="#888888", width=1, stipple="gray25",
            tags=("widget", self.name)
        )
        # Label
        self.label = self.canvas.create_text(
            sx + sw / 2, sy + sh / 2,
            text=self.name, fill="white", font=("Dejavu Sans", 8, "bold"),
            tags=("widget_label", self.name)
        )
        # Resize handle (bottom-right corner)
        hr = 5
        self.resize_handle = self.canvas.create_rectangle(
            sx + sw - hr, sy + sh - hr, sx + sw + hr, sy + sh + hr,
            fill="#ff4444", outline="#ffffff", width=1,
            tags=("resize_handle", self.name)
        )

    def update_position(self):
        sx, sy, sw, sh = self.x * SCALE, self.y * SCALE, self.w * SCALE, self.h * SCALE
        self.canvas.coords(self.rect, sx, sy, sx + sw, sy + sh)
        self.canvas.coords(self.label, sx + sw / 2, sy + sh / 2)
        hr = 5
        self.canvas.coords(self.resize_handle, sx + sw - hr, sy + sh - hr, sx + sw + hr, sy + sh + hr)

    def move(self, dx, dy):
        self.x = max(0, min(SCREEN_W - self.w, self.x + dx))
        self.y = max(0, min(SCREEN_H - self.h, self.y + dy))
        self.update_position()

    def resize(self, dx, dy):
        new_w = max(100, self.w + dx)
        new_h = max(50, self.h + dy)
        self.w = min(new_w, SCREEN_W - self.x)
        self.h = min(new_h, SCREEN_H - self.y)
        self.update_position()

    def to_dict(self):
        return {"x": int(self.x), "y": int(self.y), "w": int(self.w), "h": int(self.h)}


class LayoutEditor:
    def __init__(self, parent=None):
        self.standalone = parent is None
        self.root = tk.Tk() if self.standalone else tk.Toplevel(parent)

        global SCREEN_W, SCREEN_H
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            if sw > 0 and sh > 0:
                SCREEN_W = sw
                SCREEN_H = sh
        except Exception:
            pass

        self.root.title("Conky Layout Editor")
        self.root.geometry(f"{int(SCREEN_W * SCALE) + 60}x{int(SCREEN_H * SCALE) + 120}")
        self.root.minsize(500, 400)

        self.widgets = {}
        self.selected = None
        self.mode = "move"
        self.drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self.load_widgets()
        if self.standalone:
            self.root.mainloop()

    def setup_ui(self):
        global SCALE
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Apply", command=self.apply_positions).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=2)
        self.zoom_label = ttk.Label(toolbar, text=f"{int(SCALE * 100)}%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=2)

        self.mode_var = tk.StringVar(value="move")
        ttk.Radiobutton(toolbar, text="Move", variable=self.mode_var, value="move").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(toolbar, text="Resize", variable=self.mode_var, value="resize").pack(side=tk.LEFT, padx=2)

        # Screen label
        ttk.Label(toolbar, text=f"Screen: {SCREEN_W}x{SCREEN_H}").pack(side=tk.RIGHT, padx=5)

        # Canvas
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=int(SCREEN_W * SCALE),
            height=int(SCREEN_H * SCALE),
            bg="#1a1a2e", highlightthickness=1, highlightbackground="#444444"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Grid lines
        for x in range(0, SCREEN_W, 100):
            sx = x * SCALE
            self.canvas.create_line(sx, 0, sx, SCREEN_H * SCALE, fill="#333333", dash=(2, 4))
        for y in range(0, SCREEN_H, 100):
            sy = y * SCALE
            self.canvas.create_line(0, sy, SCREEN_W * SCALE, sy, fill="#333333", dash=(2, 4))

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def get_running_themes(self):
        """Get list of currently running theme directory names"""
        running = set()
        try:
            result = subprocess.run(['pgrep', '-a', 'conky'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) > 1:
                    # Find -c argument
                    for i, part in enumerate(parts):
                        if part == '-c' and i + 1 < len(parts):
                            config_path = parts[i + 1]
                            # Extract theme name from path like /home/user/.config/conky/theme-name/conkyrc
                            parts_path = config_path.split('/')
                            if 'conky' in parts_path:
                                idx = parts_path.index('conky')
                                if idx + 1 < len(parts_path):
                                    theme_dir = parts_path[idx + 1]
                                    running.add(theme_dir)
        except Exception:
            pass
        return running

    def load_widgets(self):
        layout = load_layout()
        running = self.get_running_themes()
        default_widgets = {
            "crypto-conky-manager": {"x": 30, "y": 720, "w": 250, "h": 250, "color": "#e94560"},
            "kev-conky-manager": {"x": 1640, "y": 870, "w": 250, "h": 250, "color": "#ff4444"},
            "infra-conky-manager": {"x": 30, "y": 980, "w": 250, "h": 250, "color": "#ff8800"},
            "bandwidth-conky-manager": {"x": 30, "y": 400, "w": 220, "h": 120, "color": "#4488ff"},
            "network-conky-manager": {"x": 30, "y": 540, "w": 220, "h": 160, "color": "#44aaff"},
            "processes-conky-manager": {"x": 1670, "y": 300, "w": 250, "h": 220, "color": "#ff88ff"},
            "docker-conky-manager": {"x": 1670, "y": 540, "w": 250, "h": 180, "color": "#88ff88"},
            "k8s-conky-manager": {"x": 1670, "y": 740, "w": 250, "h": 140, "color": "#ffff44"},
            "weather-conky-manager": {"x": 1800, "y": 20, "w": 80, "h": 80, "color": "#4488ff"},
            "calendar-conky-manager": {"x": 660, "y": 50, "w": 600, "h": 500, "color": "#44ff88"},
            "claude-conky-manager": {"x": 1520, "y": 470, "w": 300, "h": 300, "color": "#8888ff"},
            "revisited-conky-manager": {"x": 0, "y": 470, "w": 640, "h": 400, "color": "#884488"},
        }

        for name, defaults in default_widgets.items():
            if name not in running:
                continue
            pos = layout.get(name, defaults)
            self.widgets[name] = WidgetRect(
                self.canvas, name,
                pos.get("x", defaults["x"]),
                pos.get("y", defaults["y"]),
                pos.get("w", defaults["w"]),
                pos.get("h", defaults["h"]),
                pos.get("color", defaults["color"]),
            )

    def on_press(self, event):
        self.drag_data = {"x": event.x, "y": event.y}
        # Find clicked widget
        items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag in self.widgets:
                    self.selected = tag
                    # Check if clicking resize handle
                    if "resize_handle" in tags:
                        self.mode_var.set("resize")
                    return
        self.selected = None

    def on_drag(self, event):
        if not self.selected or self.selected not in self.widgets:
            return
        dx = (event.x - self.drag_data["x"]) / SCALE
        dy = (event.y - self.drag_data["y"]) / SCALE
        self.drag_data = {"x": event.x, "y": event.y}

        widget = self.widgets[self.selected]
        if self.mode_var.get() == "resize":
            widget.resize(dx, dy)
        else:
            widget.move(dx, dy)

    def on_release(self, event):
        self.drag_data = {"x": 0, "y": 0}

    def zoom_in(self):
        global SCALE
        SCALE = min(1.5, SCALE + 0.1)
        self.redraw_canvas()

    def zoom_out(self):
        global SCALE
        SCALE = max(0.2, SCALE - 0.1)
        self.redraw_canvas()

    def redraw_canvas(self):
        self.zoom_label.config(text=f"{int(SCALE * 100)}%")
        # Save current positions
        saved = {}
        for name, w in self.widgets.items():
            saved[name] = (w.x, w.y, w.w, w.h, w.color)
        # Resize canvas
        new_w = int(SCREEN_W * SCALE)
        new_h = int(SCREEN_H * SCALE)
        self.canvas.config(width=new_w, height=new_h)
        self.root.geometry(f"{new_w + 60}x{new_h + 120}")
        # Clear and redraw
        self.canvas.delete("all")
        # Grid lines
        for x in range(0, SCREEN_W, 100):
            sx = x * SCALE
            self.canvas.create_line(sx, 0, sx, new_h, fill="#333333", dash=(2, 4))
        for y in range(0, SCREEN_H, 100):
            sy = y * SCALE
            self.canvas.create_line(0, sy, new_w, sy, fill="#333333", dash=(2, 4))
        # Redraw widgets
        self.widgets.clear()
        for name, (x, y, w, h, color) in saved.items():
            self.widgets[name] = WidgetRect(self.canvas, name, x, y, w, h, color)

    def save(self):
        layout = {}
        for name, widget in self.widgets.items():
            layout[name] = widget.to_dict()
        save_layout(layout)
        print(f"Layout saved to {LAYOUT_FILE}")

    def reset(self):
        for name in self.widgets:
            w = self.widgets[name]
            self.canvas.delete(w.rect)
            self.canvas.delete(w.label)
            self.canvas.delete(w.resize_handle)
        self.widgets.clear()
        self.load_widgets()

    def apply_positions(self):
        self.save()
        conky_config = Path.home() / ".config" / "conky"
        updated_themes = set()
        for name, widget in self.widgets.items():
            theme_dir = conky_config / name
            updated = False

            # Try settings.lua (Lua position patterns)
            lua_file = theme_dir / "settings.lua"
            if lua_file.exists():
                self.update_lua_position(lua_file, widget)
                updated = True

            # Try conkyrc (gap_x/gap_y/minimum_width/minimum_height patterns)
            conkyrc = theme_dir / "conkyrc"
            if conkyrc.exists():
                self.update_conkyrc_position(conkyrc, widget)
                updated = True

            if updated:
                updated_themes.add(name)

        # Restart updated themes so gap_x/gap_y changes take effect
        if updated_themes:
            self.restart_themes(updated_themes)

    def update_conkyrc_position(self, conkyrc, widget):
        with open(conkyrc) as f:
            content = f.read()

        import re

        content = re.sub(
            r'(gap_x\s*=\s*)\d+',
            f'\\g<1>{int(widget.x)}',
            content
        )
        content = re.sub(
            r'(gap_y\s*=\s*)\d+',
            f'\\g<1>{int(widget.y)}',
            content
        )
        content = re.sub(
            r'(minimum_width\s*=\s*)\d+',
            f'\\g<1>{int(widget.w)}',
            content
        )
        content = re.sub(
            r'(minimum_height\s*=\s*)\d+',
            f'\\g<1>{int(widget.h)}',
            content
        )

        with open(conkyrc, "w") as f:
            f.write(content)
        print(f"Updated {conkyrc}")

    def update_lua_position(self, lua_file, widget):
        with open(lua_file) as f:
            content = f.read()

        import re

        # Pattern 1a: local widget_x = w - N (right-aligned)
        offset_x = SCREEN_W - widget.x
        content = re.sub(
            r'(local widget_x\s*=\s*w\s*-\s*)[\d.]+',
            f'\\g<1>{offset_x}',
            content
        )

        # Pattern 1b: local widget_x = N (left-aligned)
        content = re.sub(
            r'(local widget_x\s*=\s*)[\d.]+',
            f'\\g<1>{int(widget.x)}',
            content
        )

        # Pattern 1c: local widget_y = N
        content = re.sub(
            r'(local widget_y\s*=\s*)[\d.]+',
            f'\\g<1>{int(widget.y)}',
            content
        )

        # Pattern 2: local w, h = N, N (widget size)
        content = re.sub(
            r'(local w\s*,\s*h\s*=\s*)\d+\s*,\s*\d+',
            f'\\g<1>{int(widget.w)}, {int(widget.h)}',
            content
        )

        # Pattern 3a: local x = w - N (right-aligned system widgets)
        offset_x = SCREEN_W - widget.x
        content = re.sub(
            r'(local x\s*=\s*w\s*-\s*)[\d.]+',
            f'\\g<1>{offset_x}',
            content
        )

        # Pattern 3b: local x = N (left-aligned system widgets)
        content = re.sub(
            r'(local x\s*=\s*)[\d.]+(?!\s*\+)',
            f'\\g<1>{int(widget.x)}',
            content
        )

        # Pattern 4a: local y = (h - widget_h) / 2 (first time)
        center_y = widget.y + widget.h // 2
        content = re.sub(
            r'(local y\s*=\s*\(h\s*-\s*widget_h\s*\)\s*/\s*2)',
            f'local y = {center_y} - widget_h / 2',
            content
        )

        # Pattern 4b: local y = N - widget_h / 2 (already converted)
        content = re.sub(
            r'(local y\s*=\s*)[\d.]+\s*-\s*widget_h\s*/\s*2',
            f'\\g<1>{center_y} - widget_h / 2',
            content
        )

        # Pattern 5: local widget_h = N
        content = re.sub(
            r'(local widget_h\s*=\s*)\d+',
            f'\\g<1>{int(widget.h)}',
            content
        )

        # Pattern 6: pos_x = w-N (weather - right-aligned)
        offset_x = SCREEN_W - widget.x
        content = re.sub(
            r'(local pos_x\s*=\s*w\s*-\s*)[\d.]+',
            f'\\g<1>{offset_x}',
            content
        )

        # Pattern 7: pos_y = N (weather)
        center_y = widget.y + widget.h // 2
        content = re.sub(
            r'(local pos_y\s*=\s*)[\d.]+',
            f'\\g<1>{center_y}',
            content
        )

        with open(lua_file, "w") as f:
            f.write(content)
        print(f"Updated {lua_file}")

    def restart_themes(self, theme_names):
        for name in theme_names:
            conky_config = Path.home() / ".config" / "conky"
            conkyrc = conky_config / name / "conkyrc"
            if not conkyrc.exists():
                continue
            # Kill existing conky process for this theme
            try:
                subprocess.run(
                    ['pkill', '-f', f'conky.*-c.*{name}'],
                    timeout=5
                )
            except Exception:
                pass
            # Restart conky
            try:
                subprocess.Popen(
                    ['conky', '-c', str(conkyrc), '-d', '-m', '0'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Restarted {name}")
            except Exception as e:
                print(f"Failed to restart {name}: {e}")


if __name__ == "__main__":
    LayoutEditor()
