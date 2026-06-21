#!/bin/bash
# Build Conky Manager .deb package

set -e

PACKAGE_NAME="conky-manager"
VERSION="2.0.6"
ARCH="all"
BUILD_DIR="deb"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building $PACKAGE_NAME $VERSION..."

# Update version in control file
sed -i "s/Version: .*/Version: $VERSION/" "$BUILD_DIR/DEBIAN/control"

# Ensure postinst is executable
chmod +x "$BUILD_DIR/DEBIAN/postinst"

# Build the package
dpkg-deb --build "$BUILD_DIR" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo ""
echo "Package built: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Install with: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "Or: sudo apt install ./${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
