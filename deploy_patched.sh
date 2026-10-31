#!/system/bin/sh
svc bluetooth disable
sleep 1
killall -9 com.android.bluetooth 2>/dev/null

for i in 1 2 3 4 5 6 7 8 9 10; do
    M=$(mount | grep libbluetooth_jni | awk '{print $3}' | head -n 1)
    [ -z "$M" ] && break
    umount -l "$M" 2>/dev/null
done

cp -f /data/local/tmp/libbluetooth_jni_patched.so /data/adb/modules/lhdc_codec_support/work/libbluetooth_jni.so
chmod 644 /data/adb/modules/lhdc_codec_support/work/libbluetooth_jni.so
chown root:root /data/adb/modules/lhdc_codec_support/work/libbluetooth_jni.so

for TARGET in /apex/com.android.btservices/lib64/libbluetooth_jni.so /apex/com.android.btservices@*/lib64/libbluetooth_jni.so; do
    if [ -f "$TARGET" ]; then
        mount --bind /data/adb/modules/lhdc_codec_support/work/libbluetooth_jni.so "$TARGET"
    fi
done

echo "Current mounts:"
mount | grep libbluetooth_jni

svc bluetooth enable
echo "Bluetooth re-enabled."
