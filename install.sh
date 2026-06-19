#!/bin/bash
# Conky Manager Installation Script

set -e

INSTALL_DIR="$HOME/.local/share/conky-manager"
BIN_DIR="$HOME/.local/bin"
SCRIPT_NAME="conky-manager"
DESKTOP_FILE="$HOME/.local/share/applications/conky-manager.desktop"
ICON_DIR="$HOME/.local/share/icons"

echo "Installing Conky Manager..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$ICON_DIR"

# Copy script
cp "$(dirname "$0")/conky_manager.py" "$INSTALL_DIR/conky_manager.py"
chmod +x "$INSTALL_DIR/conky_manager.py"

# Copy themes
if [ -d "$(dirname "$0")/themes" ]; then
    mkdir -p "$HOME/.config/conky"
    cp -r "$(dirname "$0")/themes/"* "$HOME/.config/conky/"
    echo "Themes installed to ~/.config/conky/"
fi

# Copy icon
if [ -f "$(dirname "$0")/icon.svg" ]; then
    cp "$(dirname "$0")/icon.svg" "$INSTALL_DIR/icon.svg"
fi
if [ -f "$(dirname "$0")/icon.png" ]; then
    cp "$(dirname "$0")/icon.png" "$INSTALL_DIR/icon.png"
fi

# Create wrapper script in ~/.local/bin
cat > "$BIN_DIR/$SCRIPT_NAME" << 'EOF'
#!/bin/bash
exec python3 "$HOME/.local/share/conky-manager/conky_manager.py" "$@"
EOF
chmod +x "$BIN_DIR/$SCRIPT_NAME"

# Create .desktop file
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Conky Manager
Comment=Manage and configure Conky themes
Exec=$BIN_DIR/$SCRIPT_NAME
Icon=$INSTALL_DIR/icon.svg
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
echo "Installation complete!"
echo ""
echo "You can now run: $SCRIPT_NAME"
echo "Or find 'Conky Manager' in your application menu"
