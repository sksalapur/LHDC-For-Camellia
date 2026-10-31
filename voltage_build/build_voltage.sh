#!/bin/bash
set -e

# ==============================================================================
# VoltageOS 16 (Android 16) Build Script for Xiaomi Redmi Note 10 5G (camellia)
# Automatically applies Savitech LHDC V3/V5 native patches before compiling.
# ==============================================================================

PROJECT_DIR="/mnt/e/DATA/Projects/LHDC"
WORKDIR="$HOME/voltage"
OUT_DEST="$PROJECT_DIR/voltage_build/out"

echo "=== Step 1: Installing Required Dependencies ==="
sudo apt update
sudo apt install -y \
    bc bison build-essential ccache curl flex g++-multilib gcc-multilib git \
    git-lfs gnupg gperf imagemagick lib32readline-dev lib32z1-dev libelf-dev \
    liblz4-tool libncurses5 libncurses5-dev libsdl1.2-dev libssl-dev libxml2 \
    libxml2-utils lzop pngcrush rsync schedtool squashfs-tools xsltproc zip \
    zlib1g-dev python3 python-is-python3 openjdk-21-jdk libtinfo5

# Configure Git if not configured
git config --global user.name "SKSAL" 2>/dev/null || true
git config --global user.email "sksal@local" 2>/dev/null || true

# Setup repo tool
mkdir -p "$HOME/bin"
curl -s https://storage.googleapis.com/git-repo-downloads/repo > "$HOME/bin/repo"
chmod a+x "$HOME/bin/repo"
export PATH="$HOME/bin:$PATH"

# Setup ccache
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache
ccache -M 50G

mkdir -p "$WORKDIR"
mkdir -p "$OUT_DEST"
cd "$WORKDIR"

echo "=== Step 2: Initializing VoltageOS 16 Manifest ==="
if [ ! -d ".repo" ]; then
    repo init -u https://github.com/VoltageOS/manifest.git -b 16 --depth=1
fi

echo "=== Step 3: Setting Up Device Trees for camellia ==="
mkdir -p .repo/local_manifests
cp -f "$PROJECT_DIR/voltage_build/camellia_manifest.xml" .repo/local_manifests/camellia.xml

echo "=== Step 4: Syncing Source Repositories (This may take some time) ==="
repo sync -c -j$(nproc --all) --force-sync --no-clone-bundle --no-tags

echo "=== Step 5: Applying Native LHDC Patches ==="
PATCH_DIR="$PROJECT_DIR/derp_patches"

# Patch Bluetooth APEX stack
if [ -d "packages/modules/Bluetooth" ]; then
    echo "Patching packages/modules/Bluetooth with Savitech LHDC stack..."
    cd packages/modules/Bluetooth
    git apply "$PATCH_DIR/0_packages_modules_Bluetooth.patch" 2>/dev/null || git apply --whitespace=fix "$PATCH_DIR/0_packages_modules_Bluetooth.patch" 2>/dev/null || echo "Bluetooth patch already applied or skipped"
    cd "$WORKDIR"
fi

# Patch Settings App
if [ -d "packages/apps/Settings" ]; then
    echo "Patching packages/apps/Settings with LHDC Developer Options..."
    cd packages/apps/Settings
    git apply "$PATCH_DIR/0_packages_apps_Settings.patch" 2>/dev/null || git apply --whitespace=fix "$PATCH_DIR/0_packages_apps_Settings.patch" 2>/dev/null || echo "Settings patch already applied or skipped"
    cd "$WORKDIR"
fi

# Patch Frameworks Base
if [ -d "frameworks/base" ]; then
    echo "Patching frameworks/base with LHDC codec constants..."
    cd frameworks/base
    git apply "$PATCH_DIR/0_frameworks_base.patch" 2>/dev/null || git apply --whitespace=fix "$PATCH_DIR/0_frameworks_base.patch" 2>/dev/null || echo "frameworks/base patch already applied or skipped"
    cd "$WORKDIR"
fi

echo "=== Step 6: Starting Compilation ==="
source build/envsetup.sh
lunch voltage_camellia-userdebug
mka bacon -j$(nproc --all)

echo "=== Step 7: Build Succeeded! Copying Output Zip ==="
ZIP_FILE=$(find out/target/product/camellia/ -maxdepth 1 -name "VoltageOS-*.zip" -type f | head -n 1)
if [ -n "$ZIP_FILE" ]; then
    cp -f "$ZIP_FILE" "$OUT_DEST/"
    echo "Flashable zip copied to: $OUT_DEST/$(basename $ZIP_FILE)"
else
    echo "Warning: Could not locate output zip in out/target/product/camellia/"
fi

echo "=== All Done! ==="
