#!/bin/bash
# Conky Manager Installation Script

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/conky-manager"
LOCAL_DIR="$HOME/.local/share/conky-manager"
BIN_DIR="$HOME/.local/bin"
SCRIPT_NAME="conky-manager"
DESKTOP_FILE="$HOME/.local/share/applications/conky-manager.desktop"
ICON_DIR="$HOME/.local/share/icons"

echo "=== Conky Manager Installer ==="
echo ""

# Check if running as root for /opt
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install customtkinter --break-system-packages 2>/dev/null || pip3 install customtkinter 2>/dev/null || echo "Warning: Could not install customtkinter automatically. Run: pip3 install customtkinter"

# Install to /opt (as git repo so update feature works)
echo "Installing to $INSTALL_DIR..."
$SUDO mkdir -p "$INSTALL_DIR"
# Copy all files including .git
$SUDO rsync -a --exclude='.git' "$REPO_DIR/" "$INSTALL_DIR/"
# Copy .git separately to preserve it
if [ -d "$REPO_DIR/.git" ]; then
    $SUDO cp -r "$REPO_DIR/.git" "$INSTALL_DIR/.git"
fi
$SUDO chmod +x "$INSTALL_DIR/install.sh"
$SUDO chmod +x "$INSTALL_DIR/uninstall.sh"
if [ -f "$INSTALL_DIR/conky_manager.py" ]; then
    $SUDO chmod +x "$INSTALL_DIR/conky_manager.py"
fi

# Create local data dir
mkdir -p "$LOCAL_DIR"
mkdir -p "$LOCAL_DIR/backups"

# Backup existing themes
BACKUP_DIR="$LOCAL_DIR/backups/$(date +%Y%m%d_%H%M%S)"
if ls "$HOME/.config/conky/"*-conky-manager 1>/dev/null 2>&1; then
    mkdir -p "$BACKUP_DIR"
    for theme_dir in "$HOME/.config/conky/"*-conky-manager; do
        if [ -d "$theme_dir" ]; then
            cp -r "$theme_dir" "$BACKUP_DIR/"
        fi
    done
    echo "Backup saved to $BACKUP_DIR"
fi

# Install themes to ~/.config/conky
mkdir -p "$HOME/.config/conky"
for theme_dir in "$INSTALL_DIR/themes/"*-conky-manager; do
    if [ -d "$theme_dir" ]; then
        theme_name=$(basename "$theme_dir")
        rm -rf "$HOME/.config/conky/$theme_name"
        cp -r "$theme_dir" "$HOME/.config/conky/$theme_name"
    fi
done
echo "Themes installed to ~/.config/conky/"

# Copy wrapper script
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/$SCRIPT_NAME" << 'EOF'
#!/bin/bash
LOCAL_APP="$HOME/.local/share/conky-manager/conky_manager.py"
if [ -f "$LOCAL_APP" ]; then
    exec python3 "$LOCAL_APP" "$@"
else
    exec python3 "/opt/conky-manager/conky_manager.py" "$@"
fi
EOF
chmod +x "$BIN_DIR/$SCRIPT_NAME"

# Create icon directory and copy icon
mkdir -p "$ICON_DIR"
if [ -f "$INSTALL_DIR/icon.png" ]; then
    cp "$INSTALL_DIR/icon.png" "$ICON_DIR/conky-manager.png"
fi
if [ -f "$INSTALL_DIR/icon.svg" ]; then
    cp "$INSTALL_DIR/icon.svg" "$ICON_DIR/conky-manager.svg"
fi

# Create .desktop file
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Conky Manager
Comment=Manage and configure Conky themes
Exec=$BIN_DIR/$SCRIPT_NAME
Icon=$ICON_DIR/conky-manager.png
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=conky;monitor;system;widget;
EOF

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

# Add to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
    echo "Added $BIN_DIR to PATH in .bashrc"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Installed to: $INSTALL_DIR"
echo "Run with: $SCRIPT_NAME"
echo "Or find 'Conky Manager' in your application menu"
echo ""

# Ask to delete the cloned repo (skip if non-interactive)
if [[ -t 0 ]] && [[ "$INSTALL_DIR" != "$REPO_DIR" ]]; then
    echo ""
    read -p "Delete the cloned repo ($REPO_DIR)? (y/N): " delete_repo
    if [[ "$delete_repo" =~ ^[Yy]$ ]]; then
        rm -rf "$REPO_DIR"
        echo "Repository deleted."
    fi
fi
