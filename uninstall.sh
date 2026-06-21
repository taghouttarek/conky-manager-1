#!/bin/bash
# Conky Manager Uninstallation Script

set -e

INSTALL_DIR="$HOME/.local/share/conky-manager"
OPT_DIR="/opt/conky-manager"
BIN_DIR="/usr/local/bin"
LOCAL_BIN="$HOME/.local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/conky-manager.desktop"
SYS_DESKTOP="/usr/share/applications/conky-manager.desktop"
ICON_DIR="/usr/share/icons"
LOCAL_ICON="$HOME/.local/share/icons"

echo "Uninstalling Conky Manager..."

# Remove installed files
rm -rf "$INSTALL_DIR"
rm -rf "$OPT_DIR"
rm -f "$LOCAL_BIN/conky-manager"
rm -f "$BIN_DIR/conky-manager"
rm -f "$DESKTOP_FILE"
rm -f "$SYS_DESKTOP"
rm -f "$ICON_DIR/conky-manager.png"
rm -f "$LOCAL_ICON/conky-manager.png"

# Ask about themes
echo ""
if [[ -t 0 ]]; then
    read -p "Remove installed themes from ~/.config/conky? (y/N): " remove_themes
else
    remove_themes="N"
fi
if [[ "$remove_themes" =~ ^[Yy]$ ]]; then
    for theme_dir in "$HOME/.config/conky/"*-conky-manager; do
        if [ -d "$theme_dir" ]; then
            rm -rf "$theme_dir"
            echo "Removed $(basename "$theme_dir")"
        fi
    done
    echo "Themes removed."
else
    echo "Themes kept in ~/.config/conky/"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    update-desktop-database "/usr/share/applications" 2>/dev/null || true
fi

echo ""
echo "Uninstallation complete!"
