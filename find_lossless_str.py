import zipfile

with zipfile.ZipFile('timbre.apk', 'r') as z:
    for name in z.namelist():
        if name.endswith('.dex'):
            data = z.read(name)
            p = data.find(b'lossless output')
            if p != -1:
                print(f"Found 'lossless output' in {name} at 0x{p:x}")
                chunk = data[max(0, p-100):min(len(data), p+200)]
                print(chunk)
