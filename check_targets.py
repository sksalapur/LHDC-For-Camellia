import subprocess

cmd = '''
BT_PID=$(pidof com.android.bluetooth)
echo "BT_PID: $BT_PID"
awk '{print $5}' /proc/$BT_PID/mountinfo | grep -E "libbluetooth_jni|liblhdcBT_enc" | sort -u
'''

out = subprocess.check_output(['adb', 'shell', 'su', '-c', cmd]).decode('utf-8', errors='ignore')
print(out)
