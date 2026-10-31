#!/system/bin/sh
set -e

echo "Setting up apex_lib64 directory..."
mkdir -p /data/adb/modules/lhdc_codec_support/apex_lib64
cp -a /apex/com.android.btservices/lib64/* /data/adb/modules/lhdc_codec_support/apex_lib64/
cp -f /system/lib64/liblhdcv5BT_enc.so /data/adb/modules/lhdc_codec_support/apex_lib64/
cp -f /system/lib64/liblhdcv5.so /data/adb/modules/lhdc_codec_support/apex_lib64/
cp -f /data/local/tmp/liblhdcBT_enc_shim.so /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcBT_enc.so
cp -f /data/local/tmp/miui_libbluetooth_jni_patched.so /data/adb/modules/lhdc_codec_support/apex_lib64/libbluetooth_jni.so

chmod 755 /data/adb/modules/lhdc_codec_support/apex_lib64
chmod 644 /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcBT_enc.so
chmod 644 /data/adb/modules/lhdc_codec_support/apex_lib64/libbluetooth_jni.so
chmod 644 /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcv5BT_enc.so
chmod 644 /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcv5.so

chcon -R u:object_r:system_lib_file:s0 /data/adb/modules/lhdc_codec_support/apex_lib64 2>/dev/null || true

echo "apex_lib64 contents:"
ls -la /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdc* /data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcv5*
