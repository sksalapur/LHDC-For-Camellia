import subprocess

cmd = '''
BT_PID=$(pidof com.android.bluetooth)
echo "BT_PID: $BT_PID"
logcat -d --pid=$BT_PID | grep -E "a2dp_vendor_lhdc|LHDC|lhdcv5|encoder" || true
'''

out = subprocess.check_output(['adb', 'shell', 'su', '-c', cmd]).decode('utf-8', errors='ignore')
print(out)
