#!/bin/bash
set -e

# ==============================================================================
# VoltageOS 16 (Android 16) Build Script for Xiaomi Redmi Note 10 5G (camellia)
# Automatically applies Savitech LHDC V3/V5 native patches before compiling.
# ==============================================================================

PROJECT_DIR="/mnt/e/DATA/Projects/LHDC"
WORKDIR="$HOME/voltage"
OUT_DEST="$PROJECT_DIR/voltage_build/out"

echo "=== Step 1: Environment Check ==="
export PATH="$HOME/bin:/usr/local/bin:$PATH"

# Setup ccache
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache
ccache -M 50G 2>/dev/null || true

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

# Inject 64-bit LHDC vendor libraries into the build
echo "Injecting native LHDC libraries into vendor/xiaomi/camellia..."
mkdir -p vendor/xiaomi/camellia/proprietary/system/lib64
cp -f "$PROJECT_DIR/module/system/lib64/"*.so vendor/xiaomi/camellia/proprietary/system/lib64/

# Setup VoltageOS product makefile for camellia with baked-in LHDC
if [ -d "device/xiaomi/camellia" ]; then
    echo "Configuring voltage_camellia.mk with native LHDC..."
    cat << 'EOF' > device/xiaomi/camellia/voltage_camellia.mk
$(call inherit-product, device/xiaomi/camellia/lineage_camellia.mk)
$(call inherit-product, vendor/voltage/config/common_full_phone.mk)

PRODUCT_NAME := voltage_camellia

# Baked-in LHDC Native Audio Support
PRODUCT_COPY_FILES += \
    vendor/xiaomi/camellia/proprietary/system/lib64/liblhdc.so:$(TARGET_COPY_OUT_SYSTEM)/lib64/liblhdc.so \
    vendor/xiaomi/camellia/proprietary/system/lib64/liblhdcv5.so:$(TARGET_COPY_OUT_SYSTEM)/lib64/liblhdcv5.so \
    vendor/xiaomi/camellia/proprietary/system/lib64/liblhdcBT_enc.so:$(TARGET_COPY_OUT_SYSTEM)/lib64/liblhdcBT_enc.so \
    vendor/xiaomi/camellia/proprietary/system/lib64/liblhdcv5BT_enc.so:$(TARGET_COPY_OUT_SYSTEM)/lib64/liblhdcv5BT_enc.so

PRODUCT_PROPERTY_OVERRIDES += \
    persist.bluetooth.lhdc_codec.enabled=true \
    vendor.bluetooth.lhdc_codec.supported=true \
    bluetooth.a2dp.source.lhdcv3_priority.config=8002 \
    bluetooth.a2dp.source.lhdcv2_priority.config=8001 \
    persist.bluetooth.a2dp_offload.disabled=true
EOF

    if ! grep -q "voltage_camellia" device/xiaomi/camellia/AndroidProducts.mk; then
        echo "Adding voltage_camellia to AndroidProducts.mk..."
        sed -i 's/lineage_camellia.mk/lineage_camellia.mk \\\n    \$(LOCAL_DIR)\/voltage_camellia.mk/' device/xiaomi/camellia/AndroidProducts.mk
        echo -e "COMMON_LUNCH_CHOICES += voltage_camellia-userdebug\n" >> device/xiaomi/camellia/AndroidProducts.mk
    fi
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
