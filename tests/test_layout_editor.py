"""Tests for layout_editor.py functions."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys_path = str(Path(__file__).parent.parent)
import sys
sys.path.insert(0, sys_path)

import layout_editor
from layout_editor import (
    load_layout, save_layout, save_positions, detect_monitors,
    WidgetRect, LayoutEditor,
    LAYOUT_FILE, POSITIONS_FILE, DEFAULT_SCREEN_W, DEFAULT_SCREEN_H,
    RESOLUTION_PRESETS, MIN_SCREEN_W, MIN_SCREEN_H,
    MAX_SCREEN_W, MAX_SCREEN_H
)


@pytest.fixture
def sample_layout_file(tmp_path):
    layout_file = tmp_path / "layout.json"
    layout_file.write_text(json.dumps({
        "resolution": {"w": 1920, "h": 1080},
        "monitor": 0,
        "test-conky-manager": {"x": 100, "y": 200, "w": 300, "h": 400},
    }, indent=2))
    return layout_file


class TestDetectMonitors:
    def test_returns_list(self):
        monitors = detect_monitors()
        assert isinstance(monitors, list)
        assert len(monitors) > 0

    def test_has_required_keys(self):
        monitors = detect_monitors()
        for m in monitors:
            assert "index" in m
            assert "name" in m
            assert "w" in m
            assert "h" in m

    def test_with_mock_xrandr(self):
        with patch("layout_editor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Monitors: 2\n 0: +*eDP-1 1920/300x1200/190+0+768  eDP-1\n 1: +DP-2 1366/361x768/203+226+0  DP-2\n",
                returncode=0
            )
            monitors = detect_monitors()
            assert len(monitors) == 2
            assert monitors[0]["name"] == "eDP-1"
            assert monitors[0]["w"] == 1920
            assert monitors[0]["h"] == 1200
            assert monitors[1]["name"] == "DP-2"
            assert monitors[1]["w"] == 1366
            assert monitors[1]["h"] == 768

    def test_fallback_on_error(self):
        with patch("layout_editor.subprocess.run", side_effect=Exception("fail")):
            monitors = detect_monitors()
            assert len(monitors) == 1
            assert monitors[0]["w"] == DEFAULT_SCREEN_W


class TestLoadLayout:
    def test_load_layout_valid_json(self, sample_layout_file, monkeypatch):
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", sample_layout_file)
        result = load_layout()
        assert "test-conky-manager" in result
        assert result["test-conky-manager"]["x"] == 100

    def test_load_layout_has_resolution(self, sample_layout_file, monkeypatch):
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", sample_layout_file)
        result = load_layout()
        assert result["resolution"]["w"] == 1920

    def test_load_layout_has_monitor(self, sample_layout_file, monkeypatch):
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", sample_layout_file)
        result = load_layout()
        assert result["monitor"] == 0

    def test_load_layout_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", tmp_path / "nonexistent.json")
        result = load_layout()
        assert result == {}


class TestSaveLayout:
    def test_save_layout_creates_file(self, tmp_path, monkeypatch):
        layout_file = tmp_path / "layout.json"
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", layout_file)
        save_layout({"test": {"x": 0, "y": 0, "w": 100, "h": 100}})
        assert layout_file.exists()

    def test_save_layout_atomic(self, tmp_path, monkeypatch):
        layout_file = tmp_path / "layout.json"
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", layout_file)
        save_layout({"test": {"x": 0, "y": 0, "w": 100, "h": 100}})
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_save_layout_roundtrip(self, tmp_path, monkeypatch):
        layout_file = tmp_path / "layout.json"
        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", layout_file)
        data = {"resolution": {"w": 2560, "h": 1440}, "monitor": 1,
                "theme-a": {"x": 10, "y": 20, "w": 300, "h": 400}}
        save_layout(data)
        loaded = load_layout()
        assert loaded == data


class TestSavePositions:
    def test_save_positions_creates_file(self, tmp_path, monkeypatch):
        pos_file = tmp_path / "positions.lua"
        monkeypatch.setattr(layout_editor, "POSITIONS_FILE", pos_file)
        widget = MagicMock(x=30, y=720)
        save_positions(1920, 1080, 0, {"crypto-conky-manager": widget})
        assert pos_file.exists()

    def test_save_positions_includes_monitor(self, tmp_path, monkeypatch):
        pos_file = tmp_path / "positions.lua"
        monkeypatch.setattr(layout_editor, "POSITIONS_FILE", pos_file)
        save_positions(2560, 1440, 1, {})
        content = pos_file.read_text()
        assert 'screen = {w = 2560, h = 1440, monitor = 1}' in content

    def test_save_positions_content(self, tmp_path, monkeypatch):
        pos_file = tmp_path / "positions.lua"
        monkeypatch.setattr(layout_editor, "POSITIONS_FILE", pos_file)
        widget = MagicMock(x=30, y=720)
        save_positions(1920, 1080, 0, {"crypto-conky-manager": widget})
        content = pos_file.read_text()
        assert '["crypto-conky-manager"] = {x = 30, y = 720}' in content


class TestWidgetRect:
    def test_to_dict(self):
        mock_canvas = MagicMock()
        mock_canvas.create_rectangle.return_value = 1
        mock_canvas.create_text.return_value = 2
        rect = WidgetRect(mock_canvas, "test", 100, 200, 300, 400, "#ff0000")
        d = rect.to_dict()
        assert d["x"] == 100
        assert d["y"] == 200

    def test_move_custom_resolution(self):
        mock_canvas = MagicMock()
        mock_canvas.create_rectangle.return_value = 1
        mock_canvas.create_text.return_value = 2
        rect = WidgetRect(mock_canvas, "test", 0, 0, 100, 100,
                          screen_w=2560, screen_h=1440)
        rect.move(99999, 99999)
        assert rect.x <= 2560 - rect.w
        assert rect.y <= 1440 - rect.h


class TestUpdateConkyrcPosition:
    def test_update_minimum_width_height(self, tmp_path):
        conkyrc = tmp_path / "conkyrc"
        conkyrc.write_text("minimum_width = 1920, minimum_height = 1080,\ngap_x = 0,\n    gap_y = 0,")
        editor = LayoutEditor.__new__(LayoutEditor)
        editor.screen_w = 2560
        editor.screen_h = 1440
        widget = MagicMock()
        editor.update_conkyrc_position(conkyrc, widget)
        content = conkyrc.read_text()
        assert "minimum_width = 2560" in content
        assert "minimum_height = 1440" in content

    def test_gap_always_zero(self, tmp_path):
        conkyrc = tmp_path / "conkyrc"
        conkyrc.write_text("gap_x = 500,\n    gap_y = 300,")
        editor = LayoutEditor.__new__(LayoutEditor)
        editor.screen_w = 1920
        editor.screen_h = 1080
        widget = MagicMock()
        editor.update_conkyrc_position(conkyrc, widget)
        content = conkyrc.read_text()
        assert "gap_x = 0" in content
        assert "gap_y = 0" in content

    def test_no_change_no_write(self, tmp_path):
        conkyrc = tmp_path / "conkyrc"
        conkyrc.write_text("minimum_width = 2560, minimum_height = 1440,\ngap_x = 0,\n    gap_y = 0,")
        original_mtime = conkyrc.stat().st_mtime_ns
        editor = LayoutEditor.__new__(LayoutEditor)
        editor.screen_w = 2560
        editor.screen_h = 1440
        widget = MagicMock()
        editor.update_conkyrc_position(conkyrc, widget)
        assert conkyrc.stat().st_mtime_ns == original_mtime


class TestResolutionFeature:
    def test_resolution_presets_exist(self):
        assert "1920x1080" in RESOLUTION_PRESETS
        assert "2560x1440" in RESOLUTION_PRESETS
        assert "Custom" in RESOLUTION_PRESETS

    def test_resolution_bounds(self):
        assert MIN_SCREEN_W == 800
        assert MIN_SCREEN_H == 600

    def test_widget_respects_custom_resolution(self):
        mock_canvas = MagicMock()
        mock_canvas.create_rectangle.return_value = 1
        mock_canvas.create_text.return_value = 2
        rect = WidgetRect(mock_canvas, "test", 2500, 1400, 100, 50,
                          screen_w=2560, screen_h=1440)
        rect.move(1000, 0)
        assert rect.x == 2460

    def test_current_preset_detection(self):
        editor = LayoutEditor.__new__(LayoutEditor)
        editor.screen_w = 1920
        editor.screen_h = 1080
        assert editor._current_preset() == "1920x1080"

        editor.screen_w = 2560
        editor.screen_h = 1440
        assert editor._current_preset() == "2560x1440"

        editor.screen_w = 1366
        editor.screen_h = 768
        assert editor._current_preset() == "Custom"


class TestApplyPositions:
    def test_apply_positions_writes_positions_lua(self, tmp_path, monkeypatch):
        conky_dir = tmp_path / ".config" / "conky"
        theme_dir = conky_dir / "test-conky-manager"
        theme_dir.mkdir(parents=True)
        conkyrc = theme_dir / "conkyrc"
        conkyrc.write_text("minimum_width = 1920, minimum_height = 1080,\ngap_x = 0,\n    gap_y = 0,")

        monkeypatch.setattr(layout_editor, "LAYOUT_FILE", tmp_path / "layout.json")
        monkeypatch.setattr(layout_editor, "POSITIONS_FILE", tmp_path / "positions.lua")

        editor = LayoutEditor.__new__(LayoutEditor)
        editor.screen_w = 2560
        editor.screen_h = 1440
        editor.monitor = 1
        mock_canvas = MagicMock()
        mock_canvas.create_rectangle.return_value = 1
        mock_canvas.create_text.return_value = 2
        editor.widgets = {
            "test-conky-manager": WidgetRect(mock_canvas, "test-conky-manager", 100, 200, 300, 400)
        }

        with patch.object(editor, 'restart_themes'):
            with patch.object(layout_editor.Path, 'home', return_value=tmp_path):
                editor.apply_positions()

        pos_file = tmp_path / "positions.lua"
        assert pos_file.exists()
        content = pos_file.read_text()
        assert 'screen = {w = 2560, h = 1440, monitor = 1}' in content
        assert '["test-conky-manager"] = {x = 100, y = 200}' in content
        assert "minimum_width = 2560" in conkyrc.read_text()


class TestMonitorIndex:
    def test_restart_uses_monitor(self, tmp_path):
        editor = LayoutEditor.__new__(LayoutEditor)
        editor.monitor = 1
        conky_config = tmp_path / ".config" / "conky"
        theme_dir = conky_config / "test-theme"
        theme_dir.mkdir(parents=True)
        conkyrc = theme_dir / "conkyrc"
        conkyrc.write_text("test")

        with patch("layout_editor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=1)
            with patch("layout_editor.subprocess.Popen") as mock_popen:
                mock_popen.return_value = MagicMock()
                with patch.object(layout_editor.Path, 'home', return_value=tmp_path):
                    editor.restart_themes(["test-theme"])
                call_args = mock_popen.call_args[0][0]
                assert "-m" in call_args
                assert call_args[call_args.index("-m") + 1] == "1"


class TestGetRunningThemes:
    def test_detection_from_pgrep(self):
        editor = LayoutEditor.__new__(LayoutEditor)
        with patch("layout_editor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="12345 conky -c /home/user/.config/conky/test-conky-manager/conkyrc -d\n",
                returncode=0
            )
            running = editor.get_running_themes()
            assert "test-conky-manager" in running

    def test_detection_empty(self):
        editor = LayoutEditor.__new__(LayoutEditor)
        with patch("layout_editor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=1)
            running = editor.get_running_themes()
            assert len(running) == 0
