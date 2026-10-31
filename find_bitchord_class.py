import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    for dex in [n for n in z.namelist() if n.endswith('.dex')]:
        data = z.read(dex)
        # find field or method name 'bluetoothCodec'
        p = 0
        while True:
            idx = data.find(b'bluetoothCodec', p)
            if idx == -1: break
            # Look around for class descriptor like Lcom/...;
            chunk = data[max(0, idx-400):min(len(data), idx+400)]
            import re
            classes = re.findall(rb'L[a-zA-Z0-9_\$/]+;', chunk)
            print(f"In {dex} near offset 0x{idx:x}:")
            for c in set(classes):
                print(f"  {c.decode('utf-8', 'ignore')}")
            p = idx + 14
