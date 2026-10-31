#!/system/bin/sh
MODDIR=${0%/*}

setenforce 0 2>/dev/null

# Mount patched AospBluetoothResOverlay.apk to set LHDC priority to 8002/8001
OVERLAY_TARGET="/product/overlay/AospBluetoothResOverlay.apk"
OVERLAY_PATCHED="$MODDIR/work/AospBluetoothResOverlay.apk"
if [ -f "$OVERLAY_PATCHED" ] && [ -f "$OVERLAY_TARGET" ]; then
    mount --bind "$OVERLAY_PATCHED" "$OVERLAY_TARGET"
fi

# Mount patched MiuiBluetooth.apk to allow LHDC auto-restoration for all devices
MIUI_BT_TARGET="/system/app/MiuiBluetooth/MiuiBluetooth.apk"
MIUI_BT_PATCHED="$MODDIR/work/MiuiBluetooth.apk"
if [ -f "$MIUI_BT_PATCHED" ] && [ -f "$MIUI_BT_TARGET" ]; then
    mount --bind "$MIUI_BT_PATCHED" "$MIUI_BT_TARGET" 2>/dev/null || true
fi

# Directory bind-mount for APEX lib64 (includes JNI, shim, and all V5 libs)
APEX_LIB64="$MODDIR/apex_lib64"
if [ -d "$APEX_LIB64" ]; then
    mount -o bind "$APEX_LIB64" /apex/com.android.btservices/lib64 2>/dev/null || true
    for TARGET in /apex/com.android.btservices@*/lib64; do
        if [ -d "$TARGET" ]; then
            mount -o bind "$APEX_LIB64" "$TARGET" 2>/dev/null || true
        fi
    done
fi

# Individual file mounts as fallback
JNI_PATCHED="$MODDIR/work/libbluetooth_jni.so"
if [ -f "$JNI_PATCHED" ]; then
    for TARGET in /apex/com.android.btservices/lib64/libbluetooth_jni.so /apex/com.android.btservices@*/lib64/libbluetooth_jni.so; do
        if [ -f "$TARGET" ]; then
            mount --bind "$JNI_PATCHED" "$TARGET" 2>/dev/null || true
        fi
    done
fi

SHIM_PATCHED="$MODDIR/system/lib64/liblhdcBT_enc.so"
if [ -f "$SHIM_PATCHED" ]; then
    mount --bind "$SHIM_PATCHED" /system/lib64/liblhdcBT_enc.so 2>/dev/null || true
    for TARGET in /apex/com.android.btservices/lib64/liblhdcBT_enc.so /apex/com.android.btservices@*/lib64/liblhdcBT_enc.so; do
        if [ -f "$TARGET" ]; then
            mount --bind "$SHIM_PATCHED" "$TARGET" 2>/dev/null || true
        fi
    done
fi
