import subprocess

cmd = '''
dumpsys bluetooth_manager | grep -A 20 "A2DP State:"
dumpsys bluetooth_manager | grep -A 10 "Connection Events:"
'''

out = subprocess.check_output(['adb', 'shell', 'su', '-c', cmd]).decode('utf-8', errors='ignore')
print(out)
