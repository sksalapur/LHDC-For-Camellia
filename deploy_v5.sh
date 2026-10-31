#!/system/bin/sh
set -e

echo "=== Deploying LHDC V5 Fixes with Directory Bind-Mount ==="

# 1. Disable BT first
svc bluetooth disable || true
sleep 1
pkill -9 -f com.android.bluetooth || true

MODDIR=/data/adb/modules/lhdc_codec_support
APEX_LIB64="$MODDIR/apex_lib64"

# 2. Update files in apex_lib64
mkdir -p "$APEX_LIB64"
cp -a /apex/com.android.btservices/lib64/* "$APEX_LIB64/" 2>/dev/null || true
cp -f /data/local/tmp/liblhdcBT_enc_shim.so "$APEX_LIB64/liblhdcBT_enc.so"
cp -f /data/local/tmp/miui_libbluetooth_jni_patched.so "$APEX_LIB64/libbluetooth_jni.so"
cp -f /system/lib64/liblhdcv5BT_enc.so "$APEX_LIB64/liblhdcv5BT_enc.so"
cp -f /system/lib64/liblhdcv5.so "$APEX_LIB64/liblhdcv5.so"

chmod 755 "$APEX_LIB64"
chmod 644 "$APEX_LIB64/liblhdcBT_enc.so" "$APEX_LIB64/libbluetooth_jni.so" "$APEX_LIB64/liblhdcv5BT_enc.so" "$APEX_LIB64/liblhdcv5.so"
chcon -R u:object_r:system_lib_file:s0 "$APEX_LIB64" 2>/dev/null || true

# Also update module system directory
cp -f /data/local/tmp/liblhdcBT_enc_shim.so "$MODDIR/system/lib64/liblhdcBT_enc.so"
cp -f /data/local/tmp/miui_libbluetooth_jni_patched.so "$MODDIR/work/libbluetooth_jni.so"

# 3. Mount in init (pid 1) and zygote namespaces
ZYGOTE_PIDS=$(pidof zygote64 || pidof zygote || echo "")
TARGET_PIDS="1 $ZYGOTE_PIDS"

for PID in $TARGET_PIDS; do
    echo "Mounting in namespace of PID $PID..."
    nsenter -t $PID -m -- mount -o bind "$APEX_LIB64" /apex/com.android.btservices/lib64 || true
    for APEX_DIR in /apex/com.android.btservices@*/lib64; do
        if [ -d "$APEX_DIR" ]; then
            nsenter -t $PID -m -- mount -o bind "$APEX_LIB64" "$APEX_DIR" || true
        fi
    done
done

# 4. Enable BT
svc bluetooth enable
sleep 3

NEW_PID=$(pidof com.android.bluetooth || echo "")
echo "New Bluetooth PID: $NEW_PID"

if [ -n "$NEW_PID" ]; then
    echo "Verifying mounts in BT process namespace:"
    awk '{print $5}' /proc/$NEW_PID/mountinfo | grep -E "btservices/lib64" | sort -u || true
fi

echo "=== Deployment Complete ==="
