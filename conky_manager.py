#!/usr/bin/env python3
"""
Conky Manager - A full-featured Python Conky Theme Manager
Features:
- Theme discovery from ~/.conky/
- Theme switching
- Archive import (zip, tar, tar.gz, tar.xz, 7z)
- Folder import
- Autostart configuration
- Theme editing
- Theme deletion
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
import tarfile
import threading
from pathlib import Path
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("tkinter not found. Install with: sudo apt install python3-tk")
    sys.exit(1)

import layout_editor

# Constants
HOME = Path.home()
CONKY_DIR = HOME / ".conky"
CONKY_CONFIG_DIR = HOME / ".config" / "conky"
AUTOSTART_DIR = HOME / ".config" / "autostart"
DATA_DIR = HOME / ".local" / "share" / "conky-manager"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOG_FILE = DATA_DIR / "manager.log"
VERSION = "2.0.5"
REPO_URL = "https://github.com/taghouti-org/conky-manager.git"

# Supported archive extensions
ARCHIVE_EXTENSIONS = {
    '.zip': 'zip',
    '.tar': 'tar',
    '.tar.gz': 'tar.gz',
    '.tgz': 'tar.gz',
    '.tar.xz': 'tar.xz',
    '.txz': 'tar.xz',
    '.tar.bz2': 'tar.bz2',
    '.tbz2': 'tar.bz2',
    '.7z': '7z',
}


class ConkyManager:
    """Main Conky Manager class"""

    def __init__(self):
        self.ensure_directories()
        self.settings = self.load_settings()
        self.themes = []
        self.current_theme = self.settings.get("current_theme", None)
        self.scan_themes()

    def ensure_directories(self):
        """Create necessary directories"""
        for d in [CONKY_DIR, CONKY_CONFIG_DIR, AUTOSTART_DIR, DATA_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def load_settings(self):
        """Load settings from JSON file"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Error loading settings: {e}")
        return {
            "current_theme": None,
            "autostart_enabled": False,
            "window_position": {"x": 100, "y": 100},
            "running_themes": [],
        }

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.log(f"Error saving settings: {e}")

    def log(self, message):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_line + "\n")
        except Exception:
            pass

    def scan_themes(self):
        """Scan for conky themes in all known directories"""
        self.themes = []
        scanned_configs = set()
        scanned_names = set()

        # Scan directories
        dirs_to_scan = [
            CONKY_DIR,
            CONKY_CONFIG_DIR,
        ]

        for scan_dir in dirs_to_scan:
            if not scan_dir.exists():
                continue
            for item in scan_dir.iterdir():
                if item.is_dir():
                    theme = self.analyze_theme_dir(item)
                    if theme and theme['config'] not in scanned_configs and theme['name'] not in scanned_names:
                        scanned_configs.add(theme['config'])
                        scanned_names.add(theme['name'])
                        self.themes.append(theme)
                elif item.is_file() and item.suffix in ('.conf', '.cfg'):
                    # Single config files
                    theme = self.analyze_theme_file(item)
                    if theme and theme['config'] not in scanned_configs and theme['name'] not in scanned_names:
                        scanned_configs.add(theme['config'])
                        scanned_names.add(theme['name'])
                        self.themes.append(theme)

        # Also check for .conkyrc files
        for scan_dir in dirs_to_scan:
            if not scan_dir.exists():
                continue
            for item in scan_dir.iterdir():
                if item.is_file() and item.name in ('.conkyrc', 'conkyrc'):
                    # Check if already added
                    if item.name not in scanned_configs and str(item) not in scanned_configs:
                        theme = self.analyze_theme_file(item)
                        if theme and theme['config'] not in scanned_configs and theme['name'] not in scanned_names:
                            scanned_configs.add(theme['config'])
                            scanned_names.add(theme['name'])
                            self.themes.append(theme)

        self.log(f"Found {len(self.themes)} themes")
        return self.themes

    def analyze_theme_dir(self, dir_path):
        """Analyze a directory for conky theme files"""
        config_file = None
        for name in ['.conkyrc', 'conkyrc', '.conf', 'config.conf', 'conky.conf']:
            candidate = dir_path / name
            if candidate.exists():
                config_file = candidate
                break

        if not config_file:
            # Check for any .conf files
            for f in dir_path.glob('*.conf'):
                config_file = f
                break

        if not config_file:
            return None

        return {
            'name': dir_path.name,
            'path': str(dir_path),
            'config': str(config_file),
            'type': 'directory',
            'has_lua': any(dir_path.glob('*.lua')),
            'has_images': any(dir_path.glob('*.png')) or any(dir_path.glob('*.jpg')),
        }

    def analyze_theme_file(self, file_path):
        """Analyze a single config file"""
        parent_dir = file_path.parent
        return {
            'name': parent_dir.name if parent_dir != CONKY_DIR else file_path.stem,
            'path': str(parent_dir),
            'config': str(file_path),
            'type': 'file',
            'has_lua': any(parent_dir.glob('*.lua')),
            'has_images': any(parent_dir.glob('*.png')) or any(parent_dir.glob('*.jpg')),
        }

    def get_monitor_index(self):
        """Get current monitor index from layout.json."""
        try:
            layout_file = Path.home() / ".config" / "conky" / "layout.json"
            if layout_file.exists():
                with open(layout_file) as f:
                    data = json.load(f)
                return data.get("monitor", 0)
        except Exception:
            pass
        return 0

    def start_conky(self, theme):
        """Start conky with a specific theme"""
        config_path = theme['config']
        if not os.path.exists(config_path):
            self.log(f"Config file not found: {config_path}")
            return False

        # Check if this theme is already running
        if self.is_theme_running(theme):
            self.log(f"Theme already running: {theme['name']}")
            return True

        try:
            monitor = self.get_monitor_index()
            cmd = ['conky', '-c', config_path, '-d', '-m', str(monitor)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if 'running_themes' not in self.settings:
                self.settings['running_themes'] = []
            if theme['name'] not in self.settings['running_themes']:
                self.settings['running_themes'].append(theme['name'])
            self.save_settings()
            self.log(f"Started conky with theme: {theme['name']} on monitor {monitor}")
            return True
        except Exception as e:
            self.log(f"Error starting conky: {e}")
            return False

    def stop_theme(self, theme):
        """Stop a specific conky theme"""
        try:
            # Find and kill conky processes running this theme's config
            result = subprocess.run(['pgrep', '-f', theme['config']], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for pid in result.stdout.strip().split('\n'):
                    if pid:
                        subprocess.run(['kill', pid], capture_output=True, timeout=5)
            if 'running_themes' in self.settings and theme['name'] in self.settings['running_themes']:
                self.settings['running_themes'].remove(theme['name'])
                self.save_settings()
            self.log(f"Stopped theme: {theme['name']}")
            return True
        except (subprocess.TimeoutExpired, Exception) as e:
            self.log(f"Error stopping theme: {e}")
            return False

    def stop_conky(self):
        """Stop all conky instances"""
        try:
            subprocess.run(['pkill', 'conky'], capture_output=True, timeout=5)
            self.settings['running_themes'] = []
            self.save_settings()
            self.log("Stopped conky")
            return True
        except (subprocess.TimeoutExpired, Exception) as e:
            self.log(f"Error stopping conky: {e}")
            return False

    def is_theme_running(self, theme):
        """Check if a specific theme is running"""
        try:
            result = subprocess.run(['pgrep', '-f', theme['config']], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False

    def is_conky_running(self):
        """Check if conky is running"""
        try:
            result = subprocess.run(['pgrep', 'conky'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False

    def find_theme_by_name(self, name):
        """Find a theme by name"""
        for theme in self.themes:
            if theme['name'] == name:
                return theme
        return None

    def import_archive(self, archive_path, theme_name=None):
        """Import a theme from an archive"""
        archive_path = Path(archive_path)
        if not archive_path.exists():
            self.log(f"Archive not found: {archive_path}")
            return None

        # Determine archive type
        suffixes = ''.join(archive_path.suffixes)
        archive_type = None
        for ext, atype in ARCHIVE_EXTENSIONS.items():
            if suffixes.endswith(ext):
                archive_type = atype
                break

        if not archive_type:
            self.log(f"Unsupported archive type: {suffixes}")
            return None

        # Create theme directory
        if not theme_name:
            theme_name = archive_path.stem
            # Clean up name
            for ext in ['.tar', '.gz', '.xz', '.bz2', '.zip', '.tgz', '.txz', '.tbz2']:
                theme_name = theme_name.replace(ext, '')

        theme_dir = CONKY_DIR / theme_name
        theme_dir.mkdir(parents=True, exist_ok=True)

        try:
            if archive_type == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(theme_dir)
            elif archive_type.startswith('tar'):
                with tarfile.open(archive_path) as tf:
                    tf.extractall(theme_dir)
            elif archive_type == '7z':
                # Try to use 7z command
                subprocess.run(['7z', 'x', str(archive_path), f'-o{theme_dir}', '-y'],
                             capture_output=True)
            else:
                self.log(f"Unsupported archive type: {archive_type}")
                return None

            # Find the actual theme directory (might be nested)
            actual_theme_dir = self.find_theme_in_dir(theme_dir)
            if actual_theme_dir != theme_dir:
                # Move contents up
                for item in actual_theme_dir.iterdir():
                    shutil.move(str(item), str(theme_dir / item.name))
                actual_theme_dir.rmdir()

            self.log(f"Imported theme from {archive_path.name}")
            self.scan_themes()
            return theme_dir

        except Exception as e:
            self.log(f"Error importing archive: {e}")
            if theme_dir.exists():
                shutil.rmtree(theme_dir)
            return None

    def find_theme_in_dir(self, dir_path):
        """Find the actual theme directory inside an extracted archive"""
        # Check if this directory contains conky config
        for name in ['.conkyrc', 'conkyrc', '.conf', 'config.conf', 'conky.conf']:
            if (dir_path / name).exists():
                return dir_path

        # Check subdirectories
        for item in dir_path.iterdir():
            if item.is_dir():
                for name in ['.conkyrc', 'conkyrc', '.conf', 'config.conf', 'conky.conf']:
                    if (item / name).exists():
                        return item

        return dir_path

    def import_folder(self, folder_path, theme_name=None):
        """Import a theme from a folder"""
        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            self.log(f"Folder not found: {folder_path}")
            return None

        if not theme_name:
            theme_name = folder_path.name

        theme_dir = CONKY_DIR / theme_name
        theme_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Copy folder contents
            for item in folder_path.iterdir():
                dest = theme_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest))
                else:
                    shutil.copy2(str(item), str(dest))

            self.log(f"Imported theme from folder: {folder_path.name}")
            self.scan_themes()
            return theme_dir

        except Exception as e:
            self.log(f"Error importing folder: {e}")
            if theme_dir.exists():
                shutil.rmtree(theme_dir)
            return None

    def delete_theme(self, theme):
        """Delete a theme"""
        theme_path = Path(theme['path'])
        try:
            if theme_path.exists():
                shutil.rmtree(str(theme_path))
                self.log(f"Deleted theme: {theme['name']}")
                self.scan_themes()
                return True
        except Exception as e:
            self.log(f"Error deleting theme: {e}")
        return False

    def set_autostart(self, theme, enabled=True):
        """Set or remove autostart for a theme"""
        autostart_file = AUTOSTART_DIR / f"conky-{theme['name']}.desktop"

        if enabled:
            monitor = self.get_monitor_index()
            content = f"""[Desktop Entry]
Type=Application
Name=Conky {theme['name']}
Exec=/usr/bin/conky -c {theme['config']} -m {monitor}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            try:
                with open(autostart_file, 'w') as f:
                    f.write(content)
                self.log(f"Autostart enabled for: {theme['name']} on monitor {monitor}")
                return True
            except Exception as e:
                self.log(f"Error setting autostart: {e}")
                return False
        else:
            if autostart_file.exists():
                autostart_file.unlink()
                self.log(f"Autostart removed for: {theme['name']}")
                return True
            return True

    def get_autostart_themes(self):
        """Get all themes with autostart enabled"""
        autostart_themes = []
        if AUTOSTART_DIR.exists():
            for f in AUTOSTART_DIR.glob("conky-*.desktop"):
                try:
                    with open(f, 'r') as file:
                        content = file.read()
                        for line in content.split('\n'):
                            if line.startswith('Exec='):
                                config_path = line.split('-c ')[-1].strip().split(' -m ')[0]
                                for theme in self.themes:
                                    if theme['config'] == config_path:
                                        autostart_themes.append(theme)
                                break
                except Exception:
                    pass
        return autostart_themes

    def is_autostart(self, theme):
        """Check if a theme has autostart enabled"""
        autostart_themes = self.get_autostart_themes()
        return any(t['name'] == theme['name'] for t in autostart_themes)

    def open_theme_folder(self, theme):
        """Open theme folder in file manager"""
        try:
            subprocess.Popen(['xdg-open', theme['path']])
        except Exception as e:
            self.log(f"Error opening folder: {e}")

    def edit_theme(self, theme):
        """Open theme config in editor"""
        try:
            editor = os.environ.get('EDITOR', 'xdg-open')
            subprocess.Popen([editor, theme['config']])
        except Exception as e:
            self.log(f"Error opening editor: {e}")


class ConkyManagerGUI:
    """GUI for Conky Manager"""

    def __init__(self, root):
        self.root = root
        self.root.title(f"Conky Manager v{VERSION}")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        # Set window icon
        self.set_window_icon()

        self.manager = ConkyManager()
        self.selected_theme = None
        self.has_update = False

        self.setup_ui()
        self.refresh_theme_list()
        self.auto_refresh()
        self.check_for_updates()

    def set_window_icon(self):
        """Set the window icon"""
        icon_paths = [
            Path.home() / ".local/share/conky-manager/icon.png",
            Path(__file__).parent / "icon.png",
        ]
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
                    return
                except Exception:
                    pass

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text=f"Conky Manager v{VERSION}", font=('Helvetica', 16, 'bold')).pack(side=tk.LEFT)

        # Status indicator
        self.status_var = tk.StringVar(value="Stopped")
        self.status_label = ttk.Label(header_frame, textvariable=self.status_var, foreground='red')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        self.update_status()

        # Toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar_frame, text="Refresh", command=self.refresh_theme_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Import Archive", command=self.import_archive).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Import Folder", command=self.import_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Layout", command=self.open_layout_editor).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Open ~/.conky", command=self.open_conky_dir).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Monitor selector
        ttk.Label(toolbar_frame, text="Monitor:").pack(side=tk.LEFT, padx=(5, 2))
        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(
            toolbar_frame, textvariable=self.monitor_var,
            values=[], width=20, state="readonly"
        )
        self.monitor_combo.pack(side=tk.LEFT, padx=2)
        self.monitor_combo.bind("<<ComboboxSelected>>", self._on_monitor_change)
        self._populate_monitors()

        self.update_btn = ttk.Button(toolbar_frame, text="Update", command=self.update_from_repo)
        self.update_btn.pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar_frame, text="Restart Manager", command=self.restart_manager).pack(side=tk.RIGHT, padx=2)

        # Theme list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview
        columns = ('name', 'type', 'lua', 'autostart', 'status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='extended')

        self.tree.heading('name', text='Theme Name')
        self.tree.heading('type', text='Type')
        self.tree.heading('lua', text='Lua')
        self.tree.heading('autostart', text='Autostart')
        self.tree.heading('status', text='Status')

        self.tree.column('name', width=250)
        self.tree.column('type', width=100)
        self.tree.column('lua', width=80)
        self.tree.column('status', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_theme_select)
        self.tree.bind('<Double-1>', self.on_theme_double_click)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        self.run_btn = ttk.Button(button_frame, text="Run Theme", command=self.run_theme, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=2)

        self.stop_theme_btn = ttk.Button(button_frame, text="Stop Theme", command=self.stop_theme, state=tk.DISABLED)
        self.stop_theme_btn.pack(side=tk.LEFT, padx=2)

        self.restart_theme_btn = ttk.Button(button_frame, text="Restart Theme", command=self.restart_theme, state=tk.DISABLED)
        self.restart_theme_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(button_frame, text="Stop All", command=self.stop_conky)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.restart_btn = ttk.Button(button_frame, text="Restart", command=self.restart_all)
        self.restart_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.edit_btn = ttk.Button(button_frame, text="Edit", command=self.edit_theme, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=2)

        self.folder_btn = ttk.Button(button_frame, text="Open Folder", command=self.open_theme_folder, state=tk.DISABLED)
        self.folder_btn.pack(side=tk.LEFT, padx=2)

        self.delete_btn = ttk.Button(button_frame, text="Delete", command=self.delete_theme, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.autostart_var = tk.BooleanVar(value=False)
        self.autostart_check = ttk.Checkbutton(button_frame, text="Autostart", variable=self.autostart_var,
                                               command=self.toggle_autostart, state=tk.DISABLED)
        self.autostart_check.pack(side=tk.LEFT, padx=2)

        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Theme Info", padding="5")
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.info_text = scrolledtext.ScrolledText(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)

    def auto_refresh(self):
        """Auto-refresh theme list every 3 seconds"""
        self.refresh_theme_list()
        self.root.after(3000, self.auto_refresh)

    def refresh_theme_list(self):
        """Refresh the theme list"""
        # Save current selection (all selected items)
        selected_names = []
        for item in self.tree.selection():
            values = self.tree.item(item)['values']
            selected_names.append(values[0])

        self.tree.delete(*self.tree.get_children())
        self.manager.scan_themes()

        for theme in self.manager.themes:
            is_running = self.manager.is_theme_running(theme)
            status = "Running" if is_running else ""
            lua = "Yes" if theme['has_lua'] else "No"
            is_autostart = "Yes" if self.manager.is_autostart(theme) else "No"
            self.tree.insert('', tk.END, values=(theme['name'], theme['type'], lua, is_autostart, status),
                           tags=('running' if is_running else '',))

        self.tree.tag_configure('running', foreground='green')

        # Restore all selections
        new_selection = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values[0] in selected_names:
                new_selection.append(item)
        if new_selection:
            self.tree.selection_set(new_selection)
            self.tree.see(new_selection[0])
            # Update buttons based on last selected
            name = self.tree.item(new_selection[-1])['values'][0]
            self.selected_theme = next((t for t in self.manager.themes if t['name'] == name), None)
            if self.selected_theme:
                self.run_btn.config(state=tk.NORMAL)
                self.edit_btn.config(state=tk.NORMAL)
                self.folder_btn.config(state=tk.NORMAL)
                self.delete_btn.config(state=tk.NORMAL)
                self.autostart_check.config(state=tk.NORMAL)
                is_running = self.manager.is_theme_running(self.selected_theme)
                self.stop_theme_btn.config(state=tk.NORMAL if is_running else tk.DISABLED)
                self.restart_theme_btn.config(state=tk.NORMAL if is_running else tk.DISABLED)
                self.autostart_var.set(self.manager.is_autostart(self.selected_theme))

    def on_theme_select(self, event):
        """Handle theme selection"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            theme_name = item['values'][0]
            self.selected_theme = next((t for t in self.manager.themes if t['name'] == theme_name), None)

            if self.selected_theme:
                self.run_btn.config(state=tk.NORMAL)
                self.edit_btn.config(state=tk.NORMAL)
                self.folder_btn.config(state=tk.NORMAL)
                self.delete_btn.config(state=tk.NORMAL)
                self.autostart_check.config(state=tk.NORMAL)

                # Enable/disable stop theme button based on running status
                is_running = self.manager.is_theme_running(self.selected_theme)
                self.stop_theme_btn.config(state=tk.NORMAL if is_running else tk.DISABLED)
                self.restart_theme_btn.config(state=tk.NORMAL if is_running else tk.DISABLED)

                # Check if autostart
                self.autostart_var.set(self.manager.is_autostart(self.selected_theme))

                # Show info
                self.show_theme_info(self.selected_theme)

    def on_theme_double_click(self, event):
        """Handle double click - run theme"""
        self.run_theme()

    def show_theme_info(self, theme):
        """Show theme information"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)

        info = f"Name: {theme['name']}\n"
        info += f"Path: {theme['path']}\n"
        info += f"Config: {theme['config']}\n"
        info += f"Has Lua: {'Yes' if theme['has_lua'] else 'No'}\n"
        info += f"Has Images: {'Yes' if theme['has_images'] else 'No'}"

        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)

    def get_selected_themes(self):
        """Get all selected themes"""
        themes = []
        for item in self.tree.selection():
            values = self.tree.item(item)['values']
            name = values[0]
            theme = next((t for t in self.manager.themes if t['name'] == name), None)
            if theme:
                themes.append(theme)
        return themes

    def run_theme(self):
        """Run all selected themes"""
        for theme in self.get_selected_themes():
            self.manager.start_conky(theme)
        self.update_status()
        self.refresh_theme_list()

    def stop_theme(self):
        """Stop all selected themes"""
        for theme in self.get_selected_themes():
            self.manager.stop_theme(theme)
        self.update_status()
        self.refresh_theme_list()
        self.stop_theme_btn.config(state=tk.DISABLED)

    def stop_conky(self):
        """Stop all conky instances"""
        self.manager.stop_conky()
        self.update_status()
        self.refresh_theme_list()
        self.stop_theme_btn.config(state=tk.DISABLED)

    def restart_theme(self):
        """Restart all selected themes"""
        for theme in self.get_selected_themes():
            self.manager.stop_theme(theme)
            self.manager.start_conky(theme)
        self.update_status()
        self.refresh_theme_list()

    def restart_all(self):
        """Restart all currently running themes"""
        running = list(self.manager.settings.get('running_themes', []))
        self.manager.stop_conky()
        for theme_name in running:
            theme = self.manager.find_theme_by_name(theme_name)
            if theme:
                self.manager.start_conky(theme)
        self.update_status()
        self.refresh_theme_list()

    def edit_theme(self):
        """Edit the selected theme"""
        if self.selected_theme:
            self.manager.edit_theme(self.selected_theme)

    def open_theme_folder(self):
        """Open the selected theme folder"""
        if self.selected_theme:
            self.manager.open_theme_folder(self.selected_theme)

    def delete_theme(self):
        """Delete all selected themes"""
        themes = self.get_selected_themes()
        if not themes:
            return
        names = [t['name'] for t in themes]
        if messagebox.askyesno("Confirm Delete",
                              f"Delete {len(themes)} theme(s)?\n\n{', '.join(names)}"):
            for theme in themes:
                self.manager.delete_theme(theme)
            self.selected_theme = None
            self.run_btn.config(state=tk.DISABLED)
            self.edit_btn.config(state=tk.DISABLED)
            self.folder_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.autostart_check.config(state=tk.DISABLED)
            self.refresh_theme_list()

    def toggle_autostart(self):
        """Toggle autostart for all selected themes"""
        enabled = self.autostart_var.get()
        for theme in self.get_selected_themes():
            self.manager.set_autostart(theme, enabled)
        self.refresh_theme_list()

    def _populate_monitors(self):
        """Detect monitors and populate the dropdown."""
        self.monitors = []
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
                    w_str, h_str = geom.split('/')[0].split('x')
                    h_str = h_str.split('/')[0]
                    w, h = int(w_str), int(h_str)
                    label = f"{name} ({w}x{h})"
                    self.monitors.append({"index": idx, "label": label})
        except Exception:
            pass
        if not self.monitors:
            self.monitors = [{"index": 0, "label": "default (1920x1080)"}]

        labels = [m["label"] for m in self.monitors]
        self.monitor_combo["values"] = labels

        # Select current monitor from layout.json
        current = self.manager.get_monitor_index()
        for i, m in enumerate(self.monitors):
            if m["index"] == current:
                self.monitor_combo.current(i)
                return
        self.monitor_combo.current(0)

    def _on_monitor_change(self, event=None):
        """Handle monitor selection change."""
        idx = self.monitor_combo.current()
        if 0 <= idx < len(self.monitors):
            monitor = self.monitors[idx]["index"]
            # Save to layout.json
            layout_file = Path.home() / ".config" / "conky" / "layout.json"
            try:
                data = {}
                if layout_file.exists():
                    with open(layout_file) as f:
                        data = json.load(f)
                data["monitor"] = monitor
                with open(layout_file, 'w') as f:
                    json.dump(data, f, indent=2)
                self.log(f"Monitor set to {self.monitors[idx]['label']}")
            except Exception as e:
                self.log(f"Error saving monitor: {e}")

    def open_layout_editor(self):
        """Open the layout editor"""
        layout_editor.LayoutEditor(self.root)

    def check_for_updates(self):
        """Check for updates on startup (non-blocking)"""
        def _check():
            repo_path = self.get_repo_path()
            if not repo_path:
                return
            try:
                # Compare VERSION file from repo
                version_file = repo_path / "VERSION"
                if not version_file.exists():
                    return

                result = subprocess.run(['git', '-C', str(repo_path), 'fetch', 'origin'],
                                        capture_output=True, timeout=15)
                if result.returncode != 0:
                    return

                # Get remote VERSION
                result = subprocess.run(
                    ['git', '-C', str(repo_path), 'show', f'origin/master:VERSION'],
                    capture_output=True, text=True, timeout=10
                )
                remote_version = result.stdout.strip() if result.returncode == 0 else ""

                if remote_version and remote_version != VERSION:
                    self.has_update = True
                    self.root.after(0, self.blink_update_btn)
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    def blink_update_btn(self):
        """Show update available on button"""
        if not self.has_update:
            return
        self.update_btn.config(text="Update (NEW)")

    def restart_manager(self):
        """Restart the manager"""
        python = sys.executable
        self.root.destroy()
        os.execv(python, [python] + sys.argv)

    def get_repo_path(self):
        """Find the git repo path"""
        candidates = [
            Path("/opt/conky-manager"),
            Path(__file__).parent,
            Path.home() / "repos" / "conky",
        ]
        for p in candidates:
            result = subprocess.run(['git', '-C', str(p), 'rev-parse', '--git-dir'],
                                    capture_output=True, timeout=5)
            if result.returncode == 0:
                return p
        return None

    def update_from_repo(self):
        """Pull latest changes from git repo (does NOT apply to system)"""
        repo_path = self.get_repo_path()
        if not repo_path:
            messagebox.showerror("Update Error", "Git repo not found")
            return
        try:
            subprocess.run(['git', '-C', str(repo_path), 'fetch', 'origin'],
                           capture_output=True, timeout=30)

            # Compare VERSION file
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'show', f'origin/master:VERSION'],
                capture_output=True, text=True, timeout=10
            )
            remote_version = result.stdout.strip() if result.returncode == 0 else ""

            if not remote_version or remote_version == VERSION:
                messagebox.showinfo("Update", "Already up to date!")
                return

            # Get new commits between versions
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '--oneline', f'HEAD..origin/master'],
                capture_output=True, text=True, timeout=10
            )
            commits = result.stdout.strip()

            # Get file changes
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'diff', '--stat', 'HEAD', 'origin/master'],
                capture_output=True, text=True, timeout=10
            )
            changes = result.stdout.strip()

            # Get commit messages with details
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '--format=%h %s', f'HEAD..origin/master'],
                capture_output=True, text=True, timeout=10
            )
            details = result.stdout.strip()

            msg = f"Update: {VERSION} -> {remote_version}\n\n"
            if details:
                msg += f"Changes:\n{details}\n\n"
            else:
                msg += "No new commits found.\n\n"
            if changes:
                msg += f"Files:\n{changes}\n\n"
            msg += "Apply update?"

            if messagebox.askyesno("Update Available", msg):
                result = subprocess.run(['git', '-C', str(repo_path), 'pull', 'origin', 'master'],
                                        capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    import shutil
                    installed_dir = Path.home() / ".local" / "share" / "conky-manager"
                    conky_config = Path.home() / ".config" / "conky"
                    backup_dir = HOME / ".local" / "share" / "conky-manager" / "backups" / remote_version
                    backup_dir.mkdir(parents=True, exist_ok=True)

                    # Backup current manager files
                    for f in ["conky_manager.py", "layout_editor.py"]:
                        src = installed_dir / f
                        if src.exists():
                            shutil.copy2(str(src), str(backup_dir / f))

                    # Backup current themes
                    themes_backup = backup_dir / "themes"
                    themes_backup.mkdir(exist_ok=True)
                    for theme_dir in conky_config.iterdir():
                        if theme_dir.is_dir() and theme_dir.name.endswith("-conky-manager"):
                            shutil.copytree(str(theme_dir), str(themes_backup / theme_dir.name))

                    # Copy manager files to installed location
                    for f in ["conky_manager.py", "layout_editor.py"]:
                        src = repo_path / f
                        dst = installed_dir / f
                        if src.exists():
                            shutil.copy2(str(src), str(dst))

                    # Copy themes to system
                    themes_dir = repo_path / "themes"
                    if themes_dir.exists():
                        for theme_dir in themes_dir.iterdir():
                            if theme_dir.is_dir() and theme_dir.name.endswith("-conky-manager"):
                                dst = conky_config / theme_dir.name
                                if dst.exists():
                                    shutil.rmtree(str(dst))
                                shutil.copytree(str(theme_dir), str(dst))

                    self.has_update = False
                    self.update_btn.config(text="Update")
                    messagebox.showinfo("Update", f"Updated to v{remote_version}!\n\nBackup saved to: {backup_dir}\n\nRun 'Restart Manager' to reload.")
                else:
                    messagebox.showerror("Update Error", f"Pull failed:\n{result.stderr}")

        except subprocess.TimeoutExpired:
            messagebox.showerror("Update Error", "Git operation timed out")
        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    def import_archive(self):
        """Import a theme from an archive"""
        filetypes = [
            ("Archives", "*.zip *.tar *.tar.gz *.tgz *.tar.xz *.txz *.tar.bz2 *.tbz2 *.7z"),
            ("ZIP", "*.zip"),
            ("TAR", "*.tar *.tar.gz *.tgz *.tar.xz *.txz *.tar.bz2 *.tbz2"),
            ("7z", "*.7z"),
            ("All files", "*.*"),
        ]
        filepath = filedialog.askopenfilename(
            title="Select Archive",
            filetypes=filetypes
        )
        if filepath:
            theme_name = filedialog.askstring("Theme Name", "Enter theme name (or leave empty):")
            result = self.manager.import_archive(filepath, theme_name or None)
            if result:
                self.refresh_theme_list()
                messagebox.showinfo("Success", "Theme imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import theme!")

    def import_folder(self):
        """Import a theme from a folder"""
        folder = filedialog.askdirectory(title="Select Theme Folder")
        if folder:
            theme_name = filedialog.askstring("Theme Name", "Enter theme name (or leave empty):")
            result = self.manager.import_folder(folder, theme_name or None)
            if result:
                self.refresh_theme_list()
                messagebox.showinfo("Success", "Theme imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import theme!")

    def open_conky_dir(self):
        """Open the conky directory"""
        self.manager.open_theme_folder({'path': str(CONKY_DIR)})

    def update_status(self):
        """Update the status indicator"""
        if self.manager.is_conky_running():
            self.status_var.set("Running")
            self.status_label.config(foreground='green')
        else:
            self.status_var.set("Stopped")
            self.status_label.config(foreground='red')


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConkyManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
