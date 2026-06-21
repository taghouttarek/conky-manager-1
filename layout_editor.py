#!/usr/bin/env python3
"""Layout Editor - Drag and drop interface for positioning conky widgets"""
import tkinter as tk
from tkinter import ttk
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

LAYOUT_FILE = Path.home() / ".config" / "conky" / "layout.json"
POSITIONS_FILE = Path.home() / ".config" / "conky" / "positions.lua"
DEFAULT_SCREEN_W = 1920
DEFAULT_SCREEN_H = 1080
DEFAULT_SCALE = 0.5
RESOLUTION_PRESETS = ["1920x1080", "2560x1440", "3840x2160", "Custom"]
MIN_SCREEN_W = 800
MIN_SCREEN_H = 600
MAX_SCREEN_W = 7680
MAX_SCREEN_H = 4320


def detect_monitors():
    """Detect connected monitors via xrandr. Returns list of dicts."""
    monitors = []
    try:
        result = subprocess.run(
            ['xrandr', '--listmonitors'], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if parts and parts[0].rstrip(':').isdigit():
                idx = int(parts[0].rstrip(':'))
                name = parts[-1]
                geom = parts[2]
                w_str = geom.split('x')[0].split('/')[0]
                h_str = geom.split('x')[1].split('/')[0]
                w, h = int(w_str), int(h_str)
                monitors.append({"index": idx, "name": name, "w": w, "h": h})
    except Exception:
        pass
    if not monitors:
        monitors.append({"index": 0, "name": "default", "w": DEFAULT_SCREEN_W, "h": DEFAULT_SCREEN_H})
    return monitors


def load_layout():
    if LAYOUT_FILE.exists():
        try:
            with open(LAYOUT_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return {}


def save_layout(data):
    LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=LAYOUT_FILE.parent, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, LAYOUT_FILE)


def save_positions(screen_w, screen_h, monitor, widgets):
    """Write shared positions.lua for all themes."""
    POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "-- Shared widget positions and screen config",
        "-- Managed by Conky Layout Editor - do not edit manually",
        f"screen = {{w = {int(screen_w)}, h = {int(screen_h)}, monitor = {int(monitor)}}}",
        "positions = {",
    ]
    for name, widget in sorted(widgets.items()):
        lines.append(f'    ["{name}"] = {{x = {int(widget.x)}, y = {int(widget.y)}}},')
    lines.append("}")
    lines.append("")

    fd, tmp = tempfile.mkstemp(dir=POSITIONS_FILE.parent, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    os.replace(tmp, POSITIONS_FILE)


class WidgetRect:
    def __init__(self, canvas, name, x, y, w, h, color="#ffffff",
                 screen_w=DEFAULT_SCREEN_W, screen_h=DEFAULT_SCREEN_H,
                 scale=DEFAULT_SCALE):
        self.canvas = canvas
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.scale = scale
        self.rect = None
        self.label = None
        self.resize_handle = None
        self.drag_data = {"x": 0, "y": 0}
        self.resizing = False
        self.draw()

    def draw(self):
        s = self.scale
        sx, sy = self.x * s, self.y * s
        sw, sh = self.w * s, self.h * s
        self.rect = self.canvas.create_rectangle(
            sx, sy, sx + sw, sy + sh,
            fill=self.color, outline="#888888", width=1, stipple="gray25",
            tags=("widget", self.name)
        )
        self.label = self.canvas.create_text(
            sx + sw / 2, sy + sh / 2,
            text=self.name, fill="white", font=("Dejavu Sans", 8, "bold"),
            tags=("widget_label", self.name)
        )
        hr = 5
        self.resize_handle = self.canvas.create_rectangle(
            sx + sw - hr, sy + sh - hr, sx + sw + hr, sy + sh + hr,
            fill="#ff4444", outline="#ffffff", width=1,
            tags=("resize_handle", self.name)
        )

    def update_position(self):
        s = self.scale
        sx, sy = self.x * s, self.y * s
        sw, sh = self.w * s, self.h * s
        self.canvas.coords(self.rect, sx, sy, sx + sw, sy + sh)
        self.canvas.coords(self.label, sx + sw / 2, sy + sh / 2)
        hr = 5
        self.canvas.coords(self.resize_handle,
                           sx + sw - hr, sy + sh - hr,
                           sx + sw + hr, sy + sh + hr)

    def move(self, dx, dy):
        self.x = max(0, min(self.screen_w - self.w, self.x + dx))
        self.y = max(0, min(self.screen_h - self.h, self.y + dy))
        self.update_position()

    def resize(self, dx, dy):
        new_w = max(100, self.w + dx)
        new_h = max(50, self.h + dy)
        self.w = min(new_w, self.screen_w - self.x)
        self.h = min(new_h, self.screen_h - self.y)
        self.update_position()

    def to_dict(self):
        return {"x": int(self.x), "y": int(self.y),
                "w": int(self.w), "h": int(self.h)}


class LayoutEditor:
    def __init__(self, parent=None):
        self.standalone = parent is None
        self.root = tk.Tk() if self.standalone else tk.Toplevel(parent)

        self.screen_w = DEFAULT_SCREEN_W
        self.screen_h = DEFAULT_SCREEN_H
        self.scale = DEFAULT_SCALE
        self.monitor = 0

        self.monitors = detect_monitors()
        if self.monitors:
            self.screen_w = self.monitors[0]["w"]
            self.screen_h = self.monitors[0]["h"]
            self.monitor = self.monitors[0]["index"]

        self.root.title("Conky Layout Editor")
        self._update_geometry()
        self.root.minsize(500, 400)

        self.widgets = {}
        self.selected = None
        self.mode = "move"
        self.drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self.load_widgets()
        if self.standalone:
            self.root.mainloop()

    def _update_geometry(self):
        w = int(self.screen_w * self.scale) + 60
        h = int(self.screen_h * self.scale) + 120
        self.root.geometry(f"{w}x{h}")

    def _monitor_label(self, m):
        return f"{m['name']} ({m['w']}x{m['h']})"

    def setup_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Apply", command=self.apply_positions).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=2)
        self.zoom_label = ttk.Label(toolbar, text=f"{int(self.scale * 100)}%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=2)

        self.mode_var = tk.StringVar(value="move")
        ttk.Radiobutton(toolbar, text="Move", variable=self.mode_var, value="move").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(toolbar, text="Resize", variable=self.mode_var, value="resize").pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Detect button
        ttk.Button(toolbar, text="Detect", command=self._on_detect).pack(side=tk.LEFT, padx=2)

        # Monitor dropdown
        self.monitor_var = tk.StringVar()
        self.monitor_labels = [self._monitor_label(m) for m in self.monitors]
        self.monitor_combo = ttk.Combobox(
            toolbar, textvariable=self.monitor_var,
            values=self.monitor_labels, width=25, state="readonly"
        )
        self.monitor_combo.pack(side=tk.LEFT, padx=2)
        self.monitor_combo.bind("<<ComboboxSelected>>", self._on_monitor_change)
        # Set initial selection
        if self.monitor_labels:
            self.monitor_combo.current(0)

        # Resolution preset dropdown
        self.resolution_var = tk.StringVar(value=self._current_preset())
        self.resolution_combo = ttk.Combobox(
            toolbar, textvariable=self.resolution_var,
            values=RESOLUTION_PRESETS, width=12, state="readonly"
        )
        self.resolution_combo.pack(side=tk.LEFT, padx=2)
        self.resolution_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Width/Height entry fields
        ttk.Label(toolbar, text="W:").pack(side=tk.LEFT, padx=(8, 2))
        self.width_var = tk.StringVar(value=str(self.screen_w))
        self.width_entry = ttk.Entry(toolbar, textvariable=self.width_var, width=6)
        self.width_entry.pack(side=tk.LEFT, padx=2)
        self.width_entry.bind("<Return>", self._on_resolution_entry)
        self.width_entry.bind("<FocusOut>", self._on_resolution_entry)

        ttk.Label(toolbar, text="H:").pack(side=tk.LEFT, padx=(4, 2))
        self.height_var = tk.StringVar(value=str(self.screen_h))
        self.height_entry = ttk.Entry(toolbar, textvariable=self.height_var, width=6)
        self.height_entry.pack(side=tk.LEFT, padx=2)
        self.height_entry.bind("<Return>", self._on_resolution_entry)
        self.height_entry.bind("<FocusOut>", self._on_resolution_entry)

        # Canvas
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=int(self.screen_w * self.scale),
            height=int(self.screen_h * self.scale),
            bg="#1a1a2e", highlightthickness=1, highlightbackground="#444444"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Grid lines
        self._draw_grid()

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def _draw_grid(self):
        sw = int(self.screen_w * self.scale)
        sh = int(self.screen_h * self.scale)
        for x in range(0, self.screen_w, 100):
            sx = x * self.scale
            self.canvas.create_line(sx, 0, sx, sh, fill="#333333", dash=(2, 4))
        for y in range(0, self.screen_h, 100):
            sy = y * self.scale
            self.canvas.create_line(0, sy, sw, sy, fill="#333333", dash=(2, 4))

    def _current_preset(self):
        key = f"{self.screen_w}x{self.screen_h}"
        if key in RESOLUTION_PRESETS:
            return key
        return "Custom"

    def _on_detect(self):
        """Re-detect monitors and refresh dropdown."""
        self.monitors = detect_monitors()
        self.monitor_labels = [self._monitor_label(m) for m in self.monitors]
        self.monitor_combo["values"] = self.monitor_labels
        if self.monitor_labels:
            self.monitor_combo.current(0)
            self._apply_monitor(0)

    def _on_monitor_change(self, event=None):
        idx = self.monitor_combo.current()
        if 0 <= idx < len(self.monitors):
            self._apply_monitor(idx)

    def _apply_monitor(self, idx):
        m = self.monitors[idx]
        self.monitor = m["index"]
        self.screen_w = m["w"]
        self.screen_h = m["h"]
        self.width_var.set(str(self.screen_w))
        self.height_var.set(str(self.screen_h))
        preset = f"{self.screen_w}x{self.screen_h}"
        self.resolution_var.set(preset if preset in RESOLUTION_PRESETS else "Custom")
        self.redraw_canvas()

    def _on_preset_change(self, event=None):
        preset = self.resolution_var.get()
        if preset == "Custom":
            return
        w, h = preset.split("x")
        self._change_resolution(int(w), int(h))

    def _on_resolution_entry(self, event=None):
        try:
            w = int(self.width_var.get().strip())
            h = int(self.height_var.get().strip())
        except ValueError:
            self.width_var.set(str(self.screen_w))
            self.height_var.set(str(self.screen_h))
            return
        w = max(MIN_SCREEN_W, min(MAX_SCREEN_W, w))
        h = max(MIN_SCREEN_H, min(MAX_SCREEN_H, h))
        self._change_resolution(w, h)

    def _change_resolution(self, new_w, new_h):
        if new_w == self.screen_w and new_h == self.screen_h:
            return
        old_w, old_h = self.screen_w, self.screen_h
        sx = new_w / old_w
        sy = new_h / old_h

        for widget in self.widgets.values():
            widget.x = int(widget.x * sx)
            widget.y = int(widget.y * sy)
            widget.w = int(widget.w * sx)
            widget.h = int(widget.h * sy)
            widget.screen_w = new_w
            widget.screen_h = new_h

        self.screen_w = new_w
        self.screen_h = new_h

        self.width_var.set(str(new_w))
        self.height_var.set(str(new_h))
        preset = f"{new_w}x{new_h}"
        self.resolution_var.set(preset if preset in RESOLUTION_PRESETS else "Custom")

        self.redraw_canvas()

    def get_running_themes(self):
        """Get list of currently running theme directory names"""
        running = set()
        try:
            result = subprocess.run(['pgrep', '-a', 'conky'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) > 1:
                    for i, part in enumerate(parts):
                        if part == '-c' and i + 1 < len(parts):
                            config_path = parts[i + 1]
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

        # Load resolution and monitor from layout
        res = layout.get("resolution")
        if res:
            self.screen_w = res.get("w", self.screen_w)
            self.screen_h = res.get("h", self.screen_h)
            self.width_var.set(str(self.screen_w))
            self.height_var.set(str(self.screen_h))
            preset = f"{self.screen_w}x{self.screen_h}"
            self.resolution_var.set(preset if preset in RESOLUTION_PRESETS else "Custom")

        self.monitor = layout.get("monitor", 0)
        # Update monitor dropdown to match stored monitor
        for i, m in enumerate(self.monitors):
            if m["index"] == self.monitor:
                self.monitor_combo.current(i)
                break

        self._update_geometry()

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
                screen_w=self.screen_w,
                screen_h=self.screen_h,
                scale=self.scale,
            )

    def on_press(self, event):
        self.drag_data = {"x": event.x, "y": event.y}
        items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag in self.widgets:
                    self.selected = tag
                    if "resize_handle" in tags:
                        self.mode_var.set("resize")
                    return
        self.selected = None

    def on_drag(self, event):
        if not self.selected or self.selected not in self.widgets:
            return
        dx = (event.x - self.drag_data["x"]) / self.scale
        dy = (event.y - self.drag_data["y"]) / self.scale
        self.drag_data = {"x": event.x, "y": event.y}

        widget = self.widgets[self.selected]
        if self.mode_var.get() == "resize":
            widget.resize(dx, dy)
        else:
            widget.move(dx, dy)

    def on_release(self, event):
        self.drag_data = {"x": 0, "y": 0}

    def zoom_in(self):
        self.scale = min(1.5, self.scale + 0.1)
        self.redraw_canvas()

    def zoom_out(self):
        self.scale = max(0.2, self.scale - 0.1)
        self.redraw_canvas()

    def redraw_canvas(self):
        self.zoom_label.config(text=f"{int(self.scale * 100)}%")
        saved = {}
        for name, w in self.widgets.items():
            saved[name] = (w.x, w.y, w.w, w.h, w.color)
        new_w = int(self.screen_w * self.scale)
        new_h = int(self.screen_h * self.scale)
        self.canvas.config(width=new_w, height=new_h)
        self.root.geometry(f"{new_w + 60}x{new_h + 120}")
        self.canvas.delete("all")
        self.selected = None
        self._draw_grid()
        self.widgets.clear()
        for name, (x, y, w, h, color) in saved.items():
            self.widgets[name] = WidgetRect(
                self.canvas, name, x, y, w, h, color,
                screen_w=self.screen_w, screen_h=self.screen_h,
                scale=self.scale
            )

    def save(self):
        layout = {
            "resolution": {"w": self.screen_w, "h": self.screen_h},
            "monitor": self.monitor,
        }
        for name, widget in self.widgets.items():
            layout[name] = widget.to_dict()
        save_layout(layout)
        save_positions(self.screen_w, self.screen_h, self.monitor, self.widgets)
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
            try:
                theme_dir = conky_config / name
                conkyrc = theme_dir / "conkyrc"
                if conkyrc.exists():
                    self.update_conkyrc_position(conkyrc, widget)
                updated_themes.add(name)
            except Exception as e:
                print(f"Error updating {name}: {e}")

        if updated_themes:
            self.restart_themes(updated_themes)

    def update_conkyrc_position(self, conkyrc, widget):
        target = conkyrc.resolve()
        with open(target, encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'(gap_x\s*=\s*)-?\d+',
            f'\\g<1>0',
            content
        )
        new_content = re.sub(
            r'(gap_y\s*=\s*)-?\d+',
            f'\\g<1>0',
            new_content
        )
        new_content = re.sub(
            r'(minimum_width\s*=\s*)-?\d+',
            f'\\g<1>{int(self.screen_w)}',
            new_content
        )
        new_content = re.sub(
            r'(minimum_height\s*=\s*)-?\d+',
            f'\\g<1>{int(self.screen_h)}',
            new_content
        )

        if new_content != content:
            with open(target, "w", encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {conkyrc}")

    def restart_themes(self, theme_names):
        conky_config = Path.home() / ".config" / "conky"
        # Kill phase
        for name in theme_names:
            conkyrc = conky_config / name / "conkyrc"
            if not conkyrc.exists():
                continue
            config_path = str(conkyrc)
            try:
                result = subprocess.run(
                    ['pgrep', '-a', 'conky'], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if config_path in line:
                        parts = line.split()
                        if parts and parts[0].isdigit():
                            subprocess.run(['kill', parts[0]], timeout=5)
            except Exception as e:
                print(f"Error killing {name}: {e}")
        time.sleep(0.5)
        # Restart phase
        for name in theme_names:
            conkyrc = conky_config / name / "conkyrc"
            if not conkyrc.exists():
                continue
            try:
                subprocess.Popen(
                    ['conky', '-c', str(conkyrc), '-d', '-m', str(self.monitor)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                print(f"Restarted {name} on monitor {self.monitor}")
            except Exception as e:
                print(f"Failed to restart {name}: {e}")


if __name__ == "__main__":
    LayoutEditor()
