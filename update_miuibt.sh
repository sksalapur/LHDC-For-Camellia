#!/system/bin/sh
set -e

echo "=== Updating MiuiBluetooth.apk ==="
setenforce 0 2>/dev/null || true

MODDIR=/data/adb/modules/lhdc_codec_support
cp -f /data/local/tmp/MiuiBluetooth_patched.apk "$MODDIR/work/MiuiBluetooth.apk"
chmod 644 "$MODDIR/work/MiuiBluetooth.apk"
chcon u:object_r:apk_data_file:s0 "$MODDIR/work/MiuiBluetooth.apk" 2>/dev/null || true

# Rebind mount
TARGET="/system/app/MiuiBluetooth/MiuiBluetooth.apk"
umount "$TARGET" 2>/dev/null || true
mount --bind "$MODDIR/work/MiuiBluetooth.apk" "$TARGET" 2>/dev/null || true

# Clear dalvik-cache for MiuiBluetooth so ART compiles fresh DEX with timing fix
rm -f /data/dalvik-cache/arm64/*MiuiBluetooth* 2>/dev/null || true

# Restart Bluetooth daemons cleanly
am force-stop com.xiaomi.bluetooth 2>/dev/null || true
am force-stop com.android.bluetooth 2>/dev/null || true
sleep 1

# Start com.xiaomi.bluetooth service
am start-service com.xiaomi.bluetooth/com.android.bluetooth.ble.app.headset.BluetoothHeadsetService 2>/dev/null || true

sleep 1
NEW_PID=$(pidof com.xiaomi.bluetooth || echo "")
echo "MiuiBluetooth restarted with PID: $NEW_PID"
echo "=== Done ==="
