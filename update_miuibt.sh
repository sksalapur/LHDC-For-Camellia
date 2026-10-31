#!/system/bin/sh
set -e

echo "=== Updating MiuiBluetooth.apk ==="
MODDIR=/data/adb/modules/lhdc_codec_support
cp -f /data/local/tmp/MiuiBluetooth_patched.apk "$MODDIR/work/MiuiBluetooth.apk"
chmod 644 "$MODDIR/work/MiuiBluetooth.apk"
chcon u:object_r:apk_data_file:s0 "$MODDIR/work/MiuiBluetooth.apk" 2>/dev/null || true

# Rebind mount if needed
TARGET="/system/app/MiuiBluetooth/MiuiBluetooth.apk"
mount --bind "$MODDIR/work/MiuiBluetooth.apk" "$TARGET" 2>/dev/null || true

# Kill com.xiaomi.bluetooth to reload
pkill -9 -f com.xiaomi.bluetooth || true
sleep 1

NEW_PID=$(pidof com.xiaomi.bluetooth || echo "")
echo "MiuiBluetooth restarted with PID: $NEW_PID"
echo "=== Done ==="
