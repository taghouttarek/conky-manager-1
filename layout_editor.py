#!/usr/bin/env python3
"""Layout Editor - Drag and drop interface for positioning conky widgets"""
import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path

LAYOUT_FILE = Path.home() / ".config" / "conky" / "layout.json"
SCREEN_W = 1920
SCREEN_H = 1080
SCALE = 0.4  # Canvas scale factor


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
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Conky Layout Editor")
        self.root.geometry(f"{int(SCREEN_W * SCALE) + 40}x{int(SCREEN_H * SCALE) + 120}")

        self.widgets = {}
        self.selected = None
        self.mode = "move"  # "move" or "resize"
        self.drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self.load_widgets()
        self.root.mainloop()

    def setup_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Apply", command=self.apply_positions).pack(side=tk.LEFT, padx=2)

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

    def load_widgets(self):
        layout = load_layout()
        default_widgets = {
            "crypto": {"x": 30, "y": 720, "w": 250, "h": 250, "color": "#e94560"},
            "kev": {"x": 1640, "y": 870, "w": 250, "h": 250, "color": "#ff4444"},
            "infra": {"x": 30, "y": 980, "w": 250, "h": 250, "color": "#ff8800"},
        }

        for name, defaults in default_widgets.items():
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

    def save(self):
        layout = {}
        for name, widget in self.widgets.items():
            layout[name] = widget.to_dict()
        save_layout(layout)
        print(f"Layout saved to {LAYOUT_FILE}")

    def reset(self):
        for name in self.widgets:
            self.canvas.delete(name)
            self.canvas.delete(f"{name}_label")
        self.widgets.clear()
        self.load_widgets()

    def apply_positions(self):
        self.save()
        # Update conky lua files with new positions
        conky_config = Path.home() / ".config" / "conky"
        for name, widget in self.widgets.items():
            lua_file = conky_config / name / "settings.lua"
            if not lua_file.exists():
                # Try alternate names
                alt_names = {"kev": "security-vulns", "infra": "infra-vulns"}
                if name in alt_names:
                    lua_file = conky_config / alt_names[name] / "settings.lua"
            if lua_file.exists():
                self.update_lua_position(lua_file, widget)

    def update_lua_position(self, lua_file, widget):
        with open(lua_file) as f:
            content = f.read()

        # Find and replace widget_x and widget_y in draw_function
        import re
        content = re.sub(
            r'(local widget_x\s*=\s*)\d+',
            f'\\g<1>{int(widget.x)}',
            content
        )
        content = re.sub(
            r'(local widget_y\s*=\s*)\d+',
            f'\\g<1>{int(widget.y)}',
            content
        )
        content = re.sub(
            r'(local w\s*,\s*h\s*=\s*)\d+\s*,\s*\d+',
            f'\\g<1>{int(widget.w)}, {int(widget.h)}',
            content
        )

        with open(lua_file, "w") as f:
            f.write(content)
        print(f"Updated {lua_file}")


if __name__ == "__main__":
    LayoutEditor()
