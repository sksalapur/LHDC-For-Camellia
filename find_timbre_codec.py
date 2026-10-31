import zipfile, re

with zipfile.ZipFile('timbre.apk', 'r') as z:
    for name in ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex']:
        if name in z.namelist():
            data = z.read(name)
            for m in re.finditer(rb'LHDCv5', data):
                p = m.start()
                chunk = data[max(0, p-200):min(len(data), p+200)]
                strings = re.findall(rb'[\x20-\x7e]{3,}', chunk)
                print(f"=== {name} at {p} ===")
                for s in strings:
                    print('  ', s.decode())
