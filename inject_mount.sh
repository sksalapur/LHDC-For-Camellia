SRC=/data/adb/modules/lhdc_codec_support/work/libbluetooth_jni.so
for NS_PID in 1 770; do
    nsenter -t $NS_PID -m -- mount -o bind $SRC /apex/com.android.btservices/lib64/libbluetooth_jni.so
    nsenter -t $NS_PID -m -- mount -o bind $SRC /apex/com.android.btservices@339990000/lib64/libbluetooth_jni.so
done
pkill -9 -f com.android.bluetooth
sleep 2
NEW_PID=$(pidof com.android.bluetooth)
echo "New BT PID: $NEW_PID"
nsenter -t $NEW_PID -m -- mount | grep libbluetooth_jni

