import zipfile, re

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

for target in [b'BluetoothAudioTracker', b'BluetoothTelemetry']:
    p = 0
    while True:
        idx = d.find(target, p)
        if idx == -1: break
        print(f"=== {target.decode()} at 0x{idx:x} ===")
        chunk = d[max(0, idx-100):min(len(d), idx+1500)]
        strings = re.findall(rb'[\x20-\x7e]{3,}', chunk)
        for s in strings:
            st = s.decode('utf-8', 'ignore')
            if any(k in st.lower() for k in ['lhdc', 'codec', 'bluetooth', 'track', 'state', 'sample', 'bitrate', 'a2dp']):
                print('  ', st)
        p = idx + len(target)
