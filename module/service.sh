#!/system/bin/sh
MODDIR=${0%/*}

# Set permissive temporarily during boot service to ensure property injection
setenforce 0 2>/dev/null

# Wait for boot to finish
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done

# APatch / Magisk resetprop path
RESETPROP="/data/adb/ap/bin/resetprop"
[ -f "$RESETPROP" ] || RESETPROP="/data/adb/magisk/resetprop"
[ -f "$RESETPROP" ] || RESETPROP="resetprop"

# Set MIUI LHDC properties (both with -n and standard)
$RESETPROP -n vendor.bluetooth.lhdc_codec.supported true
$RESETPROP vendor.bluetooth.lhdc_codec.supported true 2>/dev/null

$RESETPROP -n persist.bluetooth.lhdc_codec.enabled true
$RESETPROP persist.bluetooth.lhdc_codec.enabled true 2>/dev/null

$RESETPROP -n persist.bluetooth.a2dp.lhdc.whitelist false
$RESETPROP persist.bluetooth.a2dp.lhdc.whitelist false 2>/dev/null

$RESETPROP -n persist.vendor.bt.a2dp.lhdc true
$RESETPROP persist.vendor.bt.a2dp.lhdc true 2>/dev/null

$RESETPROP -n ro.vendor.bt.a2dp.lhdc true
$RESETPROP ro.vendor.bt.a2dp.lhdc true 2>/dev/null

$RESETPROP -n persist.vendor.bluetooth.lhdc_abr true
$RESETPROP persist.vendor.bluetooth.lhdc_abr true 2>/dev/null

$RESETPROP -n vendor.bluetooth.lhdc.abr true
$RESETPROP vendor.bluetooth.lhdc.abr true 2>/dev/null


$RESETPROP -n bluetooth.a2dp.source.lhdcv2_priority.config 8001
$RESETPROP bluetooth.a2dp.source.lhdcv2_priority.config 8001 2>/dev/null

$RESETPROP -n bluetooth.a2dp.source.lhdcv3_priority.config 8002
$RESETPROP bluetooth.a2dp.source.lhdcv3_priority.config 8002 2>/dev/null

$RESETPROP -n bluetooth.a2dp.source.lhdcv5_priority.config 8003
$RESETPROP bluetooth.a2dp.source.lhdcv5_priority.config 8003 2>/dev/null

$RESETPROP -n persist.bluetooth.a2dp_offload.disabled false
$RESETPROP persist.bluetooth.a2dp_offload.disabled false 2>/dev/null

$RESETPROP -n persist.bluetooth.disableabsvol false
$RESETPROP persist.bluetooth.disableabsvol false 2>/dev/null

$RESETPROP -n persist.bluetooth.lhdc_bitrate 500
$RESETPROP persist.bluetooth.lhdc_bitrate 500 2>/dev/null

$RESETPROP -n persist.bluetooth.lhdc_mtu 600
$RESETPROP persist.bluetooth.lhdc_mtu 600 2>/dev/null

$RESETPROP -n persist.bluetooth.lhdc_max_queue 24
$RESETPROP persist.bluetooth.lhdc_max_queue 24 2>/dev/null

# Ensure overlay is active
OVERLAY_TARGET="/product/overlay/AospBluetoothResOverlay.apk"
OVERLAY_PATCHED="$MODDIR/work/AospBluetoothResOverlay.apk"
if [ -f "$OVERLAY_PATCHED" ] && [ -f "$OVERLAY_TARGET" ]; then
    mount --bind "$OVERLAY_PATCHED" "$OVERLAY_TARGET" 2>/dev/null
fi

NEED_RESTART=0

# Ensure APEX lib64 directory mount is active
APEX_LIB64="$MODDIR/apex_lib64"
if [ -d "$APEX_LIB64" ]; then
    for TARGET in /apex/com.android.btservices/lib64 /apex/com.android.btservices@*/lib64; do
        if [ -d "$TARGET" ]; then
            if ! grep -q "$TARGET" /proc/mounts; then
                mount -o bind "$APEX_LIB64" "$TARGET" 2>/dev/null
                NEED_RESTART=1
            fi
        fi
    done
fi

# Ensure patched libbluetooth_jni.so is active
JNI_PATCHED="$MODDIR/work/libbluetooth_jni.so"
if [ -f "$JNI_PATCHED" ]; then
    for TARGET in /apex/com.android.btservices/lib64/libbluetooth_jni.so /apex/com.android.btservices@*/lib64/libbluetooth_jni.so; do
        if [ -f "$TARGET" ]; then
            if ! grep -q "$TARGET" /proc/mounts; then
                mount --bind "$JNI_PATCHED" "$TARGET" 2>/dev/null
                NEED_RESTART=1
            fi
        fi
    done
fi

# Ensure patched liblhdcBT_enc.so shim is active
SHIM_PATCHED="$MODDIR/system/lib64/liblhdcBT_enc.so"
if [ -f "$SHIM_PATCHED" ]; then
    for TARGET in /system/lib64/liblhdcBT_enc.so /apex/com.android.btservices/lib64/liblhdcBT_enc.so /apex/com.android.btservices@*/lib64/liblhdcBT_enc.so; do
        if [ -f "$TARGET" ]; then
            if ! grep -q "$TARGET" /proc/mounts; then
                mount --bind "$SHIM_PATCHED" "$TARGET" 2>/dev/null
                NEED_RESTART=1
            fi
        fi
    done
fi

# Ensure patched MiuiBluetooth.apk is active to auto-promote case reconnects to LHDC
MIUI_BT_TARGET="/system/app/MiuiBluetooth/MiuiBluetooth.apk"
MIUI_BT_PATCHED="$MODDIR/work/MiuiBluetooth.apk"
if [ -f "$MIUI_BT_PATCHED" ] && [ -f "$MIUI_BT_TARGET" ]; then
    if ! grep -q "$MIUI_BT_TARGET f2fs" /proc/mounts && ! grep -q "$MIUI_BT_TARGET ext4" /proc/mounts; then
        mount --bind "$MIUI_BT_PATCHED" "$MIUI_BT_TARGET" 2>/dev/null
        NEED_RESTART=1
    fi
fi

if [ "$NEED_RESTART" -eq 1 ]; then
    rm -f /data/dalvik-cache/arm64/*MiuiBluetooth* 2>/dev/null || true
    am force-stop com.xiaomi.bluetooth 2>/dev/null || killall -9 com.xiaomi.bluetooth 2>/dev/null
    am force-stop com.android.bluetooth 2>/dev/null || killall -9 com.android.bluetooth 2>/dev/null
fi

exit 0
